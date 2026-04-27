"""Fonctions de calcul partagées."""
import math
import numpy as np
from matplotlib.path import Path
from .data import (
    AIRCRAFT, ARMS, DENSITY, ENVELOPE, MTOW,
    TO_GROUND_ROLL, TO_15M_DIST, LDG_GROUND_ROLL, LDG_15M_DIST,
    PERF_ALTS, PERF_ISA_DEV,
    TO_GRASS, TO_UPHILL_PER_PERCENT, TO_DOWNHILL_PER_PERCENT,
    TO_HEADWIND_PER_5KT, TO_TAILWIND_PER_5KT,
    LDG_GRASS, LDG_UPHILL_PER_PERCENT, LDG_DOWNHILL_PER_PERCENT,
    LDG_WET, LDG_HEADWIND_PER_5KT, LDG_TAILWIND_PER_5KT,
)


def isa_temp_at_altitude(alt_ft: float) -> float:
    """Température ISA à une altitude donnée (°C)."""
    return 15 - 2 * (alt_ft / 1000)


def isa_deviation(oat_c: float, alt_ft: float) -> float:
    """Écart ISA en °C."""
    return oat_c - isa_temp_at_altitude(alt_ft)


def pressure_altitude(field_alt_ft: float, qnh_hpa: float) -> float:
    """Altitude pression à partir d'altitude terrain et QNH."""
    return field_alt_ft + (1013 - qnh_hpa) * 28


def wb_calc(aircraft_id: str, pilot_kg: float, pax_kg: float,
            rear_bag_kg: float, wing_l_kg: float, wing_r_kg: float,
            fuel_L: float, fuel_type: str):
    """Calcul masse & centrage. Retourne dict complet."""
    info = AIRCRAFT[aircraft_id]
    fuel_kg = fuel_L * DENSITY[fuel_type]
    occ = pilot_kg + pax_kg
    wings = wing_l_kg + wing_r_kg

    rows = [
        ("Avion à vide",      info["mass"], info["arm"]),
        ("Pilote + Passager", occ,          ARMS["front"]),
        ("Bagages ailes",     wings,        ARMS["wing"]),
        ("Bagages arrière",   rear_bag_kg,  ARMS["rear"]),
        ("Carburant",         fuel_kg,      ARMS["fuel"]),
    ]
    detailed = [(n, m, a, m * a) for (n, m, a) in rows]
    total_m = sum(r[1] for r in detailed)
    total_mom = sum(r[3] for r in detailed)
    cg = total_mom / total_m if total_m > 0 else 0
    in_env = Path(ENVELOPE).contains_point((cg, total_m))
    return {
        "rows": detailed,
        "total_mass": total_m,
        "total_moment": total_mom,
        "cg": cg,
        "in_envelope": in_env,
        "fuel_kg": fuel_kg,
    }


def bilinear_interp(value_x, value_y, x_arr, y_arr, table):
    """
    Interpolation bilinéaire dans une table 2D.
    x_arr indexe les LIGNES (ex: altitudes), y_arr les COLONNES (ex: ISA dev).
    """
    value_x = float(np.clip(value_x, x_arr[0], x_arr[-1]))
    value_y = float(np.clip(value_y, y_arr[0], y_arr[-1]))

    i = 0
    for k in range(len(x_arr) - 1):
        if x_arr[k] <= value_x <= x_arr[k + 1]:
            i = k
            break
    j = 0
    for k in range(len(y_arr) - 1):
        if y_arr[k] <= value_y <= y_arr[k + 1]:
            j = k
            break

    fx = (value_x - x_arr[i]) / (x_arr[i + 1] - x_arr[i]) if x_arr[i + 1] != x_arr[i] else 0
    fy = (value_y - y_arr[j]) / (y_arr[j + 1] - y_arr[j]) if y_arr[j + 1] != y_arr[j] else 0

    v00 = table[i, j]
    v01 = table[i, j + 1]
    v10 = table[i + 1, j]
    v11 = table[i + 1, j + 1]
    return (1 - fx) * (1 - fy) * v00 + (1 - fx) * fy * v01 + \
           fx * (1 - fy) * v10 + fx * fy * v11


def takeoff_perf(zp_ft: float, oat_c: float,
                 grass: bool = False, slope_pct: float = 0.0,
                 wind_kt: float = 0.0):
    """Calcule TOR et TOD avec corrections. wind_kt > 0 = face, < 0 = arrière."""
    isa_dev = isa_deviation(oat_c, zp_ft)
    base_tor = bilinear_interp(zp_ft, isa_dev, PERF_ALTS, PERF_ISA_DEV, TO_GROUND_ROLL)
    base_tod = bilinear_interp(zp_ft, isa_dev, PERF_ALTS, PERF_ISA_DEV, TO_15M_DIST)

    factor = 1.0
    if grass:
        factor *= TO_GRASS
    # Pente : correction LINÉAIRE par % (manuel : "+5% par 1%")
    if slope_pct > 0:
        factor *= 1 + (TO_UPHILL_PER_PERCENT - 1) * slope_pct
    elif slope_pct < 0:
        factor *= 1 + (TO_DOWNHILL_PER_PERCENT - 1) * abs(slope_pct)
    # Vent : correction linéaire par tranche de 5 kt, mais clampée pour éviter
    # un facteur négatif (vent face très fort → distance qui s'inverserait)
    if wind_kt > 0:
        factor *= max(0.1, 1 + TO_HEADWIND_PER_5KT * (wind_kt / 5))
    elif wind_kt < 0:
        factor *= 1 + TO_TAILWIND_PER_5KT * (abs(wind_kt) / 5)

    return {
        "isa_dev": isa_dev,
        "tor_base": base_tor,
        "tod_base": base_tod,
        "factor": factor,
        "tor": base_tor * factor,
        "tod": base_tod * factor,
    }


def landing_perf(zp_ft: float, oat_c: float,
                 grass: bool = False, slope_pct: float = 0.0,
                 wet: bool = False, wind_kt: float = 0.0):
    """Calcule LDR et LDD avec corrections."""
    isa_dev = isa_deviation(oat_c, zp_ft)
    base_ldr = bilinear_interp(zp_ft, isa_dev, PERF_ALTS, PERF_ISA_DEV, LDG_GROUND_ROLL)
    base_ldd = bilinear_interp(zp_ft, isa_dev, PERF_ALTS, PERF_ISA_DEV, LDG_15M_DIST)

    factor = 1.0
    if grass:
        factor *= LDG_GRASS
    if wet:
        factor *= LDG_WET
    # Pente : correction LINÉAIRE
    if slope_pct > 0:
        factor *= 1 + (LDG_UPHILL_PER_PERCENT - 1) * slope_pct
    elif slope_pct < 0:
        factor *= 1 + (LDG_DOWNHILL_PER_PERCENT - 1) * abs(slope_pct)
    # Vent : linéaire, clamp anti-négatif
    if wind_kt > 0:
        factor *= max(0.1, 1 + LDG_HEADWIND_PER_5KT * (wind_kt / 5))
    elif wind_kt < 0:
        factor *= 1 + LDG_TAILWIND_PER_5KT * (abs(wind_kt) / 5)

    return {
        "isa_dev": isa_dev,
        "ldr_base": base_ldr,
        "ldd_base": base_ldd,
        "factor": factor,
        "ldr": base_ldr * factor,
        "ldd": base_ldd * factor,
    }


def wind_triangle(true_track_deg: float, tas_kt: float,
                  wind_dir_deg: float, wind_speed_kt: float):
    """
    Calcul du triangle des vents.
    Convention météo : wind_dir = direction d'où vient le vent.
    Retourne : {wca, true_heading, ground_speed, headwind, crosswind}
    """
    angle_rad = math.radians(wind_dir_deg - true_track_deg)
    crosswind = wind_speed_kt * math.sin(angle_rad)
    headwind = wind_speed_kt * math.cos(angle_rad)
    if tas_kt <= 0:
        return {"wca": 0, "th": true_track_deg, "gs": 0, "headwind": headwind, "crosswind": crosswind}
    sin_wca = max(-1.0, min(1.0, crosswind / tas_kt))
    wca = math.degrees(math.asin(sin_wca))
    th = (true_track_deg + wca) % 360
    gs = tas_kt * math.cos(math.radians(wca)) - headwind
    return {
        "wca": wca,
        "th": th,
        "gs": max(0, gs),
        "headwind": headwind,
        "crosswind": crosswind,
    }


def magnetic_heading(true_heading_deg: float, magnetic_variation_deg: float) -> float:
    """
    MH = TH - variation (variation est positive E, négative W).
    Convention : "Variation East — Magnetic Least"
    """
    return (true_heading_deg - magnetic_variation_deg) % 360


def fuel_planning(duree_h: float, conso_lh: float, regime: str,
                  deroutement_min: float = 0, reserve_acaf_min: float = 30,
                  taxi_L: float = 5, approach_L: float = 7):
    """
    Calcule le carburant minimum requis.
    regime : "VFR Jour A→A (10 min)" / "VFR Jour (30 min)" / "VFR Nuit (45 min)"
    Retourne dict avec breakdown.
    """
    if "Jour A" in regime or "10 min" in regime:
        reg_min = 10
    elif "Nuit" in regime:
        reg_min = 45
    else:
        reg_min = 30

    flight_L = duree_h * conso_lh
    deroutement_L = (deroutement_min / 60) * conso_lh
    reserve_reg_L = (reg_min / 60) * conso_lh
    reserve_acaf_L = (reserve_acaf_min / 60) * conso_lh

    lines = [
        ("Démarrage + Roulage + Décollage", taxi_L, "Forfait QRH"),
        ("Vol prévu (croisière)", round(flight_L, 1), f"{duree_h} h × {conso_lh} L/h"),
        ("Procédure + Atterrissage", approach_L, "Forfait QRH"),
    ]
    if deroutement_L > 0:
        lines.append(("Déroutement", round(deroutement_L, 1), f"{deroutement_min} min × {conso_lh} L/h"))
    lines.append((f"Réserve réglementaire ({reg_min} min)", round(reserve_reg_L, 1), "Part-NCO.OP.125"))
    lines.append((f"Réserve ACAF ({reserve_acaf_min} min)", round(reserve_acaf_L, 1), "Marge club"))

    total = round(sum(l[1] for l in lines), 1)
    return {
        "lines": lines,
        "total_min_L": total,
        "regulatory_min": reg_min,
        "reserve_reg_L": round(reserve_reg_L, 1),
        "reserve_acaf_L": round(reserve_acaf_L, 1),
        "flight_L": round(flight_L, 1),
    }
