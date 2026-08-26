from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import DarkStore

POPULAR_LOCATIONS = [
    {'name': 'Koramangala, Bengaluru', 'pincode': '560034', 'city': 'Bengaluru', 'tag': 'Popular'},
    {'name': 'Indiranagar, Bengaluru', 'pincode': '560038', 'city': 'Bengaluru', 'tag': 'Superfast'},
    {'name': 'HSR Layout, Bengaluru', 'pincode': '560102', 'city': 'Bengaluru', 'tag': 'Popular'},
    {'name': 'Whitefield, Bengaluru', 'pincode': '560066', 'city': 'Bengaluru', 'tag': 'Tech Park'},
    {'name': 'Jayanagar, Bengaluru', 'pincode': '560011', 'city': 'Bengaluru', 'tag': 'Central'},
    {'name': 'BTM Layout, Bengaluru', 'pincode': '560076', 'city': 'Bengaluru', 'tag': 'Express'},
]


def set_location_view(request):
    """
    Saves selected pincode and location name into session,
    and calculates assigned dark store & ETA.
    """
    if request.method in ['POST', 'GET']:
        pincode = request.POST.get('pincode') or request.GET.get('pincode')
        location_name = request.POST.get('location_name') or request.GET.get('location_name')

        if pincode:
            clean_pincode = str(pincode).strip()
            
            # Find matching active store
            active_stores = DarkStore.objects.filter(is_active=True)
            matched_store = None
            for store in active_stores:
                if store.is_pincode_serviceable(clean_pincode):
                    matched_store = store
                    break

            if not location_name:
                if matched_store:
                    location_name = f"{matched_store.name}, {matched_store.city}"
                else:
                    location_name = f"Pincode {clean_pincode}"

            request.session['pincode'] = clean_pincode
            request.session['location_name'] = location_name

            if matched_store:
                messages.success(
                    request,
                    f"Location updated to {location_name}. Superfast delivery in {matched_store.avg_delivery_mins} mins from {matched_store.name}!"
                )
            else:
                messages.warning(
                    request,
                    f"Pincode {clean_pincode} is currently outside our 10-minute micro-store zone. Standard delivery will be assigned."
                )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
                return JsonResponse({
                    'status': 'success',
                    'pincode': clean_pincode,
                    'location_name': location_name,
                    'serviceable': matched_store is not None,
                    'store_name': matched_store.name if matched_store else None,
                    'eta_mins': matched_store.avg_delivery_mins if matched_store else 15,
                })

    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def check_pincode_api(request):
    """
    AJAX API for real-time serviceability check.
    """
    pincode = request.GET.get('pincode', '').strip()
    if not pincode:
        return JsonResponse({'status': 'error', 'message': 'Pincode is required'}, status=400)

    active_stores = DarkStore.objects.filter(is_active=True)
    matched_store = None
    
    for store in active_stores:
        if store.is_pincode_serviceable(pincode):
            matched_store = store
            break

    if matched_store:
        return JsonResponse({
            'status': 'success',
            'serviceable': True,
            'pincode': pincode,
            'store_id': matched_store.id,
            'store_name': matched_store.name,
            'store_code': matched_store.code,
            'city': matched_store.city,
            'eta_mins': matched_store.avg_delivery_mins,
            'message': f"Available for instant delivery in {matched_store.avg_delivery_mins} minutes!",
        })
    else:
        return JsonResponse({
            'status': 'success',
            'serviceable': False,
            'pincode': pincode,
            'message': "Sorry, we do not deliver to this pincode yet. We are expanding rapidly!",
        })


def get_popular_locations_api(request):
    """
    Returns list of preset popular locations.
    """
    return JsonResponse({
        'status': 'success',
        'locations': POPULAR_LOCATIONS
    })
