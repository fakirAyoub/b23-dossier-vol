"""Section 6 — Plan carburant complet (Part-NCO + ACAF)."""
import streamlit as st
import pandas as pd
from lib.state import init_state
from lib.calc import fuel_planning
from lib.data import FUEL_USABLE_MAX

init_state()

st.title("⛽ 6. Carburant")
st.caption("Plan carburant conforme **Part-NCO.OP.125** + réserve **ACAF**.")

# === Saisie ===
st.subheader("📝 Plan vol")
c1, c2 = st.columns(2)
with c1:
    st.number_input("Durée vol prévue (h)", 0.0, 7.0, key="duree_vol_h", step=0.25,
                    help="Temps en croisière (hors roulage et atterrissage)")
    st.number_input("Conso croisière (L/h)", 10.0, 30.0, key="conso_lh", step=0.5,
                    help="Typique B23 : ≈ 17 éco / 20 normal / 25 max")
with c2:
    st.radio("Régime de vol",
             ["VFR Jour A→A terrain en vue (10 min)",
              "VFR Jour (30 min)",
              "VFR Nuit (45 min)"],
             key="regime_vol")
    st.number_input("Déroutement (min)", 0, 90, key="deroutement_min", step=5)

st.number_input("Réserve ACAF additionnelle (min)", 0, 60, key="reserve_acaf_min", step=5,
                help="Marge club ajoutée à la réserve réglementaire (ACAF : 30 min)")

st.divider()
st.subheader("⛽ Carburant à bord")
c1, c2 = st.columns(2)
c1.number_input("Quantité au décollage (L, max 118)", 0.0, 120.0,
                key="carburant_bord_L", step=1.0)
c2.selectbox("Type carburant", ["AVGAS 100LL", "SP98"], key="fuel_type")

# === Calcul ===
plan = fuel_planning(
    duree_h=st.session_state.duree_vol_h,
    conso_lh=st.session_state.conso_lh,
    regime=st.session_state.regime_vol,
    deroutement_min=st.session_state.deroutement_min,
    reserve_acaf_min=st.session_state.reserve_acaf_min,
)
fuel_min = plan["total_min_L"]
onboard = st.session_state.carburant_bord_L
margin = round(onboard - fuel_min, 1)
fuel_ok = margin >= 0
complement = max(0.0, -margin)

st.divider()
st.subheader("🧮 Calcul du carburant minimum requis")
df_fuel = pd.DataFrame(plan["lines"], columns=["Poste", "Volume (L)", "Référence"])
st.dataframe(df_fuel, hide_index=True, use_container_width=True)

c1, c2, c3 = st.columns(3)
c1.metric("Minimum requis", f"{fuel_min:.1f} L")
c2.metric("Au décollage", f"{onboard:.1f} L")
c3.metric("Marge", f"{margin:+.1f} L",
          delta_color="normal" if fuel_ok else "inverse")

st.divider()
if onboard > FUEL_USABLE_MAX:
    st.error(f"⛔ Quantité au décollage ({onboard} L) dépasse la capacité utilisable ({FUEL_USABLE_MAX} L).")
elif fuel_ok:
    st.success(f"✅ **Carburant suffisant** — Marge de **{margin:.1f} L** au-dessus du minimum.")
    rest_arrival = (onboard - 5 - plan["flight_L"] - 7
                    - (st.session_state.deroutement_min / 60 * st.session_state.conso_lh))
    if rest_arrival < 0:
        st.warning(
            f"⚠️ Carburant restant estimé à l'arrivée **négatif** ({rest_arrival:.1f} L) — "
            f"vérifie tes hypothèses (durée, conso, déroutement). "
            f"Tu peux atteindre la destination + déroutement, mais tu rognerais sur la réserve."
        )
    else:
        st.info(f"💡 Carburant restant estimé à l'arrivée (avant réserve) : **{rest_arrival:.1f} L**")
else:
    st.error(f"⛔ **Complément nécessaire** — Il manque **{complement:.1f} L** "
             f"pour atteindre le minimum réglementaire ({fuel_min:.1f} L).")
    st.warning(f"➡️ Faire un complément d'au moins **{complement:.1f} L** avant le vol.")

with st.expander("ℹ️ Détail des hypothèses"):
    st.markdown(f"""
- **Forfaits QRH** (page 9) :
    - Démarrage + Roulage + Décollage : **5 L**
    - Procédure intégration + Atterrissage : **7 L**
- **Réserve réglementaire** (Part-NCO.OP.125) :
    - VFR Jour A→A terrain en vue : **10 min**
    - VFR Jour autre : **30 min**
    - VFR Nuit : **45 min**
- **Réserve ACAF** : par défaut **30 min** (modifiable ci-dessus)
- **Capacité utilisable B23** : 2 × 59 L = **{FUEL_USABLE_MAX} L** total
""")
