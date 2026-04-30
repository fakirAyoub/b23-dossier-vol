"""Section 9 — Export PDF du dossier complet (template ACAF rempli)."""
import traceback
import streamlit as st
from lib.state import init_state, render_save_load_sidebar
from lib.pdf_template import fill_acaf_template, TEMPLATE_PATH

init_state()
render_save_load_sidebar()

st.title("📄 9. Export PDF du dossier")
st.caption("Génération du dossier au format **ACAF** avec toutes tes saisies "
           "remplies sur le template officiel.")

# === Vérification template ===
if not TEMPLATE_PATH.exists():
    st.error(f"⛔ Template ACAF introuvable à : `{TEMPLATE_PATH}`")
    st.info("Le template `Dossier-vol-ACAF.pdf` doit être dans le dossier `templates/`.")
    st.stop()

# === Récap des sections remplies ===
st.subheader("📋 Récap avant génération")

def _has(v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return bool(v)


sections_status = [
    ("1. État avion (MEL)",
     any(any(_has(v) for v in r.values())
         for r in st.session_state.get("mel_items", []))),
    ("2. Météo",
     _has(st.session_state.metar_dep) or _has(st.session_state.meteo_temsi)),
    ("3. NOTAM",
     _has(st.session_state.notam_depart) or _has(st.session_state.notam_route)),
    ("4. Journal de navigation",
     any(b.get("De") or b.get("Vers") or float(b.get("Dist (NM)") or 0) > 0
         for b in st.session_state.get("branches", []))),
    ("5. Performances", True),
    ("6. Carburant", True),
    ("7. Masse & Centrage", True),
    ("8. Checklists",
     any(st.session_state[k] for k in ["equip_lampe", "equip_trousse", "equip_extincteur",
                                         "equip_balise", "equip_gilets"])),
]

cols = st.columns(2)
for i, (name, ok) in enumerate(sections_status):
    cols[i % 2].markdown(f"{'✅' if ok else '⚪'} {name}")

st.divider()

# === Génération ===
st.subheader("📥 Génération du PDF")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Générer le dossier ACAF", type="primary", use_container_width=True):
        with st.spinner("Remplissage du template..."):
            try:
                pdf_bytes = fill_acaf_template()
                st.session_state["_pdf_bytes"] = pdf_bytes
                st.success(f"✅ Dossier ACAF généré ({len(pdf_bytes) // 1024} Ko)")
            except FileNotFoundError as e:
                st.error(f"⛔ {e}")
            except Exception as e:
                st.error(f"⛔ Erreur lors de la génération : {type(e).__name__} — {e}")
                with st.expander("🔍 Détails techniques"):
                    st.code(traceback.format_exc(), language="python")

with col2:
    if "_pdf_bytes" in st.session_state:
        date_vol = st.session_state.date_vol
        date_str = date_vol.strftime("%Y-%m-%d") if hasattr(date_vol, "strftime") else str(date_vol)
        filename = (f"Dossier-vol_{date_str}_{st.session_state.avion}_"
                    f"{st.session_state.depart}-{st.session_state.arrivee}.pdf")
        st.download_button("📄 Télécharger le PDF", data=st.session_state["_pdf_bytes"],
                           file_name=filename, mime="application/pdf",
                           use_container_width=True)

st.divider()

with st.expander("ℹ️ Comment ça marche ?"):
    st.markdown("""
- L'app charge le template officiel ACAF (`templates/Dossier-vol-ACAF.pdf`)
- Pour chaque page, elle dessine en surimpression (overlay) les valeurs
  saisies dans les sections précédentes (texte, coches, tableaux)
- Le résultat est un PDF identique au format papier ACAF, mais déjà rempli
- Si une page particulière échoue, l'erreur est annotée sur cette page
  uniquement et les autres pages sont générées normalement

⚠️ **Vérifier toujours** le PDF avant de le présenter à l'instructeur — les
positionnements peuvent demander un ajustement fin selon le rendu de ton
navigateur/imprimante.
""")

st.caption("ℹ️ Le PDF reprend toutes les sections au format ACAF (12 pages).")
