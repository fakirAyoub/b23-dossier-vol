"""Section 1 — État avion (MEL)."""
import streamlit as st
import pandas as pd
from lib.state import init_state

init_state()

st.title("🛠️ 1. État avion (MEL)")
st.caption("Suite à la visite prévol et étude des remarques du carnet de route, "
           "lister les systèmes/équipements affectés.")

st.markdown(
    "Ajoute autant de lignes que nécessaire avec le **+** sous le tableau. "
    "Laisse vide si l'avion est intégralement opérationnel."
)

COLS = ["Système / Équipement", "Statut", "Effet sur le vol"]


def to_clean_str(v) -> str:
    """Nettoie un input : None / NaN / 'None' / 'nan' → chaîne vide."""
    if v is None:
        return ""
    s = str(v).strip()
    if s.lower() in ("none", "nan", "<na>"):
        return ""
    return s


# Charger l'état nettoyé depuis la session
saved = st.session_state.mel_items
if not saved:
    saved = [{c: "" for c in COLS}]

clean_rows = [{c: to_clean_str(r.get(c)) for c in COLS} for r in saved]

# DataFrame typé string — évite que pandas affiche "None" / "NaN"
df = pd.DataFrame(clean_rows, columns=COLS).astype("string").fillna("")

# Pas de key= : on garde notre DataFrame comme source de vérité
edited = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Système / Équipement": st.column_config.TextColumn(width="medium", default=""),
        "Statut": st.column_config.TextColumn(width="small", default=""),
        "Effet sur le vol": st.column_config.TextColumn(width="large", default=""),
    },
)

# Re-nettoyer avant sauvegarde
st.session_state.mel_items = [
    {c: to_clean_str(r.get(c)) for c in COLS}
    for r in edited.to_dict(orient="records")
]

st.divider()
filled = [r for r in st.session_state.mel_items if any(v.strip() for v in r.values())]
if not filled:
    st.success("✅ Aucun item MEL — avion entièrement opérationnel pour le vol envisagé.")
else:
    st.warning(f"⚠️ **{len(filled)} item(s)** affecté(s) — vérifier l'impact sur le vol.")
    with st.expander("Récapitulatif des items"):
        st.dataframe(pd.DataFrame(filled), hide_index=True, use_container_width=True)
