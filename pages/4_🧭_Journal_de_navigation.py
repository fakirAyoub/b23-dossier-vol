"""Section 4 — Journal de navigation."""
import math
import streamlit as st
import pandas as pd
from lib.state import init_state
from lib.calc import wind_triangle, magnetic_heading

init_state()

st.title("🧭 4. Journal de navigation")
st.caption("Log de Nav VFR — branches avec triangle des vents intégré.")

COLS_INFO = [
    ("De",        "str",   ""),
    ("Vers",      "str",   ""),
    ("Alt (ft)",  "float", 0),
    ("Rv (°)",    "float", 0),
    ("Dist (NM)", "float", 0),
    ("WD (°)",    "float", 0),
    ("WS (kt)",   "float", 0),
    ("Fréq.",     "str",   ""),
    ("Notes",     "str",   ""),
]
COLS = [c[0] for c in COLS_INFO]


def safe_float(v):
    """Convertit en float ; None si invalide ou NaN."""
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def safe_str(v):
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("none", "nan", "<na>") else s


def normalize_branch(b: dict) -> dict:
    """Nettoie une ligne pour la session state (zéros au lieu de None)."""
    out = {}
    for col, kind, default in COLS_INFO:
        v = b.get(col)
        if kind == "str":
            out[col] = safe_str(v)
        else:
            out[col] = safe_float(v) if safe_float(v) is not None else default
    return out


# === Paramètres globaux ===
st.subheader("Paramètres globaux du vol")
c1, c2, c3, c4 = st.columns(4)
c1.number_input("TAS (kt)", 60, 140, key="tas_kt")
c2.number_input("Conso (L/h)", 10.0, 30.0, key="conso_lh", step=0.5)
c3.number_input("Variation magnétique (° E+ / W-)", -10.0, 10.0,
                key="magnetic_variation", step=0.5,
                help="France : ≈ +1°E (variable selon région et année)")
c4.number_input("Déviation compas (°)", -10, 10, key="deviation_compas")

st.divider()

# === Saisie des branches ===
st.subheader("📋 Branches de la navigation")

# Charger état nettoyé
saved = st.session_state.branches
if not saved:
    saved = [{"De": "LFPN", "Vers": "", "Alt (ft)": 2500, "Rv (°)": 270,
              "Dist (NM)": 10, "WD (°)": 270, "WS (kt)": 10, "Fréq.": "", "Notes": ""}]
saved = [normalize_branch(b) for b in saved]

df = pd.DataFrame(saved, columns=COLS)

edited = st.data_editor(
    df, num_rows="dynamic", use_container_width=True,
    column_config={
        "De":        st.column_config.TextColumn("De", width="small"),
        "Vers":      st.column_config.TextColumn("Vers", width="small"),
        "Alt (ft)":  st.column_config.NumberColumn("Alt (ft)", min_value=0, max_value=14000, step=100, default=0),
        "Rv (°)":    st.column_config.NumberColumn("Rv (°)", min_value=0, max_value=359, step=1, default=0),
        "Dist (NM)": st.column_config.NumberColumn("Dist (NM)", min_value=0.0, step=0.1, default=0.0, format="%.1f"),
        "WD (°)":    st.column_config.NumberColumn("WD (°)", min_value=0, max_value=359, step=10, default=0),
        "WS (kt)":   st.column_config.NumberColumn("WS (kt)", min_value=0, max_value=80, step=1, default=0),
        "Fréq.":     st.column_config.TextColumn("Fréq.", width="small"),
        "Notes":     st.column_config.TextColumn("Notes", width="medium"),
    },
)

# Sauver normalisé (None/NaN → 0 ou "")
st.session_state.branches = [normalize_branch(r) for r in edited.to_dict(orient="records")]

# === Calculs ===
st.divider()
st.subheader("🧮 Résultats des calculs (triangle des vents)")

results = []
warnings = []
total_dist = 0.0
total_time_min = 0.0
total_fuel_L = 0.0
tas = max(1, st.session_state.tas_kt)  # éviter division par zéro

for idx, b in enumerate(st.session_state.branches, start=1):
    dist = b.get("Dist (NM)", 0)
    rv = b.get("Rv (°)", 0)
    wd = b.get("WD (°)", 0)
    ws = b.get("WS (kt)", 0)

    if not (b.get("De") or b.get("Vers")) and dist == 0:
        continue  # ligne complètement vide

    if dist <= 0:
        warnings.append(f"⚠️ Branche {idx} ({b.get('De','?')} → {b.get('Vers','?')}) : "
                        f"distance nulle, ignorée du calcul.")
        continue

    tri = wind_triangle(rv, tas, wd, ws)
    th = tri["th"]
    mh = magnetic_heading(th, st.session_state.magnetic_variation)
    cm = (mh + st.session_state.deviation_compas) % 360
    gs = tri["gs"]

    if gs <= 0:
        warnings.append(f"⚠️ Branche {idx} : vent arrière trop fort (GS ≤ 0). "
                        f"Reconsidère la route ou l'altitude.")
        continue

    time_min = (dist / gs) * 60
    fuel_L = (time_min / 60) * st.session_state.conso_lh

    total_dist += dist
    total_time_min += time_min
    total_fuel_L += fuel_L

    results.append({
        "De → Vers": f"{b.get('De','')} → {b.get('Vers','')}",
        "Alt (ft)": int(b.get("Alt (ft)", 0)),
        "Rv (°)": int(round(rv)),
        "Cv/TH (°)": int(round(th)),
        "Cm (°)": int(round(cm)),
        "Dérive (°)": round(tri["wca"], 1),
        "GS (kt)": round(gs, 1),
        "Dist (NM)": round(dist, 1),
        "Durée (min)": round(time_min, 1),
        "Fuel (L)": round(fuel_L, 1),
    })

for w in warnings:
    st.warning(w)

if results:
    df_res = pd.DataFrame(results)
    st.dataframe(df_res, hide_index=True, use_container_width=True)

    a, b_col, c = st.columns(3)
    a.metric("Distance totale", f"{total_dist:.1f} NM")
    b_col.metric("Durée totale",
                 f"{int(total_time_min // 60)}h{int(total_time_min % 60):02d} ({total_time_min:.0f} min)")
    c.metric("Fuel total branches", f"{total_fuel_L:.1f} L")
else:
    st.info("ℹ️ Saisis une distance > 0 pour voir les calculs.")

st.caption("ℹ️ **Rv** = Route vraie · **Cv/TH** = Cap vrai (true heading) · "
           "**Cm** = Cap magnétique · Dérive = WCA")
