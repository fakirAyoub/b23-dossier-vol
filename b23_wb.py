"""
B23 — Dossier de Vol complet
Aéroclub Air France — Toussus le Noble

Usage :
    pip install streamlit pandas matplotlib fpdf2 requests
    streamlit run b23_wb.py
"""
import streamlit as st
from lib.state import init_state

st.set_page_config(
    page_title="B23 — Dossier de Vol",
    page_icon="✈️",
    layout="wide",
)

init_state()

st.title("✈️ Dossier de Vol — Bristell B23")
st.caption("Aéroclub Air France — Toussus le Noble")

st.markdown("""
## 👋 Bienvenue

Cette application vous accompagne dans la préparation complète d'un dossier de vol B23
au format **ACAF**. Saisissez les informations générales ci-dessous puis utilisez
le menu de gauche pour naviguer dans les **9 sections** du dossier.
""")

st.divider()
st.subheader("📋 Informations générales du vol")

c1, c2 = st.columns(2)
with c1:
    st.text_input("Élève / Pilote", key="eleve")
    st.date_input("Date du vol", key="date_vol")
    st.radio("Avion", ["F-HBTI", "F-HRDV"], key="avion", horizontal=True)
with c2:
    st.text_input("Instructeur", key="instructeur")
    st.text_input("Aérodrome de départ (OACI)", key="depart", max_chars=4)
    st.text_input("Aérodrome d'arrivée (OACI)", key="arrivee", max_chars=4)
    st.text_input("Dégagement(s) (OACI, séparés par virgule)", key="degagements")

st.divider()
st.subheader("🗂️ Sections du dossier")

st.markdown("""
| # | Section | Contenu |
|---|---|---|
| **1** | 🛠️ État avion (MEL) | Système, statut, effet sur le vol |
| **2** | 🌤️ Météo | METAR/TAF (auto), TEMSI, WINTEM |
| **3** | 📜 NOTAM | Départ, route, arrivée, dégagements |
| **4** | 🧭 Journal de navigation | Branches avec triangle des vents |
| **5** | 📈 Performances | Distances TO/LDG corrigées |
| **6** | ⛽ Carburant | Plan carburant complet (NCO + ACAF) |
| **7** | ⚖️ Masse & Centrage | Tableau + enveloppe + verdict |
| **8** | 📋 Checklists & Procédures | Équipements, panne radio, consignes |
| **9** | 📄 Export PDF | Génération du dossier complet |

👉 **Commencez par les sections 1 à 3, puis enchaînez avec les calculs.**
""")

st.info("💡 Toutes vos saisies sont conservées entre les sections tant que vous gardez l'application ouverte.")
