# 🏗️ PLAXIS surrogate — síkalap oktatóeszköz

Webes **oktatóeszköz**: a hallgató csúszkákkal állít síkalap-paramétereket, és
valós időben látja a **teherbírást (R_k)**, a **süllyedést (s_max)** és a
**terhelés–süllyedés (p–s) görbét** — egy **XGBoost helyettesítő (surrogate)
modell** alapján, amit **PLAXIS 2D HSsmall** szimulációkon tanítunk be. A modell a
böngészőben fut (statikus HTML/JS), nincs szerveroldali számítás.

- **Határidő:** 2027. május (komplett, valós hallgatói teszteléssel)
- **Talajmodell:** HSsmall · **drénezett** homogén induló kör · 2D síkalakváltozás
- **Bemenet:** 9 paraméter (8 folytonos + talajtípus-kapcsoló)
- **Tudományos integritás:** az éles modell KIZÁRÓLAG valódi PLAXIS-adatból tanul

---

## 📁 Mappaszerkezet

```
SURROGATE MODELL/
├─ config.yaml            ← EGYETLEN igazságforrás (bemenetek, kimenetek, talajok)
├─ DATA_CONTRACT.md       ← a CSV-k pontos formátuma
├─ requirements.txt       ← Python függőségek
├─ plaxis/                ← PLAXIS-automatizálás (mock-first, futtatható PLAXIS nélkül is)
│  ├─ derive_hssmall.py     9 bemenet → teljes HSsmall készlet (talajtípus-függő)
│  ├─ sampling.py           Latin Hypercube → doe.csv
│  ├─ plaxis_api.py         (később) valódi Remote Scripting réteg
│  ├─ mock_plaxis_api.py    (később) PLAXIS-mentes hamis API a teszteléshez
│  └─ extract_results.py    (később) eredmény-kiolvasás → plaxis_results.csv
├─ ml/                    ← ML pipeline
│  ├─ common.py             config-betöltés, oszlopnevek
│  ├─ make_smoke_fixture.py ~50 jelölt, NEM fizikai sor a plumbing-hoz
│  ├─ data_loader.py        CSV → X, y (adatszerződés szerint)
│  ├─ train_xgb.py          baseline + XGBoost tanítás, metrikák
│  └─ metrics.py            R², RMSE, MAE
├─ export/                ← (később) m2cgen: modell → tiszta JS + paritás-ellenőrzés
├─ web/                   ← (később) statikus UI: csúszkák, p–s grafikon, EC7 összevetés
├─ data/
│  └─ fixture/            ← a smoke-fixture CSV (verziókövetve, kicsi)
├─ models/               ← betanított modellek (gitignore-olt)
└─ docs/                 ← útmutatók, PLAXIS-sablon, integritás
```

---

## 🚀 Első lépések (0. hónap)

### 1. Python telepítése (EGYSZER, most még hiányzik!)
A gépen jelenleg **nincs valódi Python** — csak a Windows Store placeholder.
Lásd: [`docs/PYTHON_SETUP_HU.md`](docs/PYTHON_SETUP_HU.md).

### 2. Függőségek
```powershell
py -m pip install -r requirements.txt
```

### 3. A pipeline „szárazon" futtatása (PLAXIS és valódi adat nélkül)
```powershell
py ml/make_smoke_fixture.py      # ~50 jelölt sor → data/fixture/plaxis_results.csv
py ml/train_xgb.py               # betöltés → tanítás → metrikák (a fixture-ön)
```
Ha ez végigfut, a **plumbing kész** — a valódi PLAXIS-adat érkezésekor csak
kicseréljük a fixture-t a `plaxis_results.csv`-re (azonos fejléc, drop-in).

---

## 🔒 A legfontosabb szabály

A `data/fixture/` sorai **nem valódi geotechnikai eredmények** — kizárólag a
szoftver csővezetékének teszteléséhez. Éles modellt csak `source == "plaxis_real"`
sorokból tanítunk. Részletek: [`docs/SCIENTIFIC_INTEGRITY.md`](docs/SCIENTIFIC_INTEGRITY.md).

---

## 📌 Állapot

A projekt teljes állapot-összefoglalója és a nyitott/lezárt döntések:
[`PROJEKT_STATUS.md`](PROJEKT_STATUS.md).
