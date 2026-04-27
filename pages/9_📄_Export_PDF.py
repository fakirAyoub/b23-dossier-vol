"""Section 9 — Export PDF du dossier complet."""
import traceback
from datetime import datetime
import streamlit as st
from fpdf import FPDF
from lib.state import init_state
from lib.calc import wb_calc, fuel_planning, takeoff_perf, landing_perf, pressure_altitude
from lib.data import MTOW

init_state()

st.title("📄 9. Export PDF du dossier")
st.caption("Génère un dossier de vol complet au format ACAF, prêt à imprimer.")


def safe(text):
    """fpdf2 Latin-1 fallback."""
    if text is None:
        return ""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def _is_filled(v) -> bool:
    """True si la valeur a un contenu non-trivial (gère None/NaN/<NA>/'None'/'nan')."""
    if v is None:
        return False
    s = str(v).strip().lower()
    return bool(s) and s not in ("none", "nan", "<na>")


def _branch_is_empty(b: dict) -> bool:
    """Une branche est vide si ni From/To texte, ni distance > 0."""
    has_text = _is_filled(b.get("De")) or _is_filled(b.get("Vers"))
    try:
        dist = float(b.get("Dist (NM)") or 0)
    except (ValueError, TypeError):
        dist = 0
    return not has_text and dist <= 0


class DossierPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, safe("ACAF — Dossier de Vol Bristell B23"), ln=1, align="C")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, safe(f"Élève : {st.session_state.eleve}  ·  "
                             f"Instructeur : {st.session_state.instructeur}  ·  "
                             f"Date : {st.session_state.date_vol}"),
                  ln=1, align="C")
        self.ln(2)
        self.set_draw_color(150, 150, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 8, safe(f"Page {self.page_no()}  ·  Généré le "
                             f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                  align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(220, 230, 245)
        self.cell(0, 8, safe(f"  {title}"), ln=1, fill=True)
        self.ln(2)
        self.set_font("Helvetica", "", 10)

    def kv(self, key, value):
        self.set_font("Helvetica", "B", 10)
        self.cell(55, 6, safe(f"{key}"))
        self.set_font("Helvetica", "", 10)
        # Utiliser multi_cell pour gérer les longs contenus sans crash
        self.multi_cell(0, 6, safe(f": {value}"))

    def label_then_paragraph(self, label, text):
        """Label en gras sur une ligne, paragraphe dessous."""
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 5, safe(f"{label} :"), ln=1)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, safe(text or "—"))
        self.ln(1)


# ============ BUILDERS PAR SECTION ============

def _build_cover(pdf):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.ln(40)
    pdf.cell(0, 14, safe("DOSSIER DE VOL"), ln=1, align="C")
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, safe(f"Bristell B23 — {st.session_state.avion}"), ln=1, align="C")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, safe(f"Élève : {st.session_state.eleve or '________'}"), ln=1, align="C")
    pdf.cell(0, 8, safe(f"Instructeur : {st.session_state.instructeur or '________'}"), ln=1, align="C")
    pdf.cell(0, 8, safe(f"Date : {st.session_state.date_vol}"), ln=1, align="C")
    pdf.ln(10)
    pdf.cell(0, 8, safe(f"Départ : {st.session_state.depart}    "
                        f"Arrivée : {st.session_state.arrivee}"), ln=1, align="C")
    pdf.cell(0, 8, safe(f"Dégagement(s) : {st.session_state.degagements or '—'}"),
             ln=1, align="C")


def _build_section_1(pdf):
    pdf.add_page()
    pdf.section_title("1. État avion (MEL)")
    items = [r for r in st.session_state.mel_items
             if any(_is_filled(v) for v in r.values())]
    if not items:
        pdf.multi_cell(0, 5, safe("Aucun item — avion entièrement opérationnel."))
        pdf.ln(2)
        return
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(60, 6, safe("Système / Équipement"), border=1)
    pdf.cell(50, 6, safe("Statut"), border=1)
    pdf.cell(80, 6, safe("Effet sur le vol"), border=1, ln=1)
    pdf.set_font("Helvetica", "", 9)
    for it in items:
        pdf.cell(60, 6, safe(it.get("Système / Équipement", "")[:40]), border=1)
        pdf.cell(50, 6, safe(it.get("Statut", "")[:30]), border=1)
        pdf.cell(80, 6, safe(it.get("Effet sur le vol", "")[:55]), border=1, ln=1)


def _build_section_2(pdf):
    pdf.add_page()
    pdf.section_title("2. Situation Météo")
    pdf.label_then_paragraph(f"METAR {st.session_state.depart}", st.session_state.metar_dep)
    pdf.label_then_paragraph(f"TAF {st.session_state.depart}", st.session_state.taf_dep)
    pdf.label_then_paragraph(f"METAR {st.session_state.arrivee}", st.session_state.metar_arr)
    pdf.label_then_paragraph(f"TAF {st.session_state.arrivee}", st.session_state.taf_arr)
    pdf.label_then_paragraph("TEMSI", st.session_state.meteo_temsi)
    pdf.label_then_paragraph("WINTEM", st.session_state.meteo_wintem)
    pdf.kv("Vol envisageable",
           "OUI" if st.session_state.vol_envisageable else "NON / À RÉÉVALUER")


def _build_section_3(pdf):
    pdf.add_page()
    pdf.section_title("3. NOTAM")
    pdf.label_then_paragraph(f"Départ ({st.session_state.depart})",
                             st.session_state.notam_depart)
    pdf.label_then_paragraph("En route", st.session_state.notam_route)
    pdf.label_then_paragraph(f"Arrivée ({st.session_state.arrivee})",
                             st.session_state.notam_arrivee)
    pdf.label_then_paragraph("Dégagements", st.session_state.notam_degagements)
    pdf.kv("Vol réalisable", "OUI" if st.session_state.vol_realisable else "NON")


def _build_section_4(pdf):
    pdf.add_page()
    pdf.section_title("4. Journal de navigation")
    branches = [b for b in st.session_state.branches if not _branch_is_empty(b)]
    if not branches:
        pdf.multi_cell(0, 5, safe("Aucune branche saisie."))
        return
    pdf.set_font("Helvetica", "B", 8)
    cols = ["De", "Vers", "Alt", "Rv", "Dist", "WD/WS", "Notes"]
    widths = [25, 25, 15, 15, 18, 25, 67]
    for c, w in zip(cols, widths):
        pdf.cell(w, 6, safe(c), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for b in branches:
        pdf.cell(25, 6, safe(str(b.get("De", ""))[:12]), border=1)
        pdf.cell(25, 6, safe(str(b.get("Vers", ""))[:12]), border=1)
        pdf.cell(15, 6, safe(str(b.get("Alt (ft)", ""))), border=1)
        pdf.cell(15, 6, safe(str(b.get("Rv (°)", ""))), border=1)
        pdf.cell(18, 6, safe(f"{b.get('Dist (NM)', '')} NM"), border=1)
        pdf.cell(25, 6, safe(f"{b.get('WD (°)','')}/{b.get('WS (kt)','')}"), border=1)
        pdf.cell(67, 6, safe(str(b.get("Notes", ""))[:45]), border=1, ln=1)


def _build_section_5(pdf):
    pdf.add_page()
    pdf.section_title("5. Performances avion")
    zp = pressure_altitude(st.session_state.perf_runway_alt, st.session_state.perf_qnh)
    to = takeoff_perf(zp, st.session_state.perf_oat,
                      grass=st.session_state.perf_grass,
                      slope_pct=st.session_state.perf_slope,
                      wind_kt=st.session_state.perf_headwind)
    ld = landing_perf(zp, st.session_state.perf_oat,
                      grass=st.session_state.perf_grass,
                      slope_pct=st.session_state.perf_slope,
                      wet=st.session_state.perf_wet,
                      wind_kt=st.session_state.perf_headwind)
    pdf.kv("Conditions",
           f"Zp={zp:.0f}ft, OAT={st.session_state.perf_oat}°C, "
           f"vent={st.session_state.perf_headwind}kt, "
           f"{'herbe' if st.session_state.perf_grass else 'dur'}, "
           f"{'mouillé' if st.session_state.perf_wet else 'sec'}")
    pdf.kv("TOR (roulement)",
           f"{round(to['tor'])} m  /  TORA = {st.session_state.perf_tora} m")
    pdf.kv("TOD (passage 15 m)",
           f"{round(to['tod'])} m  /  TORA = {st.session_state.perf_tora} m")
    pdf.kv("LDD (passage 15 m)",
           f"{round(ld['ldd'])} m  /  LDA = {st.session_state.perf_lda} m")
    pdf.kv("LDR (roulement)", f"{round(ld['ldr'])} m")
    ok_perf = (to["tor"] <= st.session_state.perf_tora and
               to["tod"] <= st.session_state.perf_tora and
               ld["ldd"] <= st.session_state.perf_lda)
    pdf.kv("Verdict", "OK" if ok_perf else "NON CONFORME")


def _build_section_6(pdf):
    pdf.add_page()
    pdf.section_title("6. Carburant")
    plan = fuel_planning(
        duree_h=st.session_state.duree_vol_h,
        conso_lh=st.session_state.conso_lh,
        regime=st.session_state.regime_vol,
        deroutement_min=st.session_state.deroutement_min,
        reserve_acaf_min=st.session_state.reserve_acaf_min,
    )
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(110, 6, safe("Poste"), border=1)
    pdf.cell(25, 6, safe("Volume (L)"), border=1)
    pdf.cell(55, 6, safe("Référence"), border=1, ln=1)
    pdf.set_font("Helvetica", "", 9)
    for line in plan["lines"]:
        pdf.cell(110, 6, safe(line[0][:55]), border=1)
        pdf.cell(25, 6, safe(f"{line[1]} L"), border=1)
        pdf.cell(55, 6, safe(line[2][:30]), border=1, ln=1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(110, 6, safe("TOTAL minimum requis"), border=1)
    pdf.cell(25, 6, safe(f"{plan['total_min_L']} L"), border=1)
    pdf.cell(55, 6, "", border=1, ln=1)
    pdf.ln(2)
    pdf.kv("Carburant à bord", f"{st.session_state.carburant_bord_L} L")
    margin = round(st.session_state.carburant_bord_L - plan["total_min_L"], 1)
    pdf.kv("Marge", f"{margin:+.1f} L")
    pdf.kv("Verdict",
           "Suffisant" if margin >= 0
           else f"Complément {-margin:.1f} L nécessaire")


def _build_section_7(pdf):
    pdf.add_page()
    pdf.section_title("7. Masse & Centrage")
    wb = wb_calc(
        aircraft_id=st.session_state.avion,
        pilot_kg=st.session_state.pilote_kg, pax_kg=st.session_state.pax_kg,
        rear_bag_kg=st.session_state.bagages_arriere_kg,
        wing_l_kg=st.session_state.bagages_aile_g_kg,
        wing_r_kg=st.session_state.bagages_aile_d_kg,
        fuel_L=st.session_state.carburant_bord_L,
        fuel_type=st.session_state.fuel_type,
    )
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(70, 6, safe("Élément"), border=1)
    pdf.cell(35, 6, safe("Masse (kg)"), border=1)
    pdf.cell(30, 6, safe("Bras (m)"), border=1)
    pdf.cell(45, 6, safe("Moment (kg.m)"), border=1, ln=1)
    pdf.set_font("Helvetica", "", 9)
    for r in wb["rows"]:
        pdf.cell(70, 6, safe(str(r[0])[:40]), border=1)
        pdf.cell(35, 6, safe(f"{r[1]:.1f}"), border=1)
        pdf.cell(30, 6, safe(f"{r[2]:.3f}"), border=1)
        pdf.cell(45, 6, safe(f"{r[3]:.1f}"), border=1, ln=1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(70, 6, safe("TOTAL"), border=1)
    pdf.cell(35, 6, safe(f"{wb['total_mass']:.1f}"), border=1)
    pdf.cell(30, 6, safe(f"{wb['cg']:.3f}"), border=1)
    pdf.cell(45, 6, safe(f"{wb['total_moment']:.1f}"), border=1, ln=1)
    pdf.ln(2)
    pdf.kv("Verdict",
           "M&B CONFORME" if (wb["total_mass"] <= MTOW and wb["in_envelope"])
           else "M&B NON CONFORME")


def _build_section_8(pdf):
    pdf.add_page()
    pdf.section_title("8. Checklists & procédures")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, safe("Équipements de secours :"), ln=1)
    pdf.set_font("Helvetica", "", 10)
    for label, key in [("Lampe électrique", "equip_lampe"),
                       ("Trousse premiers secours", "equip_trousse"),
                       ("Extincteur", "equip_extincteur"),
                       ("Balise détresse (ELT)", "equip_balise"),
                       ("Gilets sauvetage", "equip_gilets")]:
        mark = "X" if st.session_state[key] else " "
        pdf.cell(0, 5, safe(f"  [{mark}] {label}"), ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, safe("Procédures panne radio (afficher 7600) :"), ln=1)
    for label, key in [("Départ", "panne_radio_depart"),
                       ("En route", "panne_radio_route"),
                       ("Arrivée", "panne_radio_arrivee"),
                       ("Dégagements", "panne_radio_degagement")]:
        pdf.label_then_paragraph(label, st.session_state[key])
    # Notes diverses
    for label, key in [("Douanes", "douanes_notes"),
                       ("ATC hors horaires", "atc_hors_horaires_notes"),
                       ("Parking", "parking_notes"),
                       ("Consignes A/D", "consignes_ad_notes"),
                       ("Sûreté", "surete_notes")]:
        if st.session_state.get(key, "").strip():
            pdf.label_then_paragraph(label, st.session_state[key])


# ============ ORCHESTRATION ============

SECTIONS = [
    ("Page de garde",          _build_cover),
    ("1. État avion (MEL)",    _build_section_1),
    ("2. Météo",               _build_section_2),
    ("3. NOTAM",               _build_section_3),
    ("4. Journal de navigation", _build_section_4),
    ("5. Performances",        _build_section_5),
    ("6. Carburant",           _build_section_6),
    ("7. Masse & Centrage",    _build_section_7),
    ("8. Checklists",          _build_section_8),
]


def build_pdf():
    """
    Construit le PDF section par section.
    Lève une SectionError si une section échoue, en indiquant laquelle.
    """
    pdf = DossierPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()

    for name, fn in SECTIONS:
        try:
            fn(pdf)
        except Exception as e:
            raise SectionError(name, e) from e

    return bytes(pdf.output())


class SectionError(Exception):
    def __init__(self, section_name, original):
        self.section_name = section_name
        self.original = original
        super().__init__(f"[{section_name}] {type(original).__name__} : {original}")


# ============ INTERFACE ============

st.subheader("📥 Génération du PDF")
st.markdown("Vérifie que toutes les sections précédentes sont remplies, puis génère le PDF.")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Générer le dossier PDF", type="primary"):
        with st.spinner("Génération en cours..."):
            try:
                pdf_bytes = build_pdf()
                st.session_state["_pdf_bytes"] = pdf_bytes
                st.success(f"✅ Dossier généré ({len(pdf_bytes) // 1024} Ko)")
            except SectionError as e:
                st.error(
                    f"⛔ **Échec dans la section : {e.section_name}**\n\n"
                    f"**Cause** : {type(e.original).__name__} — {e.original}"
                )
                st.warning(
                    f"💡 Vérifie le contenu de la section **« {e.section_name} »** "
                    f"avant de relancer la génération."
                )
                with st.expander("🔍 Détails techniques (traceback)"):
                    st.code(traceback.format_exc(), language="python")
            except Exception as e:
                st.error(f"⛔ Erreur inattendue : {type(e).__name__} — {e}")
                with st.expander("🔍 Détails techniques"):
                    st.code(traceback.format_exc(), language="python")

with col2:
    if "_pdf_bytes" in st.session_state:
        filename = (f"dossier_B23_{st.session_state.avion}_"
                    f"{st.session_state.date_vol}.pdf")
        st.download_button("📄 Télécharger le PDF",
                           data=st.session_state["_pdf_bytes"],
                           file_name=filename, mime="application/pdf")

st.divider()
st.caption("ℹ️ Le PDF reprend les sections 1 à 8 dans l'ordre du dossier ACAF.")
