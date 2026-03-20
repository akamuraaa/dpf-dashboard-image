import requests
import json
import os
from pathlib import Path

# fallback to berlin
_FALLBACK = {"lat": 52.52, "lon": 13.41, "display": "Berlin, DE"}

def _cache_path(cache_dir="/tmp"):
    return os.path.join(cache_dir, "geocode_cache.json")

def _parse_display(nominatim_result: dict, fallback: str) -> str:
    try:
        addr   = nominatim_result.get("address", {})
        city   = (addr.get("city") or addr.get("town") or
                  addr.get("village") or addr.get("county") or fallback)
        cc     = addr.get("country_code", "").upper()
        return f"{city} · {cc}" if cc else city
    except Exception:
        return fallback

def _load_cache(city, cache_dir):
    try:
        with open(_cache_path(cache_dir), encoding="utf-8") as f:
            data = json.load(f)
        if data.get("city", "").lower() == city.lower():
            return data["lat"], data["lon"], data.get("display", city)
    except Exception:
        pass
    return None, None, None

def _save_cache(city, lat, lon, display, cache_dir):
    try:
        with open(_cache_path(cache_dir), "w", encoding="utf-8") as f:
            json.dump({"city": city, "lat": lat, "lon": lon, "display": display}, f)
    except Exception as e:
        print(f"[Geocode] Cache-Error: {e}")
 
 
def resolve(city: str, cache_dir: str = "/tmp") -> tuple[float, float, str]:
    if not city:
        print("[Geocode] no city name given – use Fallback (Berlin)")
        return _FALLBACK["lat"], _FALLBACK["lon"], _FALLBACK["display"]
 
    # Cache check
    lat, lon, display = _load_cache(city, cache_dir)
    if lat is not None:
        print(f"[Geocode] from cache: {city} → {lat}, {lon} ({display})")
        return lat, lon, display
 
    # Nominatim query
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1,
                    "addressdetails": 1},
            headers={"User-Agent": "dpf-dashboard/1.0"},
            timeout=8,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise ValueError(f"No results for '{city}'")
        lat     = float(results[0]["lat"])
        lon     = float(results[0]["lon"])
        display = _parse_display(results[0], city)
        print(f"[Geocode] {city} → {lat:.4f}, {lon:.4f} ({display})")
        _save_cache(city, lat, lon, display, cache_dir)
        return lat, lon, display
    except Exception as e:
        print(f"[Geocode] Error: {e} – use Fallback ({_FALLBACK['display']})")
        return _FALLBACK["lat"], _FALLBACK["lon"], _FALLBACK["display"]