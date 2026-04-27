"""Section 5 — Performances avion / Distances utilisables."""
import streamlit as st
import pandas as pd
from lib.state import init_state
from lib.calc import takeoff_perf, landing_perf, pressure_altitude, isa_temp_at_altitude
from lib.data import ROC_SL_MCP, ROC_SL_FLAPS10_MTOP, VY_KIAS, VX_KIAS

init_state()

st.title("📈 5. Performances avion / Distances utilisables")
st.caption("Calcul automatique TO/LDG d'après le Manuel § 5.2.4 et § 5.2.5 — "
           "interpolation bilinéaire (altitude, ISA dev) + corrections.")

# === Conditions du jour ===
st.subheader("🌍 Conditions du jour")
c1, c2, c3, c4 = st.columns(4)
c1.number_input("Altitude terrain (ft)", 0, 8000, key="perf_runway_alt", step=10)
c2.number_input("QNH (hPa)", 950, 1050, key="perf_qnh")
c3.number_input("OAT (°C)", -30, 50, key="perf_oat")
c4.number_input("Composante vent face (kt) — négatif = arrière", -20, 30,
                key="perf_headwind",
                help="Composante longitudinale du vent. Face = positif, arrière = négatif.")

c5, c6, c7, c8 = st.columns(4)
c5.checkbox("Piste en herbe", key="perf_grass")
c6.number_input("Pente piste (%, + montant / - descendant)", -3.0, 3.0,
                key="perf_slope", step=0.5)
c7.checkbox("Piste mouillée (atterrissage)", key="perf_wet")

zp = pressure_altitude(st.session_state.perf_runway_alt, st.session_state.perf_qnh)
isa = isa_temp_at_altitude(zp)
delta_isa = st.session_state.perf_oat - isa

c8.metric("Zp / ΔISA", f"{zp:.0f} ft / {delta_isa:+.0f}°C")

# === Distances utilisables (saisie) ===
st.subheader("📏 Distances utilisables piste (à saisir)")
c1, c2 = st.columns(2)
c1.number_input("TORA — Take-Off Run Available (m)", 100, 4000, key="perf_tora", step=50)
c2.number_input("LDA — Landing Distance Available (m)", 100, 4000, key="perf_lda", step=50)

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
     "Limite": f"≤ TODA ({st.session_state.perf_tora} m approx)",
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
    {
        "phase": "Décollage",
        "label": "Distance de roulement (TOR)",
        "needed": round(to["tor"]),
        "available": tora,
        "available_label": "TORA",
    },
    {
        "phase": "Décollage",
        "label": "Distance passage 15 m (TOD)",
        "needed": round(to["tod"]),
        "available": tora,
        "available_label": "TORA",
    },
    {
        "phase": "Atterrissage",
        "label": "Distance passage 15 m (LDD)",
        "needed": round(ld["ldd"]),
        "available": lda,
        "available_label": "LDA",
    },
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
