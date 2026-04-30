"""
B23 — Dossier de Vol complet
Aéroclub Air France — Toussus le Noble

Usage :
    pip install -r requirements.txt
    streamlit run b23_wb.py
"""
import streamlit as st
from lib.state import init_state, render_save_load_sidebar
from lib.airports import AIRPORTS, get_airport

st.set_page_config(
    page_title="B23 — Dossier de Vol",
    page_icon="✈️",
    layout="wide",
)

init_state()
render_save_load_sidebar()

st.title("✈️ Dossier de Vol — Bristell B23")
st.caption("Aéroclub Air France — Toussus le Noble")

st.markdown("""
## 👋 Bienvenue

Cette application vous accompagne dans la préparation complète d'un dossier de vol B23
au format **ACAF**. Saisissez les informations générales ci-dessous puis utilisez
le menu de gauche pour naviguer dans les **9 sections** du dossier.

💾 **Sauvegarde / chargement** d'un dossier dans la sidebar gauche
(format JSON, à conserver pour ressortir un même vol plus tard).
""")

st.divider()
st.subheader("📋 Informations générales du vol")

ICAO_LIST = sorted(AIRPORTS.keys())


def _airport_label(icao: str) -> str:
    ad = get_airport(icao)
    return f"{icao} — {ad['name']}" if ad else icao


c1, c2 = st.columns(2)
with c1:
    st.text_input("Élève / Pilote", key="eleve")
    st.date_input("Date du vol", key="date_vol")
    st.radio("Avion", ["F-HBTI", "F-HRDV"], key="avion", horizontal=True)

with c2:
    st.text_input("Instructeur", key="instructeur")
    # Départ : selectbox + saisie libre fallback
    dep_idx = ICAO_LIST.index(st.session_state.depart) if st.session_state.depart in ICAO_LIST else None
    dep_choice = st.selectbox(
        "Aérodrome de départ (OACI)",
        options=["✏️ Saisie libre…"] + ICAO_LIST,
        index=(ICAO_LIST.index(st.session_state.depart) + 1) if st.session_state.depart in ICAO_LIST else 0,
        format_func=lambda x: x if x.startswith("✏️") else _airport_label(x),
    )
    if dep_choice == "✏️ Saisie libre…":
        st.text_input("OACI départ (4 lettres)", key="depart", max_chars=4)
    else:
        st.session_state.depart = dep_choice

    arr_idx = ICAO_LIST.index(st.session_state.arrivee) if st.session_state.arrivee in ICAO_LIST else None
    arr_choice = st.selectbox(
        "Aérodrome d'arrivée (OACI)",
        options=["✏️ Saisie libre…"] + ICAO_LIST,
        index=(ICAO_LIST.index(st.session_state.arrivee) + 1) if st.session_state.arrivee in ICAO_LIST else 0,
        format_func=lambda x: x if x.startswith("✏️") else _airport_label(x),
    )
    if arr_choice == "✏️ Saisie libre…":
        st.text_input("OACI arrivée (4 lettres)", key="arrivee", max_chars=4)
    else:
        st.session_state.arrivee = arr_choice

    st.text_input("Dégagement(s) (OACI, séparés par virgule)", key="degagements")

# Récap aérodrome de départ
ad_dep = get_airport(st.session_state.depart)
if ad_dep:
    st.info(
        f"🛬 **{st.session_state.depart} — {ad_dep['name']}** : altitude **{ad_dep['elevation_ft']} ft** · "
        f"pistes {', '.join(r['ident'] for r in ad_dep['runways'])}"
    )

st.divider()
st.subheader("🗂️ Sections du dossier")

st.markdown("""
| # | Section | Contenu |
|---|---|---|
| **1** | 🛠️ État avion (MEL) | Système, statut, effet sur le vol |
| **2** | 🌤️ Météo | METAR/TAF (auto), TEMSI, WINTEM |
| **3** | 📜 NOTAM | Départ, route, arrivée, dégagements |
| **4** | 🧭 Journal de navigation | Branches avec triangle des vents |
| **5** | 📈 Performances | Distances TO/LDG corrigées, pré-rempli par aérodrome |
| **6** | ⛽ Carburant | Plan complet (NCO + ACAF 30 min) |
| **7** | ⚖️ Masse & Centrage | Tableau + enveloppe + verdict |
| **8** | 📋 Checklists & Procédures | Équipements, panne radio, consignes |
| **9** | 📄 Export PDF | Génération du dossier au format ACAF |

👉 **Commencez par les sections 1 à 3, puis enchaînez avec les calculs.**
""")

st.info("💡 Toutes vos saisies sont conservées entre les sections. Sauvegardez un dossier "
        "(sidebar gauche) pour le ressortir plus tard.")
