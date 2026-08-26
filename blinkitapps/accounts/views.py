from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import User, Address 
from blinkitapps.cart.models import Cart, CartItem


def merge_session_cart(request, user):
    session_id = request.session.session_key
    if not session_id:
        return

    session_cart = Cart.objects.filter(session_id=session_id).first()
    if session_cart and session_cart.items.exists():
        user_cart, _ = Cart.objects.get_or_create(user=user)
        
        for item in session_cart.items.all():
            u_item, created = CartItem.objects.get_or_create(cart=user_cart, product=item.product)
            u_item.quantity = item.quantity if created else u_item.quantity + item.quantity
            u_item.save()
            
        session_cart.delete()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')

    next_url = request.GET.get('next') or request.POST.get('next') or 'products:home'
    context = {'next': next_url}

    if request.method == 'POST':
        identifier = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user_obj = User.objects.filter(username=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(email=identifier).first()
        if not user_obj:
            user_obj = User.objects.filter(phone_number=identifier).first()

        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None

        if user:
            merge_session_cart(request, user)
            login(request, user)
            return redirect(next_url)
        else:
            context['error'] = "Invalid username or password."

    return render(request, 'accounts/login.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')

    next_url = request.GET.get('next') or request.POST.get('next') or 'products:home'
    context = {'next': next_url}

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        username = request.POST.get('username')
        if not username:
            username = email.split('@')[0] if email else f"user_{phone_number}"

        if password != confirm_password:
            context['error'] = "Passwords do not match."
        elif len(password) < 6:
            context['error'] = "Password must be at least 6 characters."
        elif User.objects.filter(username=username).exists():
            context['error'] = "Username already exists."
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                full_name=full_name, phone_number=phone_number
            )
            merge_session_cart(request, user)
            login(request, user)
            return redirect(next_url)

    return render(request, 'accounts/register.html', context)


def logout_view(request):
    logout(request)
    return redirect('products:home')


@login_required
def profile_view(request):
    addresses = Address.objects.filter(user=request.user)
    context = {'addresses': addresses}

    if request.method == 'POST':
        request.user.full_name = request.POST.get('full_name', request.user.full_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.phone_number = request.POST.get('phone_number', request.user.phone_number)
        request.user.save()
        
        context['success'] = "Profile updated successfully!"

    return render(request, 'accounts/profile.html', context)


@login_required
def add_address(request):
    if request.method == 'POST':
        house_flat = request.POST.get('house_flat_no')
        area = request.POST.get('area_street')
        pincode = request.POST.get('pincode')

        if house_flat and area and pincode:
            has_existing_addresses = Address.objects.filter(user=request.user).exists()
            Address.objects.create(
                user=request.user,
                house_flat_no=house_flat,
                area_street=area,
                landmark=request.POST.get('landmark', ''),
                pincode=pincode,
                city=request.POST.get('city', 'Purnia'),
                address_type=request.POST.get('address_type', 'Home'),
                is_default=not request.user.addresses.exists() 
            )
            
    return redirect('accounts:profile')


@login_required
def delete_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        address.delete()
        return redirect('accounts:profile')
    except Address.DoesNotExist:
        return HttpResponse("Address not found.", status=404)