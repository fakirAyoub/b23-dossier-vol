"""Section 3 — NOTAM."""
import streamlit as st
from lib.state import init_state

init_state()

st.title("📜 3. NOTAM")
st.caption("Bulletins d'aérodromes (départ/arrivée/dégagements), SUP AIP, "
           "bulletins de route étroite, AZBA.")

st.info(
    "ℹ️ Récupérer les NOTAMs sur **[notaminfo.com](https://notaminfo.com/)** "
    "ou **[SIA AIP France](https://www.sia.aviation-civile.gouv.fr/)** et "
    "coller les éléments significatifs ci-dessous."
)

st.text_area(f"**Départ ({st.session_state.depart})**",
             key="notam_depart", height=140)
st.text_area("**En route (zones traversées, AZBA, etc.)**",
             key="notam_route", height=140)
st.text_area(f"**Arrivée ({st.session_state.arrivee})**",
             key="notam_arrivee", height=140)
st.text_area(f"**Dégagement(s) ({st.session_state.degagements or '—'})**",
             key="notam_degagements", height=140)

st.divider()
st.subheader("✅ Le vol est-il réalisable ?")
st.checkbox("Oui, aucun NOTAM bloquant identifié", key="vol_realisable")
if st.session_state.vol_realisable:
    st.success("✈️ Vol réalisable d'un point de vue NOTAM.")
else:
    st.warning("⚠️ Vérifier les NOTAMs avant de valider.")
