"""Sauvegarde et chargement d'un dossier de vol au format JSON."""
import json
from datetime import date, datetime
import streamlit as st
from .state import DEFAULTS


# Clés à sauvegarder (= toutes celles définies dans DEFAULTS, pas les internes)
SAVED_KEYS = list(DEFAULTS.keys())


def _serialize(v):
    """Convertit les types non-JSON en strings."""
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _deserialize(key: str, v):
    """Reconvertit les strings ISO en dates si nécessaire."""
    if key == "date_vol" and isinstance(v, str):
        try:
            return date.fromisoformat(v)
        except (ValueError, TypeError):
            return date.today()
    return v


def export_dossier_to_json() -> str:
    """Exporte le state actuel en JSON formaté."""
    data = {}
    for k in SAVED_KEYS:
        if k in st.session_state:
            data[k] = _serialize(st.session_state[k])
    data["__meta__"] = {
        "exported_at": datetime.now().isoformat(),
        "version": 1,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def import_dossier_from_json(json_text: str) -> tuple[bool, str]:
    """
    Charge un JSON dans le session_state. Retourne (ok, message).
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return False, f"Fichier JSON invalide : {e}"

    n_keys = 0
    for k in SAVED_KEYS:
        if k in data:
            st.session_state[k] = _deserialize(k, data[k])
            n_keys += 1
    return True, f"✅ Dossier chargé ({n_keys} champs restaurés)."


def suggested_filename() -> str:
    """Nom de fichier basé sur la date + avion + aérodromes."""
    date_str = str(st.session_state.get("date_vol", "")) or "vol"
    avion = st.session_state.get("avion", "B23")
    dep = st.session_state.get("depart", "")
    arr = st.session_state.get("arrivee", "")
    parts = [date_str, avion]
    if dep and arr:
        parts.append(f"{dep}-{arr}")
    return "_".join(p for p in parts if p) + ".json"
