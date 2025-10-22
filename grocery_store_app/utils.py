import requests
import math
import logging
from typing import Tuple
from django.db.models import Q, Exists, OuterRef
from django.apps import apps

API_KEY = "68b3c071edb8e216867405vxhafdb0c"  # Geocode.maps.co free API key


def geocode_postcode(postcode: str) -> Tuple[float, float] | Tuple[None, None]:
    try:
        response = requests.get(
            "https://geocode.maps.co/search",
            params={"postalcode": postcode, "country": "AU", "api_key": API_KEY},
        )
        data = response.json()

        if data and isinstance(data, list):
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        logging.error(f"Geocoding error: {e}")

    return None, None


# Haversine formula to calculate distance between two lat/lon point
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# Product Filtering
def _dec(val, lo=0, hi=1_000_000):
    try:
        if val in (None, ""):
            return None
        v = float(val)
        return v if lo <= v <= hi else None
    except Exception:
        return None


def apply_product_filters(qs, params):
    """
    Apply multi-condition filters to Product queryset.
    Supported params:
      - q: keyword (name/description if you add it later)
      - category: category name (exact match)
      - price_min, price_max: numeric
      - in_stock: "1" to require any store stock > 0
    """
    # lazy model lookup to avoid circular imports during app load
    PerStoreProduct = apps.get_model("grocery_store_app", "PerStoreProduct")
    # Search
    q = (params.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
        )  # extend to description if you add the field

    # Category (your Category has name only; no slug in model)
    cat = (params.get("category") or "").strip()
    if cat:
        qs = qs.filter(category__name=cat)

    # Price range
    pmin = _dec(params.get("price_min"))
    pmax = _dec(params.get("price_max"))
    if pmin is not None:
        qs = qs.filter(price__gte=pmin)
    if pmax is not None:
        qs = qs.filter(price__lte=pmax)

    # In stock (exists any PerStoreProduct with quantity > 0)
    if params.get("in_stock") == "1":
        in_stock_exists = PerStoreProduct.objects.filter(
            product_id=OuterRef("pk"),
            quantity__gt=0,
        )
        qs = qs.annotate(_has_stock=Exists(in_stock_exists)).filter(_has_stock=True)

    return qs
