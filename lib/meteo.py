"""Récupération METAR/TAF via aviationweather.gov (API gratuite).

Si l'aérodrome demandé n'a pas de METAR (petit terrain non-publiant),
on cherche le METAR le plus proche dans un rayon de ~50 NM via la
recherche par bbox de l'API.
"""
import math
import requests


def _is_valid_icao(icao: str) -> bool:
    return bool(icao) and len(icao) == 4 and icao.isalpha()


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distance grand cercle en km."""
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _fetch(url: str, label: str, icao: str) -> str:
    """Wrapper avec messages d'erreur explicites."""
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        text = r.text.strip()
        return text if text else f"⚠️ Aucun {label} disponible pour {icao}"
    except requests.Timeout:
        return f"⏱️ Timeout API {label} ({icao}) — réessaie dans quelques secondes."
    except requests.ConnectionError:
        return f"🌐 Pas de connexion internet pour récupérer le {label} de {icao}."
    except requests.HTTPError as e:
        return f"❌ API {label} a renvoyé HTTP {e.response.status_code} pour {icao}."
    except Exception as e:
        return f"⚠️ Erreur récupération {label} {icao} : {e}"


def fetch_metar(icao: str) -> str:
    icao = icao.strip().upper()
    if not _is_valid_icao(icao):
        return "—"
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=raw&taf=false"
    return _fetch(url, "METAR", icao)


def fetch_taf(icao: str) -> str:
    icao = icao.strip().upper()
    if not _is_valid_icao(icao):
        return "—"
    url = f"https://aviationweather.gov/api/data/taf?ids={icao}&format=raw"
    return _fetch(url, "TAF", icao)


def get_station_coords(icao: str) -> tuple[float, float] | None:
    """Récupère lat/lon d'une station.
    1) Cherche dans la DB locale lib/airports.py
    2) Sinon tente l'API aviationweather.gov stationinfo (souvent 204 pour
       les petits aérodromes français)."""
    icao = icao.strip().upper()
    if not _is_valid_icao(icao):
        return None
    # 1) DB locale
    try:
        from .airports import get_airport
        ad = get_airport(icao)
        if ad and ad.get("lat") is not None and ad.get("lon") is not None:
            return float(ad["lat"]), float(ad["lon"])
    except Exception:
        pass
    # 2) API aviationweather
    try:
        url = f"https://aviationweather.gov/api/data/stationinfo?ids={icao}&format=json"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        if r.status_code == 204 or not r.text.strip():
            return None
        data = r.json()
        if data and len(data) > 0:
            s = data[0]
            lat = s.get("latitude") or s.get("lat")
            lon = s.get("longitude") or s.get("lon")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
    except Exception:
        pass
    return None


def fetch_metar_smart(icao: str) -> dict:
    """METAR avec fallback automatique sur le plus proche aérodrome publiant.

    Retourne un dict :
        {
            "metar": str,            # texte METAR brut
            "source_icao": str,      # OACI réelle qui a fourni le METAR
            "is_fallback": bool,     # True si on a dû chercher ailleurs
            "distance_km": float|None,  # distance entre demandé et source
        }
    """
    icao = icao.strip().upper()
    if not _is_valid_icao(icao):
        return {"metar": "—", "source_icao": icao, "is_fallback": False, "distance_km": None}

    # 1) Tentative directe
    metar = fetch_metar(icao)
    if metar and not metar.startswith(("⚠️", "⏱️", "🌐", "❌")):
        return {"metar": metar, "source_icao": icao,
                "is_fallback": False, "distance_km": None}

    # 2) Pas de METAR direct → cherche dans un bbox autour
    coords = get_station_coords(icao)
    if not coords:
        return {"metar": f"⚠️ Aucun METAR pour {icao} et coordonnées inconnues",
                "source_icao": icao, "is_fallback": False, "distance_km": None}

    lat, lon = coords
    # bbox de ~1° (~111 km) autour
    delta = 1.0
    try:
        url = (f"https://aviationweather.gov/api/data/metar"
               f"?bbox={lat-delta},{lon-delta},{lat+delta},{lon+delta}"
               f"&format=json&hours=2")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        stations = r.json()
        if not stations:
            return {"metar": f"⚠️ Aucun METAR à {int(delta*111)} km de {icao}",
                    "source_icao": icao, "is_fallback": False, "distance_km": None}

        # Calcule distance vers chaque station, prend la plus proche
        ranked = []
        for s in stations:
            slat = s.get("lat")
            slon = s.get("lon")
            if slat is None or slon is None:
                continue
            d = _haversine_km(lat, lon, float(slat), float(slon))
            ranked.append((d, s))
        if not ranked:
            return {"metar": f"⚠️ Aucun METAR exploitable près de {icao}",
                    "source_icao": icao, "is_fallback": False, "distance_km": None}

        ranked.sort(key=lambda t: t[0])
        d, closest = ranked[0]
        raw = closest.get("rawOb") or closest.get("rawObservation") or ""
        src = closest.get("icaoId", "?")
        return {
            "metar": raw if raw else f"⚠️ METAR vide pour {src}",
            "source_icao": src,
            "is_fallback": True,
            "distance_km": round(d, 1),
        }
    except Exception as e:
        return {"metar": f"⚠️ Erreur recherche METAR proche de {icao} : {e}",
                "source_icao": icao, "is_fallback": False, "distance_km": None}


def fetch_taf_smart(icao: str, source_icao_fallback: str = None) -> dict:
    """TAF — si source_icao_fallback fourni (== le METAR a fallback), on l'utilise."""
    icao = icao.strip().upper()
    if not _is_valid_icao(icao):
        return {"taf": "—", "source_icao": icao, "is_fallback": False}

    # Si un fallback a déjà été utilisé pour le METAR, on l'utilise pour le TAF
    if source_icao_fallback and source_icao_fallback.upper() != icao:
        taf = fetch_taf(source_icao_fallback)
        return {"taf": taf, "source_icao": source_icao_fallback.upper(),
                "is_fallback": True}

    taf = fetch_taf(icao)
    if taf and not taf.startswith(("⚠️", "⏱️", "🌐", "❌")):
        return {"taf": taf, "source_icao": icao, "is_fallback": False}
    return {"taf": taf, "source_icao": icao, "is_fallback": False}
