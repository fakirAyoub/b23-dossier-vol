# CLAUDE.md — Projet B23 Dossier de Vol

> Mémoire projet pour Claude Code. À lire en début de chaque nouvelle session.

## 🎯 Contexte

Application Streamlit qui prépare un **dossier de vol complet** pour le **Bristell B23 (F-HBTI / F-HRDV)** de l'**Aéroclub Air France à Toussus le Noble (LFPN)**.

L'utilisateur (Ayoub Fakir) prépare son **PPL**. Le test pratique est ce **samedi 2 mai 2026**.

L'app est déployée sur Render → https://aero.fakir.dev

GitHub : https://github.com/fakirAyoub/b23-dossier-vol (compte `fakirAyoub`)

## 📁 Structure du projet

```
B23/
├── Accueil.py                    # Point d'entrée Streamlit (page d'accueil)
├── Procfile                      # web: streamlit run Accueil.py …
├── requirements.txt              # streamlit, pandas, matplotlib, fpdf2,
│                                 # requests, pypdf, reportlab
├── README.md
├── lib/
│   ├── airports.py               # DB des aérodromes français (LFPN, LFOX, …)
│   ├── calc.py                   # Calculs purs (W&B, perfs TO/LDG, vent, fuel)
│   ├── data.py                   # Constantes B23 + tables de performance
│   ├── dossier_io.py             # Save/Load JSON du dossier
│   ├── meteo.py                  # API METAR/TAF (aviationweather.gov)
│   ├── pdf_template.py           # Génère le PDF en remplissant le template ACAF
│   ├── state.py                  # session_state init + persistance multipage
│   └── wind.py                   # Parser METAR + composantes vent piste
├── pages/
│   ├── 1_🛠️_État_avion.py       # MEL
│   ├── 2_🌤️_Météo.py            # METAR/TAF auto + WINTEM + conditions
│   ├── 3_📜_NOTAM.py            # Saisie 4 zones + checkbox vol réalisable
│   ├── 4_🧭_Journal_de_navigation.py  # Branches + triangle des vents
│   ├── 5_📈_Performances.py     # Auto-fill aérodrome + calc TO/LDG
│   ├── 6_⛽_Carburant.py        # NCO.OP.125 + ACAF 30 min + déroutement
│   ├── 7_⚖️_Masse_et_centrage.py # W&B + enveloppe matplotlib
│   ├── 8_📋_Checklists.py       # Équipements + panne radio + divers
│   └── 9_📄_Export_PDF.py       # Bouton génère + télécharge PDF ACAF
├── templates/
│   └── Dossier-vol-ACAF.pdf      # Template officiel ACAF (12 pages)
└── (PDFs sources, gitignored)
    ├── Manuel-vol-13_04_2022.pdf       # Manuel B23 BRM Aero, rev. B
    └── QRH B23 F-HBTI F-HRDV- v1.0 - 21 Mars 2026.pdf  # QRH club
```

## 🛩️ Données B23 critiques

### Masses à vide (QRH p.11, Ed. 1.0 du 21/03/2026)
- **F-HBTI** : 452,5 kg @ bras 1,718 m → moment 777,4 kg.m
- **F-HRDV** : 458 kg @ bras 1,713 m → moment 785,5 kg.m
- ⚠️ À mettre à jour si nouvelle pesée

### Bras de levier (m, depuis plan hélice)
- Sièges avant : **2,085**
- Bagages ailes (max 20 kg/aile) : **2,025**
- Bagages arrière (max 15 kg) : **2,520**
- Carburant utilisable : **1,600**

### Limitations (QRH p.6)
- MTOW = MLW = **750 kg**
- Max sans charge ailes (Zero Wing Load) : **660 kg**
- Carburant utilisable : **2 × 59 = 118 L** total
- VFE 82 / VA 99 / VNO 136 / VNE 157 KIAS
- VS0 (atter) 44 / VS (volets 0) 51 KIAS

### Performances de référence (Manuel § 5.2.3)
- **Vy** = 74 KIAS, ROC SL MCP = **688 ft/min**
- **Vx** = 62 KIAS
- ROC SL MTOP (5 min max) = 702 ft/min
- ROC SL Flaps 10° MTOP (balked landing) = **634 ft/min**
- V_glide = 67 KIAS, finesse 8.5

### Tables performances (Manuel § 5.2.4 et 5.2.5, MTOW)
Tables 4×5 (altitude × ISA dev) intégrées dans `lib/data.py` :
- TO Ground Roll / TO 15m / LDG Ground Roll / LDG 15m
- Coefficients : herbe TO ×1,14 / herbe LDG ×1,18 / mouillé LDG ×1,15
- Pente : ±5%/1% / Vent face TO −15%/5kt, LDG −5%/5kt / arrière TO +20%/5kt, LDG +10%/5kt

### Forfaits carburant (QRH p.9)
- Démarrage + roulage + décollage : **5 L**
- Procédure intégration + atterrissage : **7 L**
- Réserves : VFR Jour A→A 10 min · VFR Jour 30 min · VFR Nuit 45 min
- **Réserve ACAF : 30 min** (au-dessus du réglementaire) — pas 15 min

## 🧮 Calculs clés

### Masse à l'arrivée / dégagement (`lib/pdf_template.py`)
```
masse_arrivée    = TOW − 5 L taxi − (durée × conso)        × 0,72 (densité AVGAS)
masse_dégagement = masse_arrivée − (déroutement_min/60 × conso) × 0,72
```
Conservateur : on ne déduit pas les 7 L procédure pour le calcul perf LDG.

### ISA et altitude pression
```
ISA(alt_ft)   = 15 − 2 × alt_ft / 1000
ΔISA          = OAT − ISA(Zp)
Zp            = altitude_terrain + (1013 − QNH) × 28
```

### Triangle des vents (`lib/calc.py`)
- Convention : WD = direction d'où vient le vent
- WCA = arcsin(crosswind / TAS)
- TH = TT + WCA
- GS = TAS × cos(WCA) − headwind

### Composante vent sur piste (`lib/wind.py`)
- headwind = WS × cos(WD − rwy_heading)
- crosswind = WS × sin(WD − rwy_heading)

## 🌐 Déploiement

### Render
- Service : `b23-dossier-vol` sur dashboard.render.com
- Start command (configurée dans Settings > Build & Deploy) :
  `streamlit run Accueil.py --server.port=$PORT --server.address=0.0.0.0`
- Procfile dans le repo override la commande dashboard
- Custom domain : `aero.fakir.dev` (CNAME chez Namecheap)
- Auto-deploy : à chaque push sur `main`

### GitHub Workflow
```bash
cd ~/Desktop/B23
git add -A
git commit -m "..."
git push origin main
# → Render redeploy automatique en ~2 min
```

## 🔧 Particularités techniques

### Persistance state multipage
Streamlit nettoie les widget keys quand on quitte une page. Workaround dans `lib/state.py:init_state()` :
```python
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v
    else:
        st.session_state[k] = st.session_state[k]  # ← le "touch"
```

### PDF Template ACAF
Le template `templates/Dossier-vol-ACAF.pdf` (12 pages) est rempli par overlay :
- `pypdf.PdfReader/Writer` pour merger
- `reportlab.pdfgen.canvas` pour créer l'overlay PDF par page
- Coordonnées en pt depuis le HAUT (helper `_t(c, x, y_from_top, ...)`)
- Page A5 = 419,52 × 595,32 pt

Pages remplies par `PAGE_DRAWERS` :
- Page 1 (cover), 4 (météo), 8 (perfs), 9 (carburant), 10 (M&B + graphique B23)

Les autres pages restent vierges (le pilote les remplit à la main).

Page 10 (M&B) : masque blanc sur le graphique AT3 pré-imprimé + insertion du graphique B23 (matplotlib → PNG → drawImage).

### METAR/TAF API
- `https://aviationweather.gov/api/data/metar?ids=LFPN&format=raw&taf=false`
- `https://aviationweather.gov/api/data/taf?ids=LFPN&format=raw`
- Parser dans `lib/wind.py` : extrait wind/QNH/temp depuis le METAR
- Auto-remplit `qnh`, `oat`, `vent_dir`, `vent_kt`, `perf_qnh`, `perf_oat`

### Discord bridge (Mac local uniquement)
- Plugin Claude Code Discord activé sur ce Mac
- Listener custom dans `/tmp/discord-bot/listener.mjs` (fallback car le plugin natif n'établit pas le gateway WebSocket dans certains setups)
- Wrapper `/tmp/discord-bot/dm.sh "msg"` pour envoyer via REST API
- Bot : `Claude_Fincome` (ID 1485363173300375694)
- Channel DM : `1485408920368316437`
- Allowlist : `704560000022085673` (snowflake afakir)
- Policy : `allowlist` (verrouillée)

## 📋 État actuel des features (au 1er mai 2026)

### ✅ Fait
- Page d'accueil avec saisies persistantes
- Autocomplete OACI (texte libre + helper liste)
- 9 pages dossier complètes
- Calculs : W&B, perfs TO/LDG (tables manuel), fuel NCO+ACAF, triangle vents
- METAR/TAF auto + parser QNH/temp/vent
- WINTEM avec ΔISA calculé
- Save/Load dossier JSON
- Export PDF ACAF avec :
  - Cover (page 1)
  - Météo (page 4) : valeurs WINTEM à droite des bullets, METAR/TAF DEP+ARR
  - Performances (page 8) : DEPART + ARRIVEE + DEGAGEMENT + section dégagements (sans distances utilisables — gérées manuel)
  - Carburant (page 9)
  - M&B (page 10) : tableau B23 + graphique B23 (au lieu d'AT3)

### 🚧 À améliorer (si tokens dispo)
- Section DEGAGEMENT(S) page 8 : positionnements à affiner
- Persistance refresh navigateur (utiliser cookies/localStorage)
- Plus d'aérodromes dans `lib/airports.py`
- Page Performances : interface plus claire de la composante vent
- Améliorer mise en page page 10 graphique (résidu AT3 entre tableau et graphique)

## 🆘 Pour PPL — sujets à réviser

### Théorie B23 à connaître par cœur
- Vitesses (VFE/VA/VNO/VNE/VS0/VS/Vy/Vx/V_glide)
- Limitations moteur (RPM décollage 5800 max 5min, continu 5500)
- Procédures urgence (panne moteur, feu, panne radio)
- Performances de référence
- M&B : enveloppe + Max Zero Wing Load 660 kg

### Réglementation
- Espaces aériens (CTR LFPN, TMA Paris, etc.)
- AZBA — carte du jour
- Réserves VFR : 30 min jour, 45 min nuit + 30 min ACAF club
- Plan de vol (oui/non selon trajet)

### Météo
- Décodage METAR/TAF
- TEMSI / WINTEM
- Pression QNH/QFE/STD
- Critères go/no-go

### Procédures Toussus (LFPN)
- Pistes 07L/25R (1100 m dur) et 07R/25L (1051 m herbe)
- Cartes VAC à connaître
- Points de report habituels (NH, S, H, sortie de zone)
- Espaces : LFPN dans CTR Toussus + TMA Paris

## 📞 Contacts importants

- Aéroclub Air France Toussus
- Instructeur PPL : Christophe Cassedanne (auteur du dossier ACAF)
- Examinateur : à confirmer

---

**Dernière mise à jour : 1er mai 2026**
