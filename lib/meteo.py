"""Récupération METAR/TAF via aviationweather.gov (API gratuite)."""
import requests


def _is_valid_icao(icao: str) -> bool:
    return bool(icao) and len(icao) == 4 and icao.isalpha()


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
