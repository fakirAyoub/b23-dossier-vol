"""Section 2 — Situation Météo."""
import streamlit as st
from lib.state import init_state
from lib.meteo import fetch_metar, fetch_taf

init_state()

st.title("🌤️ 2. Situation Météo")
st.caption("METAR/TAF récupérés automatiquement via aviationweather.gov · "
           "Compléter manuellement TEMSI, WINTEM, etc.")

# === METAR/TAF auto ===
st.subheader("📡 METAR / TAF (récupération automatique)")

def _valid_icao(s: str) -> bool:
    s = (s or "").strip().upper()
    return len(s) == 4 and s.isalpha()


if st.button("🔄 Récupérer METAR & TAF maintenant"):
    dep = (st.session_state.depart or "").strip().upper()
    arr = (st.session_state.arrivee or "").strip().upper()

    errors = []
    if not _valid_icao(dep):
        errors.append(f"⛔ OACI départ invalide : « {dep or '(vide)'} » — saisis 4 lettres "
                      f"(ex : LFPN) sur la page d'accueil.")
    if not _valid_icao(arr):
        errors.append(f"⛔ OACI arrivée invalide : « {arr or '(vide)'} » — saisis 4 lettres.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Récupération en cours..."):
            st.session_state.metar_dep = fetch_metar(dep)
            st.session_state.taf_dep = fetch_taf(dep)
            if arr != dep:
                st.session_state.metar_arr = fetch_metar(arr)
                st.session_state.taf_arr = fetch_taf(arr)
            else:
                st.session_state.metar_arr = st.session_state.metar_dep
                st.session_state.taf_arr = st.session_state.taf_dep
            deg_list = [d.strip().upper() for d in (st.session_state.degagements or "").split(",")
                        if d.strip()]
            valid_degs = [d for d in deg_list if _valid_icao(d)]
            if valid_degs:
                st.session_state.metar_deg = fetch_metar(valid_degs[0])
                st.session_state.taf_deg = fetch_taf(valid_degs[0])
            elif deg_list:
                st.warning(f"⚠️ Dégagement(s) « {', '.join(deg_list)} » — aucun OACI valide. "
                           f"Saisis-les sur la page d'accueil pour récupérer leur météo.")
        st.success("✅ Récupération terminée.")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"**Départ — {st.session_state.depart}**")
    st.text_area("METAR", key="metar_dep", height=80)
    st.text_area("TAF", key="taf_dep", height=120)
with c2:
    st.markdown(f"**Arrivée — {st.session_state.arrivee}**")
    st.text_area("METAR", key="metar_arr", height=80)
    st.text_area("TAF", key="taf_arr", height=120)
with c3:
    deg = st.session_state.degagements.split(",")[0].strip() if st.session_state.degagements else "—"
    st.markdown(f"**Dégagement — {deg}**")
    st.text_area("METAR", key="metar_deg", height=80)
    st.text_area("TAF", key="taf_deg", height=120)

st.divider()

# === Saisie manuelle TEMSI/WINTEM ===
st.subheader("🌐 Cartes Aeroweb / Ogimet")
st.caption("Récupérer manuellement sur Aeroweb, copier les éléments clés ci-dessous.")

st.text_area("TEMSI France — temps significatif sur le trajet "
             "(visibilité, nuages, plafonds, fronts…)",
             key="meteo_temsi", height=120)
st.text_area("WINTEM — direction/force vent à l'altitude du vol, T°, ΔISA, dérive max",
             key="meteo_wintem", height=120)

st.divider()

# === Conditions de vol ===
st.subheader("🌡️ Conditions de vol envisagées")
c1, c2, c3, c4 = st.columns(4)
c1.number_input("QNH (hPa)", 950, 1050, key="qnh")
c2.number_input("OAT au sol (°C)", -30, 50, key="oat")
c3.number_input("Vent — direction (°)", 0, 360, key="vent_dir")
c4.number_input("Vent — force (kt)", 0, 60, key="vent_kt")

st.divider()

# === Décision ===
st.subheader("✅ Le vol est-il envisageable ?")
st.checkbox("Oui, conditions météo favorables au vol envisagé", key="vol_envisageable")
if st.session_state.vol_envisageable:
    st.success("✈️ Vol envisageable d'un point de vue météo.")
else:
    st.error("⛔ Conditions à réévaluer.")
