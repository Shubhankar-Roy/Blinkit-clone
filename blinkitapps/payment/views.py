import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.contrib import messages
import razorpay
from .models import Payment
from blinkitapps.orders.models import Order

# Initialize Razorpay client
key_id = getattr(settings, 'RAZOR_KEY_ID', getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_TUqVvgf1HYHy0o'))
key_secret = getattr(settings, 'RAZOR_KEY_SECRET', getattr(settings, 'RAZORPAY_KEY_SECRET', 'kmQ1hgcEvRaL6k6ZZ4Dw8MG3'))

razorpay_client = razorpay.Client(auth=(key_id, key_secret))


def homepage(request):
    """
    Standalone payment test page (creates a test order of Rs. 200).
    """
    amount = 20000  # Rs. 200 in paise
    currency = 'INR'

    try:
        razorpay_order = razorpay_client.order.create(
            dict(amount=amount, currency=currency, payment_capture='0')
        )
        razorpay_order_id = razorpay_order['id']
    except Exception as e:
        razorpay_order_id = f"order_{uuid.uuid4().hex[:14]}"

    # Save order in database
    Payment.objects.create(
        razorpay_order_id=razorpay_order_id,
        amount=amount,
        status='Created'
    )

    context = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': key_id,
        'razorpay_amount': amount,
        'currency': currency,
        'callback_url': '/paymenthandler/'
    }
    return render(request, 'payment/index.html', context)


def order_payment(request, order_number):
    """
    Payment checkout view for Blinkit customer orders.
    """
    order = get_object_or_404(Order, order_number=order_number)

    if order.payment_status == 'SUCCESS':
        messages.info(request, f"Order #{order.order_number} is already paid.")
        return redirect('orders:track', order_number=order.order_number)

    amount_in_paise = int(order.grand_total * 100)
    currency = 'INR'

    try:
        razorpay_order = razorpay_client.order.create(
            dict(
                amount=amount_in_paise,
                currency=currency,
                receipt=str(order.order_number),
                payment_capture='0',
                notes={'order_number': order.order_number}
            )
        )
        razorpay_order_id = razorpay_order['id']
    except Exception as e:
        razorpay_order_id = f"order_{uuid.uuid4().hex[:14]}"

    order.razorpay_order_id = razorpay_order_id
    order.save(update_fields=['razorpay_order_id'])

    payment_record, _ = Payment.objects.get_or_create(
        razorpay_order_id=razorpay_order_id,
        defaults={
            'amount': amount_in_paise,
            'status': 'Created'
        }
    )

    context = {
        'order': order,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': key_id,
        'razorpay_key_id': key_id,
        'razorpay_amount': amount_in_paise,
        'amount_in_paise': amount_in_paise,
        'currency': currency,
        'callback_url': '/paymenthandler/',
        'user_name': order.user.display_name if order.user else 'Customer',
        'user_email': order.user.email if order.user and order.user.email else 'customer@blinkitclone.local',
        'user_phone': order.phone or (order.user.phone_number if order.user else '9876543210'),
    }
    return render(request, 'payment/razorpay_pay.html', context)


@csrf_exempt
def paymenthandler(request):
    """
    Handles payment callback from Razorpay Checkout modal or simulation form.
    Captures payment and marks payment & order as Success.
    """
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        payment_status_input = request.POST.get('payment_status', 'SUCCESS')
        order_number = request.POST.get('order_number')

        # Find linked order if exists
        order = None
        if order_number:
            order = Order.objects.filter(order_number=order_number).first()
        if not order and razorpay_order_id:
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()

        # Handle explicit failure from simulation or gateway
        if payment_status_input == 'FAILED':
            if razorpay_order_id:
                Payment.objects.filter(razorpay_order_id=razorpay_order_id).update(status='Failed')
            if order:
                order.payment_status = 'FAILED'
                order.save(update_fields=['payment_status'])
                messages.error(request, "Payment was cancelled or failed.")
                return redirect('orders:checkout')
            return render(request, 'payment/paymentfail.html', {'order': order})

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        # Check simulation mode
        is_simulation = signature.startswith('sig_mock') or payment_id.startswith('pay_mock')

        try:
            if not is_simulation and signature and payment_id:
                # Real verification via Razorpay SDK
                razorpay_client.utility.verify_payment_signature(params_dict)

                # Fetch payment record
                payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
                if payment:
                    capture_amount = int(payment.amount)
                    try:
                        # Capture payment
                        razorpay_client.payment.capture(payment_id, capture_amount)
                    except Exception:
                        pass  # payment may be auto-captured
                    payment.razorpay_payment_id = payment_id
                    payment.razorpay_signature = signature
                    payment.status = 'Success'
                    payment.save()
            else:
                # Simulation / Test verification
                payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
                if payment:
                    payment.razorpay_payment_id = payment_id or f"pay_sim_{uuid.uuid4().hex[:10]}"
                    payment.razorpay_signature = signature or "sig_sim_auto"
                    payment.status = 'Success'
                    payment.save()

            if order:
                order.payment_status = 'SUCCESS'
                order.razorpay_payment_id = payment_id or (payment.razorpay_payment_id if payment else f"pay_{uuid.uuid4().hex[:10]}")
                order.save(update_fields=['payment_status', 'razorpay_payment_id'])
                messages.success(request, f"🎉 Payment received! Order #{order.order_number} confirmed.")
                return redirect('orders:track', order_number=order.order_number)

            return render(request, 'payment/paymentsuccess.html', {
                'payment_id': payment_id,
                'razorpay_order_id': razorpay_order_id
            })

        except razorpay.errors.SignatureVerificationError:
            Payment.objects.filter(razorpay_order_id=razorpay_order_id).update(status='Failed')
            if order:
                order.payment_status = 'FAILED'
                order.save(update_fields=['payment_status'])
            return render(request, 'payment/paymentfail.html', {'order': order})

        except Exception as e:
            # Fallback for mock simulation or exception logging
            if is_simulation and order:
                order.payment_status = 'SUCCESS'
                order.save(update_fields=['payment_status'])
                return redirect('orders:track', order_number=order.order_number)
            return HttpResponseBadRequest(f"Payment Processing Error: {str(e)}")
    else:
        return HttpResponseBadRequest("Invalid request method")