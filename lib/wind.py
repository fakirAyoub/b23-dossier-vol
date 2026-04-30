"""Parsing METAR + calcul des composantes vent (face/travers) sur une piste."""
import math
import re


METAR_WIND_PATTERN = re.compile(
    r"\b(?P<dir>\d{3}|VRB)(?P<spd>\d{2,3})(?:G(?P<gust>\d{2,3}))?(?:KT|MPS|KMH)\b"
)
# QNH : Q1018 (hPa) ou A2992 (inHg)
METAR_QNH_PATTERN = re.compile(r"\bQ(\d{4})\b|\bA(\d{4})\b")
# Température/dew : 12/03 ou M02/M05 (M = négatif)
METAR_TEMP_PATTERN = re.compile(r"\s(M?\d{2})/(M?\d{2})\s")


def parse_metar_qnh(metar: str) -> int | None:
    """Extrait le QNH en hPa depuis un METAR. None si pas trouvé."""
    if not metar:
        return None
    m = METAR_QNH_PATTERN.search(metar.upper())
    if not m:
        return None
    if m.group(1):
        return int(m.group(1))
    # A29.92 = altimeter setting en pouces de mercure → conversion vers hPa
    inhg = int(m.group(2)) / 100
    return round(inhg * 33.8639)


def parse_metar_temp(metar: str) -> int | None:
    """Extrait la température en °C. None si pas trouvée."""
    if not metar:
        return None
    m = METAR_TEMP_PATTERN.search(metar.upper())
    if not m:
        return None
    t = m.group(1)
    if t.startswith("M"):
        return -int(t[1:])
    return int(t)


def parse_metar_full(metar: str) -> dict:
    """Retourne {wind, qnh, temp} parsés depuis METAR."""
    return {
        "wind": parse_metar_wind(metar),
        "qnh": parse_metar_qnh(metar),
        "temp": parse_metar_temp(metar),
    }


def parse_metar_wind(metar: str) -> dict | None:
    """
    Extrait la direction et force du vent depuis un METAR.
    Retourne {"dir": int|None, "speed": int, "gust": int|None, "variable": bool}
    ou None si non trouvé.
    """
    if not metar:
        return None
    m = METAR_WIND_PATTERN.search(metar.upper())
    if not m:
        # Calme : "00000KT"
        if re.search(r"\b00000KT\b", metar.upper()):
            return {"dir": None, "speed": 0, "gust": None, "variable": False, "calm": True}
        return None
    dir_str = m.group("dir")
    spd = int(m.group("spd"))
    gust = int(m.group("gust")) if m.group("gust") else None
    if dir_str == "VRB":
        return {"dir": None, "speed": spd, "gust": gust, "variable": True, "calm": False}
    return {
        "dir": int(dir_str),
        "speed": spd,
        "gust": gust,
        "variable": False,
        "calm": False,
    }


def wind_components(wind_dir_deg: float, wind_speed_kt: float,
                    runway_heading_deg: float) -> dict:
    """
    Calcule les composantes vent sur une piste.
    Convention : wind_dir_deg = direction d'OÙ vient le vent.
                 runway_heading_deg = cap vrai d'utilisation de la piste (sens d'atterrissage/décollage).

    Retourne :
        headwind   (positif = face, négatif = arrière)
        crosswind  (signé : positif = de droite, négatif = de gauche)
        crosswind_abs : composante de travers en valeur absolue
        component_label : "face" / "arrière" / "calme"
    """
    if wind_speed_kt <= 0 or wind_dir_deg is None:
        return {"headwind": 0, "crosswind": 0, "crosswind_abs": 0,
                "component_label": "calme"}
    diff_rad = math.radians(wind_dir_deg - runway_heading_deg)
    headwind = wind_speed_kt * math.cos(diff_rad)
    crosswind = wind_speed_kt * math.sin(diff_rad)
    label = "face" if headwind >= 0 else "arrière"
    return {
        "headwind": round(headwind, 1),
        "crosswind": round(crosswind, 1),
        "crosswind_abs": round(abs(crosswind), 1),
        "component_label": label,
    }
