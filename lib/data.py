"""Données B23 — Manuel de vol § 5/§ 6 + QRH."""
import numpy as np

AIRCRAFT = {
    "F-HBTI": {"mass": 452.5, "arm": 1.718, "moment": 777.4},
    "F-HRDV": {"mass": 458.0, "arm": 1.713, "moment": 785.5},
}

ARMS = {
    "front": 2.085,   # Sièges avant
    "wing":  2.025,   # Bagages dans les ailes
    "rear":  2.520,   # Bagages arrière
    "fuel":  1.600,   # Carburant
}

DENSITY = {"AVGAS 100LL": 0.72, "SP98": 0.75}

# Enveloppe Masse/Centrage (bras_m, masse_kg) — QRH p.11
ENVELOPE = [
    (1.712, 490), (1.808, 490), (1.840, 600),
    (1.840, 750), (1.792, 750), (1.712, 600),
]

# Forfaits carburant (QRH p.9)
TAXI_FUEL     = 5
APPROACH_FUEL = 7

# Réserves (Part-NCO.OP.125 + ACAF)
RESERVE_DAY_NCO   = 30  # min — VFR Jour
RESERVE_NIGHT_NCO = 45  # min — VFR Nuit
RESERVE_LOCAL     = 10  # min — VFR Jour A/A vers A avec terrain en vue
RESERVE_ACAF      = 30  # min — Marge supplémentaire ACAF (en plus de la réserve réglementaire)

# === TABLES PERFORMANCES (Manuel § 5.2.4 et 5.2.5, MTOW=750kg) ===
# Décollage — Distance roulement (m)
TO_GROUND_ROLL = np.array([
    [309, 335, 365, 396, 431],   # 0 ft
    [362, 396, 432, 475, 522],   # 2000 ft
    [431, 476, 526, 584, 652],   # 4000 ft
    [525, 587, 661, 747, 852],   # 6000 ft
])
# Décollage — Distance passage 15m (m)
TO_15M_DIST = np.array([
    [400, 438, 479, 523, 570],
    [470, 515, 562, 616, 675],
    [554, 610, 671, 739, 818],
    [663, 735, 818, 921, 1030],
])
# Atterrissage — Distance roulement (m)
LDG_GROUND_ROLL = np.array([
    [136, 141, 146, 151, 157],
    [146, 151, 157, 163, 169],
    [157, 163, 169, 175, 182],
    [169, 175, 182, 189, 196],
])
# Atterrissage — Distance passage 15m (m)
LDG_15M_DIST = np.array([
    [362, 376, 391, 405, 419],
    [389, 405, 420, 436, 451],
    [419, 436, 453, 469, 485],
    [452, 470, 488, 505, 523],
])
PERF_ALTS = [0, 2000, 4000, 6000]
PERF_ISA_DEV = [-20, -10, 0, 10, 20]

# Corrections décollage (manuel § 5.2.4)
TO_GRASS = 1.14
TO_UPHILL_PER_PERCENT = 1.05
TO_DOWNHILL_PER_PERCENT = 0.95
TO_HEADWIND_PER_5KT = -0.15
TO_TAILWIND_PER_5KT = +0.20

# Corrections atterrissage (manuel § 5.2.5)
LDG_GRASS = 1.18
LDG_UPHILL_PER_PERCENT = 0.95
LDG_DOWNHILL_PER_PERCENT = 1.05
LDG_WET = 1.15
LDG_HEADWIND_PER_5KT = -0.05
LDG_TAILWIND_PER_5KT = +0.10

# Performances de référence — manuel § 5.2.3
ROC_SL_MCP = 688           # ft/min, Vy=74kt, Flaps 0, MTOW
ROC_SL_MTOP = 702          # ft/min, MTOP (5min max)
ROC_SL_FLAPS10_MTOP = 634  # ft/min, MTOP, Flaps 10° (balked landing)
VY_KIAS = 74
VX_KIAS = 62
V_GLIDE_KIAS = 67

# Vitesses limites (QRH p.6)
VFE = 82
VA = 99
VNO = 136
VNE = 157
VS_FLAPS_0 = 51
VS_FLAPS_10 = 47
VS_FLAPS_25 = 44

# Capacités
FUEL_USABLE_MAX = 118  # L
MTOW = 750             # kg
MLW = 750
MAX_ZERO_WING = 660
