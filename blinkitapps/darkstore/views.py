import json
import math
import urllib.parse
import urllib.request
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import DarkStore

POPULAR_LOCATIONS = [
    {'name': 'Koramangala, Bengaluru', 'pincode': '560034', 'city': 'Bengaluru', 'tag': 'Popular', 'lat': 12.9352, 'lng': 77.6245},
    {'name': 'Indiranagar, Bengaluru', 'pincode': '560038', 'city': 'Bengaluru', 'tag': 'Superfast', 'lat': 12.9719, 'lng': 77.6412},
    {'name': 'HSR Layout, Bengaluru', 'pincode': '560102', 'city': 'Bengaluru', 'tag': 'Popular', 'lat': 12.9121, 'lng': 77.6446},
    {'name': 'Whitefield, Bengaluru', 'pincode': '560066', 'city': 'Bengaluru', 'tag': 'Tech Park', 'lat': 12.9698, 'lng': 77.7500},
    {'name': 'Jayanagar, Bengaluru', 'pincode': '560011', 'city': 'Bengaluru', 'tag': 'Central', 'lat': 12.9250, 'lng': 77.5938},
    {'name': 'BTM Layout, Bengaluru', 'pincode': '560076', 'city': 'Bengaluru', 'tag': 'Express', 'lat': 12.9166, 'lng': 77.6101},
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle distance between two points on the earth in kilometers.
    """
    try:
        r = 6371.0  # Earth radius in kilometers
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)
    except Exception:
        return 999.0


def find_nearest_darkstore(lat, lng):
    """
    Finds the nearest active darkstore to the given GPS coordinates
    and computes estimated delivery turnaround in minutes.
    """
    active_stores = list(DarkStore.objects.filter(is_active=True))
    if not active_stores:
        return None, 999.0, 15

    closest_store = None
    min_dist = float('inf')

    for store in active_stores:
        dist = haversine_distance(lat, lng, store.latitude, store.longitude)
        if dist < min_dist:
            min_dist = dist
            closest_store = store

    # Dynamic ETA calculation based on distance in km
    if min_dist <= 2.0:
        eta = 8
    elif min_dist <= 4.0:
        eta = 10
    elif min_dist <= 7.0:
        eta = 13
    elif min_dist <= 10.0:
        eta = 16
    else:
        eta = 20

    return closest_store, min_dist, eta


def set_location_view(request):
    """
    Saves selected pincode and location name into session,
    calculates assigned dark store & ETA.
    """
    if request.method in ['POST', 'GET']:
        pincode = (request.POST.get('pincode') or request.GET.get('pincode') or '').strip()
        location_name = (request.POST.get('location_name') or request.GET.get('location_name') or '').strip()
        lat_raw = request.POST.get('lat') or request.GET.get('lat')
        lng_raw = request.POST.get('lng') or request.GET.get('lng')
        eta_raw = request.POST.get('eta_mins') or request.GET.get('eta_mins')

        active_stores = DarkStore.objects.filter(is_active=True)
        matched_store = None
        lat = None
        lng = None
        eta = 10

        try:
            if lat_raw and lng_raw:
                lat = float(lat_raw)
                lng = float(lng_raw)
        except (ValueError, TypeError):
            pass

        # 1. Match by pincode if provided
        if pincode:
            for store in active_stores:
                if store.is_pincode_serviceable(pincode):
                    matched_store = store
                    eta = store.avg_delivery_mins
                    break

        # 2. If no direct pincode match but coordinates provided, find nearest store
        if not matched_store and lat is not None and lng is not None:
            nearest_store, dist, dynamic_eta = find_nearest_darkstore(lat, lng)
            if nearest_store and dist <= 8.0:
                matched_store = nearest_store
                eta = dynamic_eta

        # If user passed custom ETA
        if eta_raw:
            try:
                eta = int(eta_raw)
            except ValueError:
                pass

        if not location_name:
            if matched_store:
                location_name = f"{matched_store.name}, {matched_store.city}"
            elif pincode:
                location_name = f"Pincode {pincode}"
            else:
                location_name = "Bengaluru"

        if not pincode and matched_store and matched_store.pincode_list:
            pincode = matched_store.pincode_list[0]
        elif not pincode:
            pincode = "560034"

        # Save into session for universal template availability
        request.session['pincode'] = pincode
        request.session['location_name'] = location_name
        request.session['eta_mins'] = eta
        request.session['darkstore_id'] = matched_store.id if matched_store else None
        request.session['darkstore_name'] = matched_store.name if matched_store else None
        request.session['is_serviceable'] = matched_store is not None
        if lat and lng:
            request.session['user_lat'] = lat
            request.session['user_lng'] = lng

        if matched_store:
            messages.success(
                request,
                f"Location updated to {location_name}. Instant delivery in {eta} mins from {matched_store.name}!"
            )
        else:
            messages.info(
                request,
                f"Location updated to {location_name} (Pincode: {pincode}). Standard delivery available."
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({
                'status': 'success',
                'pincode': pincode,
                'location_name': location_name,
                'serviceable': matched_store is not None,
                'store_name': matched_store.name if matched_store else None,
                'eta_mins': eta,
            })

    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def detect_location_api(request):
    """
    Real-time Reverse Geocoding and Accurate GPS Location Detection API.
    Takes `lat` and `lng` (from navigator.geolocation), resolves exact locality & pincode,
    and matches the closest dark store with real ETA.
    """
    lat_val = request.GET.get('lat') or request.POST.get('lat')
    lng_val = request.GET.get('lng') or request.POST.get('lng')

    if not lat_val or not lng_val:
        return JsonResponse({'status': 'error', 'message': 'Latitude and Longitude are required'}, status=400)

    try:
        lat = float(lat_val)
        lng = float(lng_val)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid coordinates provided'}, status=400)

    # 1. Reverse Geocode via OpenStreetMap Nominatim
    resolved_pincode = None
    locality_name = None
    full_address = None
    city = 'Bengaluru'

    try:
        nominatim_url = (
            f"https://nominatim.openstreetmap.org/reverse?"
            f"format=jsonv2&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
        )
        req = urllib.request.Request(
            nominatim_url,
            headers={'User-Agent': 'BlinkitCloneLocationEngine/2.0 (contact: support@blinkitclone.local)'}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            addr = data.get('address', {})

            resolved_pincode = addr.get('postcode')
            # Extract postal code if formatted with spaces e.g. "560 034"
            if resolved_pincode:
                resolved_pincode = ''.join(c for c in resolved_pincode if c.isdigit())
                if len(resolved_pincode) != 6:
                    resolved_pincode = None

            suburb = addr.get('suburb') or addr.get('neighbourhood') or addr.get('residential') or addr.get('road')
            city = addr.get('city') or addr.get('town') or addr.get('city_district') or addr.get('county') or 'Bengaluru'

            if suburb and city:
                locality_name = f"{suburb}, {city}"
            elif suburb:
                locality_name = suburb
            else:
                locality_name = city

            full_address = data.get('display_name')
    except Exception:
        # Fallback if geocoding service is unreachable
        pass

    # 2. Find nearest Dark Store & calculate exact ETA
    closest_store, distance_km, dynamic_eta = find_nearest_darkstore(lat, lng)

    # If pincode wasn't returned by reverse-geocoding, use closest store's primary pincode
    if not resolved_pincode:
        if closest_store and closest_store.pincode_list:
            resolved_pincode = closest_store.pincode_list[0]
        else:
            resolved_pincode = '560034'

    if not locality_name:
        if closest_store:
            locality_name = f"{closest_store.name.split('#')[0].strip()}, {closest_store.city}"
        else:
            locality_name = f"Location near {resolved_pincode}"

    # Check serviceability (pincode match or within delivery distance)
    is_pincode_covered = closest_store.is_pincode_serviceable(resolved_pincode) if closest_store else False
    is_distance_covered = distance_km <= 8.0
    is_serviceable = is_pincode_covered or is_distance_covered

    if is_serviceable:
        message = f"⚡ Instant {dynamic_eta}-min delivery available from {closest_store.name} ({distance_km:.1f} km away)"
    else:
        message = f"Location is {distance_km:.1f} km from nearest hub. Standard delivery will be assigned."

    return JsonResponse({
        'status': 'success',
        'pincode': resolved_pincode,
        'location_name': locality_name,
        'full_address': full_address or locality_name,
        'latitude': lat,
        'longitude': lng,
        'distance_km': distance_km,
        'eta_mins': dynamic_eta,
        'store_id': closest_store.id if closest_store else None,
        'store_name': closest_store.name if closest_store else None,
        'store_code': closest_store.code if closest_store else None,
        'serviceable': is_serviceable,
        'message': message,
    })


def search_locations_api(request):
    """
    Search localities, landmarks, and pincodes with autocomplete.
    """
    query = (request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'status': 'success', 'results': []})

    results = []

    # 1. Search local preset hubs first for instant response
    for loc in POPULAR_LOCATIONS:
        if query.lower() in loc['name'].lower() or query in loc['pincode']:
            store, dist, eta = find_nearest_darkstore(loc['lat'], loc['lng'])
            results.append({
                'name': loc['name'],
                'pincode': loc['pincode'],
                'city': loc['city'],
                'lat': loc['lat'],
                'lng': loc['lng'],
                'eta_mins': eta,
                'is_preset': True,
                'tag': loc.get('tag', 'Hub'),
            })

    # 2. Search OpenStreetMap Nominatim for Indian places if query is > 2 chars
    if len(query) >= 3:
        try:
            search_url = (
                f"https://nominatim.openstreetmap.org/search?"
                + urllib.parse.urlencode({
                    'q': f"{query}, India",
                    'format': 'jsonv2',
                    'limit': 5,
                    'countrycodes': 'in',
                    'addressdetails': 1
                })
            )
            req = urllib.request.Request(
                search_url,
                headers={'User-Agent': 'BlinkitCloneLocationEngine/2.0 (contact: support@blinkitclone.local)'}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for item in data:
                    addr = item.get('address', {})
                    pincode = addr.get('postcode', '')
                    if pincode:
                        pincode = ''.join(c for c in pincode if c.isdigit())
                        if len(pincode) != 6:
                            pincode = ''

                    suburb = addr.get('suburb') or addr.get('neighbourhood') or addr.get('residential') or addr.get('road')
                    city = addr.get('city') or addr.get('town') or addr.get('city_district') or addr.get('state_district') or 'Bengaluru'
                    
                    display_name = f"{suburb}, {city}" if suburb else (item.get('name') or city)
                    
                    try:
                        lat = float(item.get('lat'))
                        lng = float(item.get('lon'))
                    except (ValueError, TypeError):
                        continue

                    # Avoid duplicate names in results
                    if not any(r['name'].lower() == display_name.lower() for r in results):
                        store, dist, eta = find_nearest_darkstore(lat, lng)
                        results.append({
                            'name': display_name,
                            'full_name': item.get('display_name', display_name),
                            'pincode': pincode or (store.pincode_list[0] if store and store.pincode_list else '560034'),
                            'city': city,
                            'lat': lat,
                            'lng': lng,
                            'eta_mins': eta,
                            'is_preset': False,
                            'tag': 'Address',
                        })
        except Exception:
            pass

    return JsonResponse({
        'status': 'success',
        'results': results[:6]
    })


def check_pincode_api(request):
    """
    AJAX API for real-time pincode serviceability check.
    """
    pincode = request.GET.get('pincode', '').strip()
    if not pincode:
        return JsonResponse({'status': 'error', 'message': 'Pincode is required'}, status=400)

    clean_pincode = ''.join(c for c in pincode if c.isdigit())
    active_stores = DarkStore.objects.filter(is_active=True)
    matched_store = None
    
    for store in active_stores:
        if store.is_pincode_serviceable(clean_pincode):
            matched_store = store
            break

    if matched_store:
        return JsonResponse({
            'status': 'success',
            'serviceable': True,
            'pincode': clean_pincode,
            'store_id': matched_store.id,
            'store_name': matched_store.name,
            'store_code': matched_store.code,
            'city': matched_store.city,
            'eta_mins': matched_store.avg_delivery_mins,
            'message': f"⚡ Instant {matched_store.avg_delivery_mins}-min delivery available from {matched_store.name}!",
        })
    else:
        # Fallback to nearest active store for standard delivery
        first_store = active_stores.first()
        return JsonResponse({
            'status': 'success',
            'serviceable': False,
            'pincode': clean_pincode,
            'store_name': first_store.name if first_store else None,
            'eta_mins': 20,
            'message': "This pincode is currently outside our 10-min micro-hub zone. Standard delivery will apply.",
        })


def get_popular_locations_api(request):
    """
    Returns list of preset popular locations with real-time ETA.
    """
    locations = []
    for loc in POPULAR_LOCATIONS:
        store, dist, eta = find_nearest_darkstore(loc['lat'], loc['lng'])
        locations.append({
            **loc,
            'eta_mins': eta,
            'store_name': store.name if store else 'Bengaluru Hub'
        })

    return JsonResponse({
        'status': 'success',
        'locations': locations
    })
