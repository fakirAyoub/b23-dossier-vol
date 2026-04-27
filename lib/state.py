"""Initialisation et helpers pour st.session_state."""
import streamlit as st
from datetime import date

DEFAULTS = {
    # Cover
    "date_vol": date.today(),
    "eleve": "",
    "instructeur": "",
    "avion": "F-HBTI",
    "depart": "LFPN",
    "arrivee": "LFPN",
    "degagements": "",

    # Météo
    "metar_dep": "", "taf_dep": "",
    "metar_arr": "", "taf_arr": "",
    "metar_deg": "", "taf_deg": "",
    "meteo_temsi": "", "meteo_wintem": "",
    "vol_envisageable": False,
    "qnh": 1013, "oat": 15,
    "vent_dir": 0, "vent_kt": 0,

    # NOTAM
    "notam_depart": "", "notam_route": "",
    "notam_arrivee": "", "notam_degagements": "",
    "vol_realisable": False,

    # MEL
    "mel_items": [],

    # Carburant
    "duree_vol_h": 1.0, "conso_lh": 20.0,
    "regime_vol": "VFR Jour (30 min)",
    "deroutement_min": 0,
    "reserve_acaf_min": 30,
    "carburant_bord_L": 60.0,
    "fuel_type": "AVGAS 100LL",

    # Charges (M&B)
    "pilote_kg": 80.0, "pax_kg": 0.0,
    "bagages_arriere_kg": 0.0,
    "bagages_aile_g_kg": 0.0, "bagages_aile_d_kg": 0.0,

    # Performances
    "perf_runway_alt": 538,        # ft (LFPN)
    "perf_qnh": 1013,
    "perf_oat": 15,
    "perf_grass": False,
    "perf_slope": 0.0,
    "perf_wet": False,
    "perf_headwind": 0,
    "perf_tora": 1100,             # m TORA LFPN piste 25
    "perf_lda": 1100,

    # Journal de navigation
    "branches": [],                # liste de dicts {from, to, alt, rv, dist_nm, ...}
    "tas_kt": 100,
    "magnetic_variation": 1.0,     # +1° E pour la France
    "deviation_compas": 0,

    # Équipements
    "equip_lampe": False, "equip_trousse": False, "equip_extincteur": False,
    "equip_balise": False, "equip_gilets": False,

    # Procédures
    "panne_radio_depart": "",
    "panne_radio_route": "",
    "panne_radio_arrivee": "",
    "panne_radio_degagement": "",

    # Checklists diverses
    "douanes_notes": "",
    "atc_hors_horaires_notes": "",
    "parking_notes": "",
    "consignes_ad_notes": "",
    "surete_notes": "",
}


def init_state():
    """À appeler en haut de chaque page."""
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
