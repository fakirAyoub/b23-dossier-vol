"""Section 8 — Checklists & procédures (équipements, panne radio, divers)."""
import streamlit as st
from lib.state import init_state

init_state()

st.title("📋 8. Checklists & Procédures")
st.caption("Équipements de secours, procédures panne radio, formalités diverses.")

tabs = st.tabs([
    "🆘 Équipements de secours",
    "📻 Panne radio",
    "🛂 Douanes",
    "🌙 ATC hors horaires",
    "🅿️ Préavis parking",
    "📝 Consignes A/D",
    "🔒 Sûreté",
])

# === Équipements ===
with tabs[0]:
    st.subheader("🆘 Équipements de secours")
    st.checkbox("Lampe électrique", key="equip_lampe")
    st.checkbox("Trousse de premiers secours", key="equip_trousse")
    st.checkbox("Extincteur à main", key="equip_extincteur")
    st.checkbox("Balise de détresse (ELT)", key="equip_balise")
    st.checkbox("Gilets de sauvetage", key="equip_gilets")
    n_ok = sum([
        st.session_state.equip_lampe,
        st.session_state.equip_trousse,
        st.session_state.equip_extincteur,
        st.session_state.equip_balise,
        st.session_state.equip_gilets,
    ])
    st.divider()
    if n_ok == 5:
        st.success("✅ Tous les équipements de secours sont à bord et opérationnels.")
    else:
        st.warning(f"⚠️ {n_ok}/5 équipements vérifiés.")

# === Panne radio ===
with tabs[1]:
    st.subheader("📻 Procédures panne radio (afficher 7600)")
    st.text_area("Au départ", key="panne_radio_depart", height=100,
                 placeholder="Ex : retour parking si avant point d'arrêt, "
                             "ou décollage et tour de piste à vue avec signaux lumineux…")
    st.text_area("En route", key="panne_radio_route", height=100,
                 placeholder="Ex : poursuite vol, signalement par signaux visuels, "
                             "déroutement vers terrain non contrôlé…")
    st.text_area("À l'arrivée", key="panne_radio_arrivee", height=100,
                 placeholder="Ex : tour de piste standard côté piste en service, "
                             "intégration verticale terrain à 1000 ft AAL, "
                             "balancement des ailes…")
    st.text_area("Sur dégagement(s)", key="panne_radio_degagement", height=100)

# === Douanes ===
with tabs[2]:
    st.subheader("🛂 Douanes (vols internationaux)")
    st.markdown("""
- Aéroport pour dédouaner obligatoire ?
- Aéroport douanier prévu au plan de vol ?
- Horaires d'ouverture compatibles / demande faite ?
""")
    st.text_area("Notes douanes", key="douanes_notes", height=120)

# === ATC hors horaires ===
with tabs[3]:
    st.subheader("🌙 Ouverture hors horaires ATC")
    st.markdown("""
- Le terrain est-il accessible en dehors des horaires ATC ?
- Quels sont les horaires de fermeture ?
- Le PCL (Pilot Controlled Lighting) sera-t-il actif ?
""")
    st.text_area("Notes ATC hors horaires", key="atc_hors_horaires_notes", height=120)

# === Parking ===
with tabs[4]:
    st.subheader("🅿️ Préavis demande parking")
    st.markdown("""
- Un préavis est-il nécessaire ? Si oui, demande faite ?
- Une demande de handling est-elle nécessaire et à quel coût ?
""")
    st.text_area("Notes parking / handling", key="parking_notes", height=120)

# === Consignes A/D ===
with tabs[5]:
    st.subheader("📝 Consignes particulières A/D")
    st.markdown("""
- Le terrain est-il ouvert à la CAP ?
- Le terrain nécessite-t-il une qualification spéciale ?
- Y a-t-il des consignes particulières pour les vols d'entraînement ?
- Avez-vous pensé aux gilets jaunes pour circuler sur le parking ?
""")
    st.text_area("Notes consignes A/D", key="consignes_ad_notes", height=120)

# === Sûreté ===
with tabs[6]:
    st.subheader("🔒 Procédures de sûreté")
    st.markdown("""
- Avez-vous vérifié les mesures de sûreté (interdiction de descendre de l'avion ou de circuler à pied) ?
- Avez-vous pensé à prendre vos licences et pièces d'identité (carte d'identité, passeport, carte de séjour, visa) ?
""")
    st.text_area("Notes sûreté", key="surete_notes", height=120)
