import requests
import math
import logging
from typing import Tuple

API_KEY = "68b3c071edb8e216867405vxhafdb0c" # Geocode.maps.co free API key

def geocode_postcode(postcode: str) -> Tuple[float, float] | Tuple[None, None]:
    try:
        response = requests.get("https://geocode.maps.co/search", params={
            "postalcode": postcode,
            "country": "AU",
            "api_key": API_KEY
        })
        data = response.json()

        if data and isinstance(data, list):
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        logging.error(f"Geocoding error: {e}")
    
    return None, None

# Haversine formula to calculate distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c