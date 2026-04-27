# ✈️ B23 — Dossier de Vol

Application web Streamlit pour préparer un dossier de vol complet sur **Bristell B23** (F-HBTI / F-HRDV) — Aéroclub Air France, Toussus le Noble.

## 🎯 Fonctionnalités

L'application reproduit les **9 sections** du dossier de vol ACAF :

1. **État avion (MEL)** — Liste des systèmes/équipements affectés
2. **Météo** — METAR/TAF récupérés automatiquement via aviationweather.gov + saisie TEMSI/WINTEM
3. **NOTAM** — Saisie par zone (départ, route, arrivée, dégagements)
4. **Journal de navigation** — Triangle des vents intégré (Rv → Cv → Cm + dérive + GS)
5. **Performances** — Distances décollage/atterrissage avec interpolation des tables manuel + corrections (herbe, mouillé, pente, vent)
6. **Carburant** — Plan complet : forfaits QRH + Part-NCO.OP.125 + réserve ACAF
7. **Masse & Centrage** — Calcul + enveloppe + vérification automatique des limites
8. **Checklists & Procédures** — Équipements de secours, panne radio, douanes, sûreté…
9. **Export PDF** — Génération d'un PDF complet au format ACAF

## 🚀 Lancer en local

```bash
pip install -r requirements.txt
streamlit run b23_wb.py
```

Puis ouvre [http://localhost:8501](http://localhost:8501).

## 📚 Sources

- Manuel de vol B23 (ADXC-73-001-AFM, rev. B, 13/04/2022)
- QRH B23 F-HBTI / F-HRDV v1.0 (21/03/2026)
- Part-NCO.OP.125 (réserve carburant VFR)
- Format dossier de vol ACAF

## ⚠️ Avertissement

Cette application est un **outil d'aide à la préparation** uniquement. Les calculs sont basés sur le manuel de vol mais **ne se substituent pas** au manuel certifié, à la QRH et au jugement du pilote/instructeur. Toujours vérifier les valeurs critiques avant le vol.

## 📜 Licence

Code en accès libre pour usage pédagogique. Les manuels de vol et données techniques restent la propriété de **BRM Aero** et de l'**Aéroclub Air France**.
