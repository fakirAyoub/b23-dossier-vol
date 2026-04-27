"""Section 7 — Masse & Centrage."""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from lib.state import init_state
from lib.calc import wb_calc
from lib.data import ENVELOPE, AIRCRAFT, MTOW, MAX_ZERO_WING, FUEL_USABLE_MAX

init_state()

st.title("⚖️ 7. Masse & Centrage")
st.caption("Calcul détaillé + enveloppe — données issues du Manuel § 6 et de la QRH p.11.")

# === Saisie ===
st.subheader("⚖️ Charges")
c1, c2 = st.columns(2)
with c1:
    st.number_input("Pilote (kg)", 0.0, 150.0, key="pilote_kg", step=1.0)
    st.number_input("Passager (kg)", 0.0, 150.0, key="pax_kg", step=1.0)
    st.number_input("Bagages arrière (kg, max 15)", 0.0, 16.0, key="bagages_arriere_kg", step=0.5)
with c2:
    st.number_input("Bagages aile gauche (kg, max 20)", 0.0, 20.0, key="bagages_aile_g_kg", step=0.5)
    st.number_input("Bagages aile droite (kg, max 20)", 0.0, 20.0, key="bagages_aile_d_kg", step=0.5)

# Le carburant et fuel_type viennent de la page Carburant
st.info(f"⛽ Carburant utilisé pour le calcul : "
        f"**{st.session_state.carburant_bord_L} L** de **{st.session_state.fuel_type}** "
        f"(modifiable dans la section Carburant).")

# === Calcul ===
wb = wb_calc(
    aircraft_id=st.session_state.avion,
    pilot_kg=st.session_state.pilote_kg,
    pax_kg=st.session_state.pax_kg,
    rear_bag_kg=st.session_state.bagages_arriere_kg,
    wing_l_kg=st.session_state.bagages_aile_g_kg,
    wing_r_kg=st.session_state.bagages_aile_d_kg,
    fuel_L=st.session_state.carburant_bord_L,
    fuel_type=st.session_state.fuel_type,
)

st.divider()
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("📊 Calcul détaillé")
    df = pd.DataFrame(wb["rows"],
                      columns=["Élément", "Masse (kg)", "Bras (m)", "Moment (kg.m)"])
    df["Masse (kg)"] = df["Masse (kg)"].round(2)
    df["Moment (kg.m)"] = df["Moment (kg.m)"].round(2)
    st.dataframe(df, hide_index=True, use_container_width=True)

    a, b, c = st.columns(3)
    a.metric("Masse totale", f"{wb['total_mass']:.1f} kg")
    b.metric("Moment total", f"{wb['total_moment']:.1f} kg.m")
    c.metric("CG", f"{wb['cg']:.3f} m")

with col2:
    st.subheader("✓ Vérifications")

    def chk(label, ok, val):
        msg = f"{'✅' if ok else '❌'} {label} — {val}"
        (st.success if ok else st.error)(msg)

    chk("Masse max (≤ 750 kg)", wb["total_mass"] <= MTOW, f"{wb['total_mass']:.1f} kg")
    chk("Bagages arrière (≤ 15 kg)", st.session_state.bagages_arriere_kg <= 15,
        f"{st.session_state.bagages_arriere_kg} kg")
    chk("Aile gauche (≤ 20 kg)", st.session_state.bagages_aile_g_kg <= 20,
        f"{st.session_state.bagages_aile_g_kg} kg")
    chk("Aile droite (≤ 20 kg)", st.session_state.bagages_aile_d_kg <= 20,
        f"{st.session_state.bagages_aile_d_kg} kg")
    chk("Carburant (≤ 118 L)", st.session_state.carburant_bord_L <= FUEL_USABLE_MAX,
        f"{st.session_state.carburant_bord_L} L")
    chk("Centrage dans enveloppe", wb["in_envelope"], f"CG = {wb['cg']:.3f} m")

    all_ok = (wb["total_mass"] <= MTOW
              and st.session_state.bagages_arriere_kg <= 15
              and st.session_state.bagages_aile_g_kg <= 20
              and st.session_state.bagages_aile_d_kg <= 20
              and st.session_state.carburant_bord_L <= FUEL_USABLE_MAX
              and wb["in_envelope"])
    st.divider()
    if all_ok:
        st.success("### ✈️ M&B CONFORME")
    else:
        st.error("### ⛔ M&B NON CONFORME")

# === Graphique ===
st.subheader("📈 Enveloppe Masse & Centrage")
fig, ax = plt.subplots(figsize=(10, 5.5))
xs, ys = zip(*ENVELOPE + [ENVELOPE[0]])
ax.fill(xs, ys, alpha=0.15, color="steelblue")
ax.plot(xs, ys, "b-", linewidth=2, label="Enveloppe autorisée")
ax.axhline(MAX_ZERO_WING, color="orange", linestyle="--", linewidth=1.5,
           label=f"Max Zero Wing Load ({MAX_ZERO_WING} kg)")
color = "green" if wb["in_envelope"] else "red"
ax.plot(wb["cg"], wb["total_mass"], "o", color=color, markersize=18, markeredgecolor="black",
        label=f"Configuration ({wb['cg']:.3f} m, {wb['total_mass']:.0f} kg)")
ax.set_xlabel("Centre de gravité — bras (m)")
ax.set_ylabel("Masse (kg)")
ax.set_xlim(1.68, 1.87)
ax.set_ylim(450, 790)
ax.grid(True, alpha=0.3)
ax.legend(loc="lower right")
ax.set_title(f"{st.session_state.avion} — Bristell B23")
st.pyplot(fig)
