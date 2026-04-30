"""Section 5 — Performances avion / Distances utilisables."""
import streamlit as st
import pandas as pd
from lib.state import init_state, render_save_load_sidebar
from lib.calc import takeoff_perf, landing_perf, pressure_altitude, isa_temp_at_altitude
from lib.data import ROC_SL_MCP, ROC_SL_FLAPS10_MTOP, VY_KIAS, VX_KIAS
from lib.airports import AIRPORTS, get_airport, best_runway_for_wind
from lib.wind import parse_metar_wind, wind_components

init_state()
render_save_load_sidebar()

st.title("📈 5. Performances avion / Distances utilisables")
st.caption("Calcul automatique TO/LDG d'après le Manuel § 5.2.4 et § 5.2.5 — "
           "interpolation bilinéaire (altitude, ISA dev) + corrections.")

# === Choix aérodrome ===
st.subheader("✈️ Aérodrome de calcul")
icao_options = ["(saisie manuelle)"] + sorted(AIRPORTS.keys())
default_icao = st.session_state.depart if st.session_state.depart in AIRPORTS else "(saisie manuelle)"
icao_sel = st.selectbox(
    "Aérodrome",
    options=icao_options,
    index=icao_options.index(default_icao),
    format_func=lambda x: x if x.startswith("(") else f"{x} — {get_airport(x)['name']}",
)

ad = get_airport(icao_sel) if not icao_sel.startswith("(") else None

# === Pré-remplissage automatique selon aérodrome + piste ===
if ad:
    rwy_idents = [r["ident"] for r in ad["runways"]]
    # Suggestion basée sur le vent METAR si disponible
    suggested = None
    metar = st.session_state.metar_dep or st.session_state.metar_arr
    parsed_wind = parse_metar_wind(metar)
    if parsed_wind and parsed_wind.get("dir") is not None:
        wd = parsed_wind["dir"]
        best = best_runway_for_wind(icao_sel, wd)
        if best:
            suggested = best["ident"]
            st.caption(f"🧭 Vent METAR {wd}°/{parsed_wind['speed']}kt → "
                       f"piste suggérée : **{suggested}**")
    rwy_default = (st.session_state.perf_runway_ident
                   if st.session_state.perf_runway_ident in rwy_idents
                   else (suggested if suggested in rwy_idents else rwy_idents[0]))
    rwy_ident = st.radio("Piste", options=rwy_idents,
                         index=rwy_idents.index(rwy_default),
                         horizontal=True, key="perf_runway_ident")
    rwy = next(r for r in ad["runways"] if r["ident"] == rwy_ident)

    # Auto-fill altitude, TORA, LDA, surface, slope
    st.session_state.perf_runway_alt = ad["elevation_ft"]
    st.session_state.perf_tora = rwy["tora"]
    st.session_state.perf_lda = rwy["lda"]
    st.session_state.perf_grass = (rwy.get("surface") == "herbe")
    st.session_state.perf_slope = rwy.get("slope", 0.0)
else:
    rwy = None
    rwy_ident = None
    parsed_wind = None

# === Conditions du jour ===
st.subheader("🌍 Conditions du jour")
c1, c2, c3 = st.columns(3)
c1.number_input("Altitude terrain (ft)", 0, 8000, key="perf_runway_alt", step=10,
                disabled=ad is not None,
                help="Auto-rempli depuis l'aérodrome sélectionné" if ad else None)
c2.number_input("QNH (hPa)", 950, 1050, key="perf_qnh")
c3.number_input("OAT (°C)", -30, 50, key="perf_oat")

# === Composante vent : auto via METAR + piste, ou manuelle ===
c4, c5 = st.columns([2, 1])
with c4:
    st.checkbox("Calculer la composante vent automatiquement (depuis METAR + piste)",
                key="perf_use_metar_wind",
                disabled=(parsed_wind is None or rwy is None))

if (st.session_state.perf_use_metar_wind and parsed_wind
        and parsed_wind.get("dir") is not None and rwy):
    wd = parsed_wind["dir"]
    ws = parsed_wind["speed"]
    comp = wind_components(wd, ws, rwy["true_heading"])
    st.session_state.perf_headwind = int(round(comp["headwind"]))
    with c5:
        st.metric("Composante vent", f"{comp['headwind']:+.0f} kt {comp['component_label']}")
    st.caption(f"Vent METAR : {wd}°/{ws}kt · piste {rwy['ident']} (cap {rwy['true_heading']}°) → "
               f"face {comp['headwind']:+.1f} kt · travers {comp['crosswind_abs']:.1f} kt")
else:
    c5.number_input("Composante vent face (kt) — négatif = arrière",
                    -20, 30, key="perf_headwind",
                    help="Composante longitudinale du vent. Face = positif, arrière = négatif.")

c6, c7, c8 = st.columns(3)
c6.checkbox("Piste en herbe", key="perf_grass",
            disabled=ad is not None,
            help="Auto-déterminé par la piste sélectionnée" if ad else None)
c7.number_input("Pente piste (%, + montant / - descendant)", -3.0, 3.0,
                key="perf_slope", step=0.5)
c8.checkbox("Piste mouillée (atterrissage)", key="perf_wet")

zp = pressure_altitude(st.session_state.perf_runway_alt, st.session_state.perf_qnh)
isa = isa_temp_at_altitude(zp)
delta_isa = st.session_state.perf_oat - isa

st.metric("Zp / ΔISA", f"{zp:.0f} ft / {delta_isa:+.0f}°C")

# === Distances utilisables ===
st.subheader("📏 Distances utilisables piste")
c1, c2 = st.columns(2)
c1.number_input("TORA — Take-Off Run Available (m)", 100, 4000, key="perf_tora", step=50,
                disabled=ad is not None)
c2.number_input("LDA — Landing Distance Available (m)", 100, 4000, key="perf_lda", step=50,
                disabled=ad is not None)

# === Calcul ===
to = takeoff_perf(zp, st.session_state.perf_oat,
                  grass=st.session_state.perf_grass,
                  slope_pct=st.session_state.perf_slope,
                  wind_kt=st.session_state.perf_headwind)
ld = landing_perf(zp, st.session_state.perf_oat,
                  grass=st.session_state.perf_grass,
                  slope_pct=st.session_state.perf_slope,
                  wet=st.session_state.perf_wet,
                  wind_kt=st.session_state.perf_headwind)

st.divider()
st.subheader("🛫 Performances décollage (volets 10°, MTOW 750 kg)")

df_to = pd.DataFrame([
    {"Indicateur": "Distance roulement (TOR)",
     "Base (m)": round(to["tor_base"]), "Corrigée (m)": round(to["tor"]),
     "Limite": f"≤ TORA ({st.session_state.perf_tora} m)",
     "OK ?": "✅" if to["tor"] <= st.session_state.perf_tora else "❌"},
    {"Indicateur": "Distance passage 15 m (TOD)",
     "Base (m)": round(to["tod_base"]), "Corrigée (m)": round(to["tod"]),
     "Limite": f"≤ TORA ({st.session_state.perf_tora} m approx)",
     "OK ?": "✅" if to["tod"] <= st.session_state.perf_tora else "❌"},
    {"Indicateur": "Distance accélération-arrêt (≈ TOR)",
     "Base (m)": round(to["tor_base"]), "Corrigée (m)": round(to["tor"]),
     "Limite": f"≤ ASDA ({st.session_state.perf_tora} m approx)",
     "OK ?": "✅" if to["tor"] <= st.session_state.perf_tora else "❌"},
])
st.dataframe(df_to, hide_index=True, use_container_width=True)

c1, c2 = st.columns(2)
c1.metric("Vy (taux montée max)", f"{VY_KIAS} kt")
c2.metric("Taux montée SL — MCP", f"{ROC_SL_MCP} ft/min")
st.caption(f"Coefficient correctif appliqué : ×{to['factor']:.2f}")

st.divider()
st.subheader("🛬 Performances atterrissage (volets 25°, MLW 750 kg)")

df_ld = pd.DataFrame([
    {"Indicateur": "Distance passage 15 m (LDD)",
     "Base (m)": round(ld["ldd_base"]), "Corrigée (m)": round(ld["ldd"]),
     "Limite": f"≤ LDA ({st.session_state.perf_lda} m)",
     "OK ?": "✅" if ld["ldd"] <= st.session_state.perf_lda else "❌"},
    {"Indicateur": "Distance roulement (LDR)",
     "Base (m)": round(ld["ldr_base"]), "Corrigée (m)": round(ld["ldr"]),
     "Limite": "—", "OK ?": "—"},
])
st.dataframe(df_ld, hide_index=True, use_container_width=True)

c1, c2 = st.columns(2)
c1.metric("Taux montée API (volets 10°, MTOP)", f"{ROC_SL_FLAPS10_MTOP} ft/min")
c2.metric("Vx (angle max)", f"{VX_KIAS} kt")
st.caption(f"Coefficient correctif appliqué : ×{ld['factor']:.2f}")

st.divider()
st.subheader("🎯 Verdict détaillé")

tora = st.session_state.perf_tora
lda = st.session_state.perf_lda

checks = [
    {"phase": "Décollage", "label": "Distance de roulement (TOR)",
     "needed": round(to["tor"]), "available": tora, "available_label": "TORA"},
    {"phase": "Décollage", "label": "Distance passage 15 m (TOD)",
     "needed": round(to["tod"]), "available": tora, "available_label": "TORA"},
    {"phase": "Atterrissage", "label": "Distance passage 15 m (LDD)",
     "needed": round(ld["ldd"]), "available": lda, "available_label": "LDA"},
]

problems = []
for chk in checks:
    diff = chk["needed"] - chk["available"]
    margin_pct = (chk["available"] - chk["needed"]) / chk["available"] * 100 if chk["available"] else 0
    if diff > 0:
        st.error(
            f"❌ **{chk['phase']} — {chk['label']}** : "
            f"requise = **{chk['needed']} m** > {chk['available_label']} disponible = "
            f"**{chk['available']} m** → **dépassement de {diff} m** "
            f"({-margin_pct:.0f}% au-delà)."
        )
        problems.append(chk)
    else:
        st.success(
            f"✅ **{chk['phase']} — {chk['label']}** : "
            f"requise = **{chk['needed']} m** ≤ {chk['available_label']} = "
            f"**{chk['available']} m** → marge de **{-diff} m** "
            f"({margin_pct:.0f}% de marge)."
        )

st.divider()
if not problems:
    st.success("### ✅ Vol envisageable — toutes les distances sont compatibles avec la piste.")
else:
    st.error(
        f"### ⛔ Vol NON envisageable sur cette piste — "
        f"{len(problems)} dépassement(s) :"
    )
    for p in problems:
        diff = p["needed"] - p["available"]
        st.markdown(f"- **{p['phase']}** ({p['label']}) → manque **{diff} m**")
    st.warning(
        "💡 Solutions possibles : choisir une piste plus longue, "
        "réduire la masse, attendre des conditions plus favorables "
        "(plus froid, vent face), ou utiliser une piste en dur si herbe."
    )

with st.expander("ℹ️ Détail des coefficients utilisés"):
    st.markdown("""
**Décollage** :
- Herbe : ×1,14 · Pente montante : ×1,05 par 1% · Pente descendante : ×0,95 par 1%
- Vent face 5 kt : −15% · Vent arrière 5 kt : +20%

**Atterrissage** :
- Herbe : ×1,18 · Mouillé : ×1,15
- Pente montante : ×0,95 par 1% · Pente descendante : ×1,05 par 1%
- Vent face 5 kt : −5% · Vent arrière 5 kt : +10%
""")
