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
    "perf_tora": 1100,
    "perf_lda": 1100,
    "perf_runway_ident": "25R",    # piste sélectionnée
    "perf_use_metar_wind": True,   # calcul auto vent depuis METAR

    # Journal de navigation
    "branches": [],
    "tas_kt": 100,
    "magnetic_variation": 1.0,
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
    """À appeler en haut de chaque page.

    Note : le 'touch' `st.session_state[k] = st.session_state[k]` est un
    workaround documenté de Streamlit. Sans ça, dans une appli multipage
    les valeurs des widgets sont réinitialisées quand on quitte la page
    où elles ont été créées (Streamlit "garbage collecte" les clés
    de widgets non utilisés sur la nouvelle page). Le re-assignement
    force la persistance.
    Ref : https://docs.streamlit.io/develop/concepts/multipage-apps/widgets
    """
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
        else:
            # Touch pour forcer la persistance entre pages
            st.session_state[k] = st.session_state[k]


def render_save_load_sidebar():
    """Boutons Sauvegarder / Charger un dossier dans la sidebar."""
    from .dossier_io import export_dossier_to_json, import_dossier_from_json, suggested_filename

    with st.sidebar:
        st.divider()
        st.subheader("💾 Dossier")

        # Export
        try:
            json_text = export_dossier_to_json()
            st.download_button(
                "📥 Sauvegarder (JSON)",
                data=json_text,
                file_name=suggested_filename(),
                mime="application/json",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erreur export : {e}")

        # Import
        uploaded = st.file_uploader("📤 Charger un dossier", type=["json"],
                                     key="_dossier_uploader",
                                     label_visibility="collapsed")
        if uploaded is not None:
            txt = uploaded.read().decode("utf-8")
            ok, msg = import_dossier_from_json(txt)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
