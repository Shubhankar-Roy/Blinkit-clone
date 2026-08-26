from .models import DarkStore


def location_processor(request):
    """
    Injects current user location, assigned Dark Store, delivery ETA,
    and serviceability status into all Django templates.
    """
    pincode = request.session.get('pincode', '560034')
    location_name = request.session.get('location_name', 'Koramangala, Bengaluru')

    # Find the active Dark Store that covers the user's pincode
    active_stores = DarkStore.objects.filter(is_active=True)
    matching_store = None
    
    for store in active_stores:
        if store.is_pincode_serviceable(pincode):
            matching_store = store
            break

    # Fallback to the first active store if available
    fallback_store = active_stores.first()
    effective_store = matching_store or fallback_store
    is_serviceable = matching_store is not None

    eta_mins = matching_store.avg_delivery_mins if matching_store else (fallback_store.avg_delivery_mins if fallback_store else 10)

    return {
        'current_pincode': pincode,
        'current_location_name': location_name,
        'current_dark_store': effective_store,
        'assigned_dark_store': matching_store,
        'eta_mins': eta_mins,
        'is_location_serviceable': is_serviceable,
        'all_active_darkstores': active_stores,
    }
