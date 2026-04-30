"""Base de données des aérodromes courants région parisienne + dégagements habituels.

Pour chaque aérodrome :
- icao : code OACI
- name : nom usuel
- elevation_ft : altitude terrain (ft)
- runways : liste de pistes : ident, true_heading_deg, tora_m, lda_m, surface, slope_pct (par défaut 0)

Source : AIP France / cartes VAC SIA. Valeurs à vérifier avant chaque vol.
"""

AIRPORTS = {
    "LFPN": {
        "name": "Toussus le Noble",
        "elevation_ft": 538,
        "runways": [
            {"ident": "07L", "true_heading": 73,  "tora": 1100, "lda": 1100, "surface": "dur",   "slope": 0.0},
            {"ident": "25R", "true_heading": 253, "tora": 1100, "lda": 1100, "surface": "dur",   "slope": 0.0},
            {"ident": "07R", "true_heading": 73,  "tora": 1051, "lda": 1051, "surface": "herbe", "slope": 0.0},
            {"ident": "25L", "true_heading": 253, "tora": 1051, "lda": 1051, "surface": "herbe", "slope": 0.0},
        ],
    },
    "LFOX": {
        "name": "Étampes-Mondésir",
        "elevation_ft": 519,
        "runways": [
            {"ident": "10",  "true_heading": 100, "tora": 1100, "lda": 1100, "surface": "dur",   "slope": 0.0},
            {"ident": "28",  "true_heading": 280, "tora": 1100, "lda": 1100, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFPT": {
        "name": "Pontoise-Cormeilles",
        "elevation_ft": 325,
        "runways": [
            {"ident": "05",  "true_heading": 50,  "tora": 1690, "lda": 1690, "surface": "dur",   "slope": 0.0},
            {"ident": "23",  "true_heading": 230, "tora": 1690, "lda": 1690, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFPK": {
        "name": "Coulommiers-Voisins",
        "elevation_ft": 470,
        "runways": [
            {"ident": "08",  "true_heading": 80,  "tora": 1450, "lda": 1450, "surface": "dur",   "slope": 0.0},
            {"ident": "26",  "true_heading": 260, "tora": 1450, "lda": 1450, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFPL": {
        "name": "Lognes-Émerainville",
        "elevation_ft": 365,
        "runways": [
            {"ident": "08",  "true_heading": 80,  "tora": 760,  "lda": 760,  "surface": "dur",   "slope": 0.0},
            {"ident": "26",  "true_heading": 260, "tora": 760,  "lda": 760,  "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFFE": {
        "name": "La Ferté-Alais",
        "elevation_ft": 463,
        "runways": [
            {"ident": "10",  "true_heading": 100, "tora": 750,  "lda": 750,  "surface": "herbe", "slope": 0.0},
            {"ident": "28",  "true_heading": 280, "tora": 750,  "lda": 750,  "surface": "herbe", "slope": 0.0},
        ],
    },
    "LFPB": {
        "name": "Paris Le Bourget",
        "elevation_ft": 218,
        "runways": [
            {"ident": "07",  "true_heading": 70,  "tora": 3000, "lda": 3000, "surface": "dur",   "slope": 0.0},
            {"ident": "25",  "true_heading": 250, "tora": 3000, "lda": 3000, "surface": "dur",   "slope": 0.0},
            {"ident": "03",  "true_heading": 30,  "tora": 1845, "lda": 1845, "surface": "dur",   "slope": 0.0},
            {"ident": "21",  "true_heading": 210, "tora": 1845, "lda": 1845, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFOA": {
        "name": "Avord",
        "elevation_ft": 580,
        "runways": [
            {"ident": "08",  "true_heading": 80,  "tora": 2400, "lda": 2400, "surface": "dur",   "slope": 0.0},
            {"ident": "26",  "true_heading": 260, "tora": 2400, "lda": 2400, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFOI": {
        "name": "Abbeville",
        "elevation_ft": 217,
        "runways": [
            {"ident": "02",  "true_heading": 20,  "tora": 920,  "lda": 920,  "surface": "dur",   "slope": 0.0},
            {"ident": "20",  "true_heading": 200, "tora": 920,  "lda": 920,  "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFAQ": {
        "name": "Albert-Picardie",
        "elevation_ft": 364,
        "runways": [
            {"ident": "09",  "true_heading": 90,  "tora": 2300, "lda": 2300, "surface": "dur",   "slope": 0.0},
            {"ident": "27",  "true_heading": 270, "tora": 2300, "lda": 2300, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFAY": {
        "name": "Amiens-Glisy",
        "elevation_ft": 246,
        "runways": [
            {"ident": "12",  "true_heading": 120, "tora": 1600, "lda": 1600, "surface": "dur",   "slope": 0.0},
            {"ident": "30",  "true_heading": 300, "tora": 1600, "lda": 1600, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFOC": {
        "name": "Châteaudun",
        "elevation_ft": 433,
        "runways": [
            {"ident": "10",  "true_heading": 100, "tora": 2500, "lda": 2500, "surface": "dur",   "slope": 0.0},
            {"ident": "28",  "true_heading": 280, "tora": 2500, "lda": 2500, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFGS": {
        "name": "Saint-Cyr l'École",
        "elevation_ft": 372,
        "runways": [
            {"ident": "12",  "true_heading": 120, "tora": 940,  "lda": 940,  "surface": "dur",   "slope": 0.0},
            {"ident": "30",  "true_heading": 300, "tora": 940,  "lda": 940,  "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFAT": {
        "name": "Le Touquet",
        "elevation_ft": 36,
        "runways": [
            {"ident": "14",  "true_heading": 140, "tora": 1849, "lda": 1849, "surface": "dur",   "slope": 0.0},
            {"ident": "32",  "true_heading": 320, "tora": 1849, "lda": 1849, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFRD": {
        "name": "Dinard-Pleurtuit",
        "elevation_ft": 219,
        "runways": [
            {"ident": "17",  "true_heading": 170, "tora": 2150, "lda": 2150, "surface": "dur",   "slope": 0.0},
            {"ident": "35",  "true_heading": 350, "tora": 2150, "lda": 2150, "surface": "dur",   "slope": 0.0},
        ],
    },
    "LFAQ": {
        "name": "Albert-Picardie",
        "elevation_ft": 364,
        "runways": [
            {"ident": "09",  "true_heading": 90,  "tora": 2300, "lda": 2300, "surface": "dur",   "slope": 0.0},
        ],
    },
}


def search_icao(query: str) -> list:
    """Recherche fuzzy sur OACI ou nom. Retourne liste de codes triée."""
    q = (query or "").strip().upper()
    if not q:
        return list(AIRPORTS.keys())
    matches = []
    for icao, ad in AIRPORTS.items():
        score = 0
        if icao.startswith(q):
            score = 100
        elif q in icao:
            score = 50
        elif q.lower() in ad["name"].lower():
            score = 25
        if score:
            matches.append((score, icao))
    matches.sort(reverse=True)
    return [icao for _, icao in matches]


def get_airport(icao: str) -> dict | None:
    return AIRPORTS.get((icao or "").strip().upper())


def get_runway(icao: str, ident: str) -> dict | None:
    ad = get_airport(icao)
    if not ad:
        return None
    for rwy in ad["runways"]:
        if rwy["ident"].upper() == (ident or "").upper():
            return rwy
    return None


def best_runway_for_wind(icao: str, wind_dir_deg: float) -> dict | None:
    """
    Retourne la piste qui présente la meilleure composante de face pour
    le vent donné (direction d'où vient le vent).
    """
    ad = get_airport(icao)
    if not ad or not ad["runways"]:
        return None
    import math
    best, best_score = None, -1e9
    for rwy in ad["runways"]:
        # composante face = cos(WD - RWY_HDG). On veut cos > 0 et max.
        diff = math.radians(wind_dir_deg - rwy["true_heading"])
        comp = math.cos(diff)
        if comp > best_score:
            best_score = comp
            best = rwy
    return best
