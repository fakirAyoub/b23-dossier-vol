"""Section 2 — Situation Météo."""
import streamlit as st
from lib.state import init_state, render_save_load_sidebar
from lib.meteo import fetch_metar_smart, fetch_taf_smart
from lib.wind import parse_metar_full

init_state()
render_save_load_sidebar()


def _apply_extracted(target: str, parsed: dict) -> list:
    """Met à jour les session_state qnh/oat/vent_* à partir d'un METAR parsé.
    target='dep' ou 'arr'. Retourne liste de strings de ce qui a été mis à jour."""
    suffix = "" if target == "dep" else "_arr"
    msgs = []
    if parsed.get("qnh"):
        st.session_state[f"qnh{suffix}"] = parsed["qnh"]
        if target == "dep":
            st.session_state.perf_qnh = parsed["qnh"]
        msgs.append(f"QNH={parsed['qnh']}")
    if parsed.get("temp") is not None:
        st.session_state[f"oat{suffix}"] = parsed["temp"]
        if target == "dep":
            st.session_state.perf_oat = parsed["temp"]
        msgs.append(f"OAT={parsed['temp']}°C")
    if parsed.get("wind"):
        w = parsed["wind"]
        if w.get("dir") is not None:
            st.session_state[f"vent_dir{suffix}"] = w["dir"]
        if w.get("speed") is not None:
            st.session_state[f"vent_kt{suffix}"] = w["speed"]
        msgs.append(f"Vent={w.get('dir', 'VRB')}°/{w.get('speed', 0)}kt")
    return msgs

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
            # === DÉPART ===
            res_dep = fetch_metar_smart(dep)
            st.session_state.metar_dep = res_dep["metar"]
            st.session_state.metar_dep_source = res_dep["source_icao"]
            st.session_state.metar_dep_distance_km = res_dep.get("distance_km") or 0
            taf_res = fetch_taf_smart(
                dep, source_icao_fallback=res_dep["source_icao"] if res_dep["is_fallback"] else None)
            st.session_state.taf_dep = taf_res["taf"]

            # === ARRIVÉE ===
            if arr == dep:
                st.session_state.metar_arr = st.session_state.metar_dep
                st.session_state.taf_arr = st.session_state.taf_dep
                st.session_state.metar_arr_source = st.session_state.metar_dep_source
                st.session_state.metar_arr_distance_km = st.session_state.metar_dep_distance_km
            else:
                res_arr = fetch_metar_smart(arr)
                st.session_state.metar_arr = res_arr["metar"]
                st.session_state.metar_arr_source = res_arr["source_icao"]
                st.session_state.metar_arr_distance_km = res_arr.get("distance_km") or 0
                taf_res_arr = fetch_taf_smart(
                    arr, source_icao_fallback=res_arr["source_icao"] if res_arr["is_fallback"] else None)
                st.session_state.taf_arr = taf_res_arr["taf"]

            # === DÉGAGEMENT ===
            deg_list = [d.strip().upper() for d in (st.session_state.degagements or "").split(",")
                        if d.strip()]
            valid_degs = [d for d in deg_list if _valid_icao(d)]
            if valid_degs:
                res_deg = fetch_metar_smart(valid_degs[0])
                st.session_state.metar_deg = res_deg["metar"]
                taf_res_deg = fetch_taf_smart(
                    valid_degs[0],
                    source_icao_fallback=res_deg["source_icao"] if res_deg["is_fallback"] else None)
                st.session_state.taf_deg = taf_res_deg["taf"]
            elif deg_list:
                st.warning(f"⚠️ Dégagement(s) « {', '.join(deg_list)} » — aucun OACI valide.")

            # === Auto-extraction des conditions DEPART et ARRIVÉE ===
            parsed_dep = parse_metar_full(st.session_state.metar_dep)
            parsed_arr = parse_metar_full(st.session_state.metar_arr)
            updates_dep = _apply_extracted("dep", parsed_dep)
            updates_arr = _apply_extracted("arr", parsed_arr)

            # Notifications de fallback
            if res_dep["is_fallback"]:
                st.info(
                    f"📍 Pas de METAR pour **{dep}** — utilisé celui de "
                    f"**{res_dep['source_icao']}** ({res_dep['distance_km']} km)"
                )
            if arr != dep and res_arr.get("is_fallback"):
                st.info(
                    f"📍 Pas de METAR pour **{arr}** — utilisé celui de "
                    f"**{res_arr['source_icao']}** ({res_arr['distance_km']} km)"
                )

            extra_dep = f" · DEP: {', '.join(updates_dep)}" if updates_dep else ""
            extra_arr = f" · ARR: {', '.join(updates_arr)}" if updates_arr else ""
        st.success(f"✅ Récupération terminée{extra_dep}{extra_arr}")

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

st.markdown("**WINTEM à l'altitude du vol** (récupéré sur Aeroweb) :")
c1, c2, c3, c4, c5 = st.columns(5)
c1.number_input("Altitude (ft)", 0, 14000, key="wintem_alt_ft", step=500)
c2.number_input("Direction vent (°)", 0, 360, key="wintem_wind_dir", step=10)
c3.number_input("Force vent (kt)", 0, 100, key="wintem_wind_kt")
c4.number_input("Température (°C)", -50, 40, key="wintem_temp")
c5.number_input("Dérive max prévue (°)", 0, 30, key="wintem_drift_max")

# Delta ISA calculé automatiquement
isa_at_alt = 15 - 2 * (st.session_state.wintem_alt_ft / 1000)
delta_isa = st.session_state.wintem_temp - isa_at_alt
st.caption(
    f"📐 ISA à {st.session_state.wintem_alt_ft} ft = {isa_at_alt:.1f}°C  →  "
    f"**ΔISA = {delta_isa:+.1f}°C** (calculé auto)"
)

st.text_area("WINTEM — notes complémentaires (optionnel)",
             key="meteo_wintem", height=80,
             placeholder="Ex : couche de cisaillement à 4000 ft, vent variable au-dessus de 6000…")

st.divider()

# === Conditions de vol ===
st.subheader("🌡️ Conditions de vol envisagées")
st.caption(
    "🤖 Auto-rempli depuis le METAR départ quand tu cliques « Récupérer ». "
    "Tu peux re-parser si tu modifies le METAR à la main, ou éditer directement."
)

cb1, cb2 = st.columns(2)
if cb1.button("🔁 Re-parser DÉPART"):
    msgs = _apply_extracted("dep", parse_metar_full(st.session_state.metar_dep))
    st.success(f"✅ DEP : {', '.join(msgs)}" if msgs else "⚠️ Rien d'extractible.")
if cb2.button("🔁 Re-parser ARRIVÉE"):
    msgs = _apply_extracted("arr", parse_metar_full(st.session_state.metar_arr))
    st.success(f"✅ ARR : {', '.join(msgs)}" if msgs else "⚠️ Rien d'extractible.")

dep_label = st.session_state.depart or "DÉPART"
if st.session_state.metar_dep_source and st.session_state.metar_dep_source != dep_label:
    dep_label += f" (METAR de {st.session_state.metar_dep_source})"
st.markdown(f"**🛫 {dep_label}**")
c1, c2, c3, c4 = st.columns(4)
c1.number_input("QNH (hPa)", 950, 1050, key="qnh")
c2.number_input("OAT (°C)", -30, 50, key="oat")
c3.number_input("Vent — direction (°)", 0, 360, key="vent_dir")
c4.number_input("Vent — force (kt)", 0, 60, key="vent_kt")

arr_label = st.session_state.arrivee or "ARRIVÉE"
if st.session_state.metar_arr_source and st.session_state.metar_arr_source != arr_label:
    arr_label += f" (METAR de {st.session_state.metar_arr_source})"
st.markdown(f"**🛬 {arr_label}**")
ca1, ca2, ca3, ca4 = st.columns(4)
ca1.number_input("QNH (hPa) ", 950, 1050, key="qnh_arr")
ca2.number_input("OAT (°C) ", -30, 50, key="oat_arr")
ca3.number_input("Vent — direction (°) ", 0, 360, key="vent_dir_arr")
ca4.number_input("Vent — force (kt) ", 0, 60, key="vent_kt_arr")

st.divider()

# === Décision ===
st.subheader("✅ Le vol est-il envisageable ?")
st.checkbox("Oui, conditions météo favorables au vol envisagé", key="vol_envisageable")
if st.session_state.vol_envisageable:
    st.success("✈️ Vol envisageable d'un point de vue météo.")
else:
    st.error("⛔ Conditions à réévaluer.")
