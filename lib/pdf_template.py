"""
Génération du PDF en remplissant le template ACAF (Dossier-vol-ACAF.pdf).

Stratégie : pour chaque page, on crée un overlay PDF (reportlab) avec du texte
positionné aux bonnes coordonnées, puis on le merge sur la page d'origine
avec pypdf.

Coordonnées : reportlab utilise (0, 0) en BAS-GAUCHE (axe Y vers le haut).
Page A5 = 419.52 × 595.32 pts.
"""
from io import BytesIO
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, gray, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath

from .calc import wb_calc, fuel_planning, takeoff_perf, landing_perf, pressure_altitude
from .data import AIRCRAFT, DENSITY, MTOW, ENVELOPE, MAX_ZERO_WING

PAGE_W, PAGE_H = 419.52, 595.32
TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "Dossier-vol-ACAF.pdf"


# ============================================================
# UTILITAIRES DE DESSIN
# ============================================================

def _set_font(c, size=10, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)


def _t(c, x, y_from_top, text, size=9, bold=False, color=black, max_width=None):
    """Dessine du texte. y_from_top = distance depuis le HAUT de la page (plus intuitif)."""
    if text is None or text == "":
        return
    text = str(text)
    if max_width:
        # Tronquer si trop long
        while pdfmetrics.stringWidth(text, "Helvetica", size) > max_width and len(text) > 1:
            text = text[:-1]
    y = PAGE_H - y_from_top
    _set_font(c, size, bold)
    c.setFillColor(color)
    c.drawString(x, y, text)


def _t_multiline(c, x, y_from_top, text, size=9, line_h=11, max_width=320, max_lines=10):
    """Texte multi-lignes avec word-wrap simple."""
    if not text:
        return
    text = str(text).strip()
    if not text:
        return
    _set_font(c, size, False)
    lines = []
    for raw_line in text.split("\n"):
        if not raw_line:
            lines.append("")
            continue
        words = raw_line.split(" ")
        current = ""
        for w in words:
            test = (current + " " + w).strip() if current else w
            if pdfmetrics.stringWidth(test, "Helvetica", size) > max_width:
                if current:
                    lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)
    for i, line in enumerate(lines[:max_lines]):
        c.drawString(x, PAGE_H - (y_from_top + i * line_h), line)


def _check(c, x, y_from_top, checked: bool):
    """Dessine une coche dans une case (X si coché)."""
    if checked:
        _set_font(c, 11, True)
        c.drawString(x, PAGE_H - y_from_top, "X")


def _generate_wb_envelope_image(cg: float, total_mass: float) -> BytesIO:
    """Génère le graphique d'enveloppe M&B B23 (matplotlib) en PNG."""
    fig, ax = plt.subplots(figsize=(5, 3.2), dpi=200)
    xs, ys = zip(*ENVELOPE + [ENVELOPE[0]])
    ax.fill(xs, ys, alpha=0.15, color="steelblue")
    ax.plot(xs, ys, "b-", linewidth=2, label="Enveloppe B23")
    ax.axhline(MAX_ZERO_WING, color="orange", linestyle="--", linewidth=1.2,
               label=f"Max Zero Wing Load ({MAX_ZERO_WING} kg)")

    in_env = MplPath(ENVELOPE).contains_point((cg, total_mass))
    color = "green" if in_env else "red"
    ax.plot(cg, total_mass, "o", color=color, markersize=14,
            markeredgecolor="black",
            label=f"Config ({cg:.3f} m, {total_mass:.0f} kg)")

    ax.set_xlabel("Centre de gravité — bras (m)", fontsize=8)
    ax.set_ylabel("Masse (kg)", fontsize=8)
    ax.set_xlim(1.68, 1.87)
    ax.set_ylim(450, 790)
    ax.tick_params(labelsize=7)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=6.5)
    ax.set_title("Enveloppe Masse & Centrage — Bristell B23", fontsize=9)

    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf


# ============================================================
# CONSTRUCTEURS PAR PAGE (overlays)
# ============================================================

def _draw_page_1_cover(c):
    """Page 1 — Cover : ELEVE, INSTRUCTEUR, DATE, DEPART, ARRIVEE, DEGAGEMENTS.
    Coordonnées calibrées via grille sur le template ACAF (page 1)."""
    # Ligne ELEVE / INSTRUCTEUR (y ≈ 185)
    eleve = st.session_state.get("eleve", "")
    instructeur = st.session_state.get("instructeur", "")
    _t(c, 145, 185, eleve[:20], size=10)
    _t(c, 325, 185, instructeur[:18], size=10)  # tronquer pour rester dans la box

    # DATE (y ≈ 348)
    date_vol = st.session_state.get("date_vol")
    date_str = date_vol.strftime("%d/%m/%Y") if hasattr(date_vol, "strftime") else str(date_vol or "")
    _t(c, 175, 348, date_str, size=10)

    # DEPART / ARRIVEE (y ≈ 402)
    _t(c, 140, 402, st.session_state.get("depart", ""), size=10)
    _t(c, 325, 402, st.session_state.get("arrivee", ""), size=10)

    # DEGAGEMENTS (y ≈ 425)
    _t(c, 230, 425, st.session_state.get("degagements", ""), size=10)


def _draw_page_2_checklist(c):
    """Page 2 — Checklist préparation : on coche tout ce qui a été rempli."""
    checks = [
        # (y_from_top, condition)
        (170, _has_mel()),                     # 1. ETAT AVION
        (203, st.session_state.get("vol_envisageable")),   # 2. METEO
        (236, st.session_state.get("vol_realisable")),     # 3. NOTAM
        (269, True),                            # 4. CARTE VAC LFPN (toujours fournie)
        (302, _has_branches()),                 # 5. JOURNAL DE NAV
        (335, True),                            # 6. PERFORMANCES (toujours calculé)
        (368, True),                            # 7. CARBURANT
        (401, True),                            # 8. M&B
        (434, _all_equip()),                    # 9. EQUIPEMENTS DE SECOURS
        (467, _has_panne_radio()),              # 10. PROCEDURES PANNE RADIO
        (500, False),                           # 11. PLAN DE VOL (manuel)
        (533, _has(st.session_state.get("douanes_notes"))),       # 12
        (566, _has(st.session_state.get("atc_hors_horaires_notes"))),  # 13
        (599, _has(st.session_state.get("parking_notes"))),       # 14
        (632, _has(st.session_state.get("consignes_ad_notes"))),  # 15
        (665, _has(st.session_state.get("surete_notes"))),        # 16
    ]
    # Les positions verticales ci-dessus sont approximatives — on couvre
    # surtout les items principaux (1-10). Position de la case ≈ x=410.
    for y, ok in checks[:10]:
        _check(c, 410, y, bool(ok))


def _draw_page_3_mel(c):
    """Page 3 — Tableau MEL (3 colonnes : Système, Statut, Effet)."""
    items = [r for r in st.session_state.get("mel_items", [])
             if any(_has(v) for v in r.values())]
    if not items:
        _t(c, 100, 290, "(aucun item — avion entièrement opérationnel)",
           size=9, color=gray)
        return

    # En-tête de tableau commence à y ≈ 245, hauteur de ligne ≈ 60 pt
    row_h = 60
    y_first_row_top = 250
    for i, item in enumerate(items[:6]):
        y = y_first_row_top + i * row_h + 15
        _t_multiline(c, 35, y, item.get("Système / Équipement", ""),
                     size=8, line_h=10, max_width=120, max_lines=4)
        _t_multiline(c, 165, y, item.get("Statut", ""),
                     size=8, line_h=10, max_width=140, max_lines=4)
        _t_multiline(c, 320, y, item.get("Effet sur le vol", ""),
                     size=8, line_h=10, max_width=170, max_lines=4)


def _draw_page_4_meteo(c):
    """Page 4 — Météo : on écrit un résumé en bas + tick "envisageable"."""
    summary_lines = []
    if _has(st.session_state.get("metar_dep")):
        summary_lines.append(f"METAR {st.session_state.get('depart','')} : "
                             f"{(st.session_state.get('metar_dep') or '')[:80]}")
    if _has(st.session_state.get("taf_dep")):
        summary_lines.append(f"TAF {st.session_state.get('depart','')} : "
                             f"{(st.session_state.get('taf_dep') or '')[:80]}")
    if _has(st.session_state.get("metar_arr")):
        summary_lines.append(f"METAR {st.session_state.get('arrivee','')} : "
                             f"{(st.session_state.get('metar_arr') or '')[:80]}")
    if _has(st.session_state.get("meteo_temsi")):
        summary_lines.append(f"TEMSI : {(st.session_state.get('meteo_temsi') or '')[:80]}")
    if _has(st.session_state.get("meteo_wintem")):
        summary_lines.append(f"WINTEM : {(st.session_state.get('meteo_wintem') or '')[:80]}")
    txt = "\n".join(summary_lines)
    _t_multiline(c, 35, 470, txt, size=8, line_h=10, max_width=350, max_lines=8)

    # Vol envisageable
    yes = bool(st.session_state.get("vol_envisageable"))
    _t(c, 280, 700, "OUI" if yes else "NON / À RÉÉVALUER",
       size=10, bold=True, color=(black if yes else gray))


def _draw_page_5_notam(c):
    """Page 5 — NOTAMs par section."""
    pages = [
        (255, st.session_state.get("notam_depart")),
        (335, st.session_state.get("notam_route")),
        (415, st.session_state.get("notam_arrivee")),
    ]
    for y, txt in pages:
        _t_multiline(c, 130, y, txt, size=8, line_h=10, max_width=270, max_lines=6)

    # 3 dégagements
    deg_list = [d.strip() for d in (st.session_state.get("degagements") or "").split(",") if d.strip()]
    deg_notes = (st.session_state.get("notam_degagements") or "").strip()
    # On répartit les notes globales sur les 3 lignes en gros
    y_deg = [510, 540, 570]
    for i in range(3):
        line_text = ""
        if i < len(deg_list):
            line_text = f"{deg_list[i]}"
            if i == 0 and deg_notes:
                line_text += f" — {deg_notes[:60]}"
        _t(c, 145, y_deg[i], line_text, size=9)

    # Vol réalisable ?
    yes = bool(st.session_state.get("vol_realisable"))
    _t(c, 280, 700, "OUI" if yes else "NON",
       size=10, bold=True, color=(black if yes else gray))


def _draw_page_7_journal_nav(c):
    """
    Page 7 — Journal de nav : page descriptive sans tableau pré-imprimé.
    On ajoute un récap des branches en dessous des bullets.
    """
    branches = [b for b in st.session_state.get("branches", [])
                if (b.get("De") or b.get("Vers"))
                and float(b.get("Dist (NM)") or 0) > 0]
    if not branches:
        return
    # Liste compacte des branches
    y0 = 380
    _t(c, 35, y0, "Récap branches saisies dans l'app :", size=9, bold=True)
    for i, b in enumerate(branches[:8]):
        line = (f"  {b.get('De','?')} → {b.get('Vers','?')}  "
                f"Alt {int(b.get('Alt (ft)', 0))}ft  "
                f"Rv {int(b.get('Rv (°)', 0))}°  "
                f"{float(b.get('Dist (NM)') or 0):.1f}NM  "
                f"vent {int(b.get('WD (°)', 0))}°/{int(b.get('WS (kt)', 0))}kt")
        _t(c, 35, y0 + 15 + i * 12, line, size=8)


def _draw_page_8_perfs(c):
    """Page 8 — Performances complètes : DEPART + ARRIVEE + DEGAGEMENT(S).

    Pour chaque aérodrome, on déduit conditions depuis le METAR si dispo,
    sinon on utilise les valeurs saisies (DEPART) ou par défaut.
    """
    from .data import ROC_SL_MCP, ROC_SL_FLAPS10_MTOP
    from .airports import get_airport
    from .wind import parse_metar_full, wind_components

    grass = st.session_state.get("perf_grass", False)
    slope = st.session_state.get("perf_slope", 0.0)
    wet = st.session_state.get("perf_wet", False)
    tora = st.session_state.get("perf_tora", 1100)
    lda = st.session_state.get("perf_lda", 1100)

    # === Conditions par aéroport (DEPART, ARRIVEE, DEGAGEMENT 1) ===
    # Conditions DEPART — saisies dans l'app
    dep_qnh = st.session_state.get("perf_qnh", 1013)
    dep_oat = st.session_state.get("perf_oat", 15)
    dep_wind = st.session_state.get("perf_headwind", 0)
    dep_alt = st.session_state.get("perf_runway_alt", 538)
    total_mass = _total_mass()

    # Conditions ARRIVEE — depuis METAR si dispo
    arr_metar = st.session_state.get("metar_arr", "")
    arr_parsed = parse_metar_full(arr_metar)
    arr_icao = st.session_state.get("arrivee", "")
    arr_ad = get_airport(arr_icao)
    arr_alt = arr_ad["elevation_ft"] if arr_ad else dep_alt
    arr_qnh = arr_parsed["qnh"] or dep_qnh
    arr_oat = arr_parsed["temp"] if arr_parsed["temp"] is not None else dep_oat
    # Composante vent à l'arrivée : si METAR + piste arrival connue
    arr_wind = dep_wind  # fallback
    if arr_parsed["wind"] and arr_parsed["wind"].get("dir") is not None and arr_ad:
        # Choisir piste face au vent
        from .airports import best_runway_for_wind
        rwy = best_runway_for_wind(arr_icao, arr_parsed["wind"]["dir"])
        if rwy:
            comp = wind_components(arr_parsed["wind"]["dir"],
                                    arr_parsed["wind"]["speed"],
                                    rwy["true_heading"])
            arr_wind = int(round(comp["headwind"]))
    # Masse à l'arrivée = ZFM + fuel restant (ce qu'on a déjà calculé en M&B)
    duree = st.session_state.get("duree_vol_h", 1.0)
    conso = st.session_state.get("conso_lh", 20.0)
    fuel_consumed_kg = duree * conso * 0.72
    fuel_taxi_kg = 5 * 0.72
    arr_mass = max(0, total_mass - fuel_consumed_kg - fuel_taxi_kg)

    # Conditions DEGAGEMENT 1 — depuis METAR si dispo
    deg_metar = st.session_state.get("metar_deg", "")
    deg_parsed = parse_metar_full(deg_metar)
    deg_list = [d.strip().upper() for d in
                (st.session_state.get("degagements") or "").split(",") if d.strip()]
    deg_icao = deg_list[0] if deg_list else ""
    deg_ad = get_airport(deg_icao)
    deg_alt = deg_ad["elevation_ft"] if deg_ad else dep_alt
    deg_qnh = deg_parsed["qnh"] or dep_qnh
    deg_oat = deg_parsed["temp"] if deg_parsed["temp"] is not None else dep_oat
    deg_wind = arr_wind  # fallback
    if deg_parsed["wind"] and deg_parsed["wind"].get("dir") is not None and deg_ad:
        from .airports import best_runway_for_wind
        rwy = best_runway_for_wind(deg_icao, deg_parsed["wind"]["dir"])
        if rwy:
            comp = wind_components(deg_parsed["wind"]["dir"],
                                    deg_parsed["wind"]["speed"],
                                    rwy["true_heading"])
            deg_wind = int(round(comp["headwind"]))
    deroutement_kg = (st.session_state.get("deroutement_min", 0) / 60) * conso * 0.72
    deg_mass = max(0, arr_mass - deroutement_kg)

    # === Conditions du jour (les 3 colonnes) ===
    # X centres : DEPART=165, ARRIVEE=240, DEGAGEMENT=315
    cols = [
        (165, dep_wind, dep_qnh, dep_oat, total_mass),
        (240, arr_wind, arr_qnh, arr_oat, arr_mass),
        (315, deg_wind, deg_qnh, deg_oat, deg_mass),
    ]
    for x, w, q, t, m in cols:
        _t(c, x, 139, f"{w:+d} kt", size=8)
        _t(c, x, 162, f"{q} hPa", size=8)
        _t(c, x, 184, f"{t:.0f} °C", size=8)
        _t(c, x, 204, f"{m:.0f} kg", size=8)

    # === Performances DEPART (table principale) ===
    zp_dep = pressure_altitude(dep_alt, dep_qnh)
    to = takeoff_perf(zp_dep, dep_oat, grass=grass, slope_pct=slope, wind_kt=dep_wind)
    ld = landing_perf(zp_dep, dep_oat, grass=grass, slope_pct=slope, wet=wet, wind_kt=dep_wind)

    x_val = 255
    x_lim = 380

    _t(c, x_val, 259, f"{round(to['tor'])} m", size=8)
    _t(c, x_lim, 259, f"{tora}", size=8)

    _t(c, x_val, 281, f"{round(to['tod'])} m", size=8)
    _t(c, x_lim, 281, f"{tora}", size=8)

    _t(c, x_val, 305, f"{round(to['tor'])} m", size=8)
    _t(c, x_lim, 305, f"{tora}", size=8)

    _t(c, x_val, 331, f"{ROC_SL_MCP} ft/min", size=8)

    # ATTERRISSAGE — utilise conditions ARRIVEE (atterrissage = aéroport d'arrivée)
    zp_arr = pressure_altitude(arr_alt, arr_qnh)
    ld_arr = landing_perf(zp_arr, arr_oat, grass=grass, slope_pct=slope, wet=wet, wind_kt=arr_wind)
    arr_lda = (arr_ad["runways"][0]["lda"] if arr_ad and arr_ad["runways"] else lda)

    _t(c, x_val, 353, f"{round(ld_arr['ldd'])} m", size=8)
    _t(c, x_lim, 353, f"{arr_lda}", size=8)

    _t(c, x_val, 379, f"{round(ld_arr['ldr'])} m", size=8)

    _t(c, x_val, 403, f"{ROC_SL_FLAPS10_MTOP} ft/min", size=8)

    # Distance atterrissage volets UP — approximation = LDD × 1.4 (volets UP plus long)
    ldd_up = round(ld_arr['ldd'] * 1.4)
    _t(c, x_val, 433, f"{ldd_up} m", size=8)
    _t(c, x_lim, 433, f"{arr_lda}", size=8)

    # === Performances DEGAGEMENT(S) — section du bas ===
    # 3 colonnes pour 3 dégagements possibles
    # X centers approximatives : 290, 340, 390
    deg_cols_x = [285, 335, 385]
    for i, deg_ic in enumerate(deg_list[:3]):
        x_d = deg_cols_x[i]
        deg_ad_i = get_airport(deg_ic)
        if not deg_ad_i:
            continue
        deg_alt_i = deg_ad_i["elevation_ft"]
        deg_lda_i = deg_ad_i["runways"][0]["lda"] if deg_ad_i["runways"] else 1100
        # Conditions : utilise METAR du 1er dégagement pour tous (simplification)
        zp_deg = pressure_altitude(deg_alt_i, deg_qnh)
        ld_deg = landing_perf(zp_deg, deg_oat, grass=grass, slope_pct=slope,
                              wet=wet, wind_kt=deg_wind)
        # Lignes dégagement (similaire à atterrissage section)
        _t(c, x_d, 460, f"{round(ld_deg['ldd'])}", size=7)   # LDD 15m volets LDG
        _t(c, x_d, 488, f"{round(ld_deg['ldr'])}", size=7)   # LDR
        _t(c, x_d, 516, f"{ROC_SL_FLAPS10_MTOP}", size=7)    # Taux montée API
        _t(c, x_d, 545, f"{round(ld_deg['ldd'] * 1.4)}", size=7)  # Volets UP

    # Limites LDA pour dégagement (3 valeurs)
    if deg_list:
        for i, deg_ic in enumerate(deg_list[:3]):
            deg_ad_i = get_airport(deg_ic)
            if deg_ad_i and deg_ad_i["runways"]:
                lda_d = deg_ad_i["runways"][0]["lda"]
                # Limite LDA pour LDD: même ligne y=460
                _t(c, x_lim, 460, f"{lda_d}", size=7) if i == 0 else None
                _t(c, x_lim, 545, f"{lda_d}", size=7) if i == 0 else None


def _draw_page_9_carburant(c):
    """Page 9 — Tableau carburant ACAF. Coordonnées calibrées via grille.

    Colonne "Qté carburant L" : x ≈ 365 (centre cellule)
    Lignes (y_from_top calibrés) :
      188 - Roulage (forfait 5 L)
      220 - Carburant pour le vol
      252 - Tout carburant supplémentaire désiré
      285 - De jour A→A terrain en vue (10 min)
      314 - Tout autre vol de jour (30 min)
      343 - De nuit (45 min)
      370 - De A vers B / plan de repli
      396 - Réserve ACAF
      423 - TOTAL
    """
    plan = fuel_planning(
        duree_h=st.session_state.get("duree_vol_h", 1.0),
        conso_lh=st.session_state.get("conso_lh", 20.0),
        regime=st.session_state.get("regime_vol", "VFR Jour (30 min)"),
        deroutement_min=st.session_state.get("deroutement_min", 0),
        reserve_acaf_min=st.session_state.get("reserve_acaf_min", 30),
    )

    x_val = 365   # colonne "Qté carburant L"

    # Roulage (forfait 5 L)
    _t(c, x_val, 180, "5", size=9)

    # Carburant pour le vol (croisière + procédure approche)
    fuel_vol = plan["flight_L"] + 7  # vol + 7L procédure
    _t(c, x_val, 200, f"{fuel_vol:.1f}", size=9)

    # Tout carburant supplémentaire désiré → on laisse vide (y=225)

    # Réserve réglementaire selon régime
    regime = st.session_state.get("regime_vol", "")
    reserve_l = plan["reserve_reg_L"]
    if "10 min" in regime or "A→A" in regime:
        _t(c, x_val, 250, f"{reserve_l:.1f}", size=9)
    elif "Nuit" in regime:
        _t(c, x_val, 305, f"{reserve_l:.1f}", size=9)
    else:  # 30 min jour par défaut
        _t(c, x_val, 277, f"{reserve_l:.1f}", size=9)

    # Plan de repli (déroutement)
    if st.session_state.get("deroutement_min", 0) > 0:
        derout_L = (st.session_state.get("deroutement_min", 0) / 60
                    * st.session_state.get("conso_lh", 20))
        _t(c, x_val, 330, f"{derout_L:.1f}", size=9)

    # Réserve ACAF
    _t(c, x_val, 357, f"{plan['reserve_acaf_L']:.1f}", size=9)

    # TOTAL
    _t(c, x_val, 383, f"{plan['total_min_L']:.1f}", size=10, bold=True)


def _draw_page_10_mb(c):
    """Page 10 — Masse & Centrage. Coordonnées calibrées via grille.

    ⚠️ Le template ACAF est conçu pour AT3 — les bras de levier pré-imprimés
    (0.600, 1.125, -0.257) ne correspondent PAS au B23 (2.085, 2.520, 1.600).
    On écrit les MASSES + MOMENTS calculés avec les bras B23 corrects, et on
    écrit aussi les bras B23 par-dessus pour cohérence.
    """
    from .data import ARMS

    wb = wb_calc(
        aircraft_id=st.session_state.get("avion", "F-HBTI"),
        pilot_kg=st.session_state.get("pilote_kg", 0),
        pax_kg=st.session_state.get("pax_kg", 0),
        rear_bag_kg=st.session_state.get("bagages_arriere_kg", 0),
        wing_l_kg=st.session_state.get("bagages_aile_g_kg", 0),
        wing_r_kg=st.session_state.get("bagages_aile_d_kg", 0),
        fuel_L=st.session_state.get("carburant_bord_L", 60),
        fuel_type=st.session_state.get("fuel_type", "AVGAS 100LL"),
    )
    info = AIRCRAFT[st.session_state.get("avion", "F-HBTI")]
    occ = st.session_state.get("pilote_kg", 0) + st.session_state.get("pax_kg", 0)
    bag = (st.session_state.get("bagages_arriere_kg", 0)
           + st.session_state.get("bagages_aile_g_kg", 0)
           + st.session_state.get("bagages_aile_d_kg", 0))
    zfm = wb["total_mass"] - wb["fuel_kg"]
    zfm_moment = wb["total_moment"] - wb["fuel_kg"] * ARMS["fuel"]
    bag_arm = ARMS["rear"] if st.session_state.get("bagages_arriere_kg", 0) >= bag else ARMS["wing"]

    # === Header masse en haut ===
    _t(c, 220, 134, f"{zfm:.1f} kg", size=9)        # Masse sans carburant
    _t(c, 220, 158, f"{wb['total_mass']:.1f} kg", size=9)  # Masse au décollage
    _t(c, 360, 158, f"{MTOW} kg", size=9)            # MMSD
    duree = st.session_state.get("duree_vol_h", 1.0)
    conso = st.session_state.get("conso_lh", 20.0)
    fuel_rest_kg = max(0, wb["fuel_kg"] - duree * conso * 0.72)
    landing_mass = zfm + fuel_rest_kg
    _t(c, 220, 178, f"{landing_mass:.1f} kg", size=9)  # Masse à l'atterrissage
    _t(c, 360, 178, f"{MTOW} kg", size=9)              # MMSA

    # === Tableau Masse / Bras / Moment (centres calibrés via grille) ===
    x_mass = 192
    x_arm = 271
    x_moment = 350

    rows = [
        # (y, masse, bras, moment) — Y values calibrés via grille fine
        (226, info["mass"],     info["arm"],   info["mass"] * info["arm"]),  # Avion à vide
        (245, occ,              ARMS["front"], occ * ARMS["front"]),         # Equipage
        (266, bag,              bag_arm,       bag * bag_arm),               # Bagages
        (286, zfm,              None,          zfm_moment),                  # Total sans carburant
        (306, wb["fuel_kg"],    ARMS["fuel"],  wb["fuel_kg"] * ARMS["fuel"]), # Carburant
        (327, wb["total_mass"], None,          wb["total_moment"]),          # Total au décollage
        (346, fuel_rest_kg,     ARMS["fuel"],  fuel_rest_kg * ARMS["fuel"]), # Carburant restant
        (366, landing_mass,     None,          zfm_moment + fuel_rest_kg * ARMS["fuel"]),  # Total atterrissage
    ]
    # Masque blanc sur les bras pré-imprimés AT3 dans la colonne "Bras de levier"
    # (cellules x=246-302, y=235-380 environ) avant d'écrire les bras B23 corrects
    c.setFillColor(white)
    c.rect(246, PAGE_H - 380, 56, 145, fill=1, stroke=0)
    c.setFillColor(black)

    for y, mass, arm, moment in rows:
        if mass is not None:
            _t(c, x_mass, y, f"{mass:.1f}", size=8)
        if arm is not None:
            _t(c, x_arm, y, f"{arm:.3f}", size=8)
        if moment is not None:
            _t(c, x_moment, y, f"{moment:.1f}", size=8)

    # === Remplacer le graphique AT3 par celui du B23 ===
    # Masque blanc large pour couvrir AT3 chart + labels périphériques
    c.setFillColor(white)
    c.rect(40, PAGE_H - 580, 380, 215, fill=1, stroke=0)  # x=40-420, y=365-580
    c.setFillColor(black)

    # Insertion du graphique B23 — taille adaptée
    try:
        chart_buf = _generate_wb_envelope_image(wb["cg"], wb["total_mass"])
        chart_img = ImageReader(chart_buf)
        # Position centrée : x=50, y=PAGE_H-555, width=320, height=180
        c.drawImage(chart_img, 50, PAGE_H - 555,
                    width=320, height=180,
                    preserveAspectRatio=True, mask='auto')
    except Exception as e:
        _t(c, 100, 470, f"(Graphique B23 indisponible : {e})", size=8, color=gray)


def _draw_page_11_equip_radio(c):
    """Page 11 — Équipements + Procédures panne radio."""
    # Cases équipements (x ≈ 130, 5 lignes y)
    equip_y = [180, 205, 228, 250, 273]
    equip_keys = ["equip_lampe", "equip_trousse", "equip_extincteur",
                  "equip_balise", "equip_gilets"]
    for y, k in zip(equip_y, equip_keys):
        _check(c, 130, y, bool(st.session_state.get(k, False)))

    # Procédures panne radio (4 zones)
    radio_y = [360, 460, 555, 650]
    radio_keys = ["panne_radio_depart", "panne_radio_route",
                  "panne_radio_arrivee", "panne_radio_degagement"]
    for y, k in zip(radio_y, radio_keys):
        _t_multiline(c, 100, y, st.session_state.get(k, ""),
                     size=8, line_h=10, max_width=380, max_lines=3)


def _draw_page_12_divers(c):
    """Page 12 — Plan vol, Douanes, ATC, Parking, Consignes, Sûreté."""
    # Notes en marge à côté de chaque section (positions approximatives)
    sections = [
        # (y_from_top, key)
        (210, "douanes_notes"),
        (310, "atc_hors_horaires_notes"),
        (385, "parking_notes"),
        (470, "consignes_ad_notes"),
        (590, "surete_notes"),
    ]
    for y, k in sections:
        _t_multiline(c, 35, y, st.session_state.get(k, ""),
                     size=8, line_h=10, max_width=370, max_lines=3)


# ============================================================
# HELPERS DE STATUT
# ============================================================

def _has(v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return bool(v)


def _has_mel() -> bool:
    return any(any(_has(v) for v in r.values())
               for r in st.session_state.get("mel_items", []))


def _has_branches() -> bool:
    branches = st.session_state.get("branches", [])
    return any(b.get("De") or b.get("Vers") or float(b.get("Dist (NM)") or 0) > 0
               for b in branches)


def _all_equip() -> bool:
    return all(st.session_state.get(k, False)
               for k in ["equip_lampe", "equip_trousse", "equip_extincteur",
                         "equip_balise", "equip_gilets"])


def _has_panne_radio() -> bool:
    return any(_has(st.session_state.get(k, ""))
               for k in ["panne_radio_depart", "panne_radio_route",
                         "panne_radio_arrivee", "panne_radio_degagement"])


def _total_mass() -> float:
    wb = wb_calc(
        aircraft_id=st.session_state.get("avion", "F-HBTI"),
        pilot_kg=st.session_state.get("pilote_kg", 0),
        pax_kg=st.session_state.get("pax_kg", 0),
        rear_bag_kg=st.session_state.get("bagages_arriere_kg", 0),
        wing_l_kg=st.session_state.get("bagages_aile_g_kg", 0),
        wing_r_kg=st.session_state.get("bagages_aile_d_kg", 0),
        fuel_L=st.session_state.get("carburant_bord_L", 60),
        fuel_type=st.session_state.get("fuel_type", "AVGAS 100LL"),
    )
    return wb["total_mass"]


# ============================================================
# ORCHESTRATION
# ============================================================

# Mapping page (0-based) → fonction de dessin
# On ne remplit QUE les pages critiques (cover + perfs + carbu + M&B).
# Les autres restent vierges — l'utilisateur les remplit à la main.
PAGE_DRAWERS = {
    0:  _draw_page_1_cover,       # Page 1 — Cover
    7:  _draw_page_8_perfs,       # Page 8 — Performances
    8:  _draw_page_9_carburant,   # Page 9 — Carburant
    9:  _draw_page_10_mb,         # Page 10 — Masse & Centrage
}


def fill_acaf_template() -> bytes:
    """
    Charge le template ACAF, dessine les overlays sur chaque page,
    retourne le PDF résultant en bytes.
    """
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template introuvable : {TEMPLATE_PATH}")

    reader = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if i in PAGE_DRAWERS:
            try:
                # Créer overlay
                buf = BytesIO()
                c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
                PAGE_DRAWERS[i](c)
                c.showPage()
                c.save()
                buf.seek(0)
                overlay_reader = PdfReader(buf)
                overlay_page = overlay_reader.pages[0]
                page.merge_page(overlay_page)
            except Exception as e:
                # Ne pas faire planter tout le PDF si une page rate
                # On annote l'erreur sur la page
                buf = BytesIO()
                c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
                _t(c, 35, 50, f"⚠️ Erreur overlay page {i+1} : {e}", size=8, color=(0.6, 0, 0))
                c.showPage()
                c.save()
                buf.seek(0)
                page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out.getvalue()
