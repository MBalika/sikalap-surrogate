# 🔒 Tudományos integritás

A projekt sarokköve: **az éles surrogate modell kizárólag valódi PLAXIS-adatból tanulhat.**

## Miért?
Ha a modellt EC7-képletből vagy más zárt formulából generált adaton tanítanánk, akkor
csak azt a képletet közelítené — nem adna hozzá semmit, sőt a képlet hibáit is átvenné.
A surrogate értéke pontosan az, hogy a **végeselemes** (HSsmall) számítás input–output
kapcsolatát tanulja meg, amit zárt képlet nem ad vissza.

## A három adatforrás és a szabály
A `plaxis_results.csv` `source` oszlopa mindig jelzi az eredetet:

| `source` | Mi ez? | Éles tanításra? |
|----------|--------|-----------------|
| `plaxis_real` | valódi PLAXIS 2D HSsmall futás | **IGEN** |
| `mock_plaxis` | a `mock_plaxis_api.py` egyszerűsített képlete (plumbing-teszt) | **NEM** |
| `smoke_fixture` | véletlen, nem-fizikai sorok (a `make_smoke_fixture.py`-ból) | **NEM** |

Az éles tanítás mindig `--real-only` kapcsolóval fut:
```powershell
py ml/train_xgb.py --csv data/raw/plaxis_results.csv --real-only
```
Ez a `data_loader.load_dataset(real_only=True)`-on keresztül kiszűr minden nem-valódi sort,
és hibát dob, ha egyetlen `plaxis_real` sor sincs — így sosem tanulhatunk véletlenül
mock- vagy fixture-adaton.

## Amit dokumentálni kell (a modell megbízhatóságához)
- a **tanítási tartomány** (a config.yaml `inputs`/`soil_types` szerint),
- a **validációs hibák** (R², RMSE, MAE — `models/metrics.csv`),
- a **failure-region pontosság** (nem elég az átlagos R²),
- a **fizikai konzisztencia** (monoton p–s, hihető nagyságrend),
- a **numerikus modell minősége** (konvergencia-arány, hálófüggetlenség).

## A fixture és a mock szerepe
Mindkettő **csak a szoftver csővezetékének** teszteléséhez van — hogy a betöltés →
tanítás → export → web lánc PLAXIS nélkül is végigfusson. A becsléseik NEM
geotechnikai eredmények, és ezt a web-felület is figyelmeztetésként kiírja.
