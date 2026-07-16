# 📋 PROJEKT ÁLLAPOT — PLAXIS surrogate síkalap oktatóeszköz

> **Belépési pont.** Utoljára frissítve: 2026-07-15. Build-mappa: `d:\CLAUDE\SURROGATE MODELL`.
> A szoftver-váz felépült ÉS a teljes offline lánc végigfut (Python 3.14 + telepített csomagok).

---

## 1. Egy mondat
Webes oktatóeszköz: csúszkákkal állított síkalap-paraméterekből egy böngészőben futó
XGBoost surrogate azonnal becsli a törőterhet (R_k), a süllyedést (s_max) és a p–s görbét.
Tanítóadat: PLAXIS 2D HSsmall. Határidő: 2027. május.

## 2. 🔒 Lezárt döntések (2026-07-15)
1. **Talajmodell:** HSsmall · **drénezett**, homogén induló kör · 2D síkalakváltozás (R_k = kN/m).
2. **9 bemenet:** 8 folytonos (B, D, φ', c', γ, E', GWL, α) + **talajtípus-kapcsoló** (homok/iszap/agyag).
3. **Talajtípus = külön bemenet** → a korrelációs kaszkád típusonként más (m, γ0.7, Eoed/E50…).
4. **E' = E₅₀ʳᵉᶠ** @ p_ref = 100 kPa.
5. **R_k** = a törőteher függőleges komponense az adott α-nál.
6. **UI:** több statikus fájl, böngészőben futó modell, `file://`-ből is megnyílik.
7. **Tudományos integritás:** éles modell CSAK valódi PLAXIS-adatból tanul (lásd docs/SCIENTIFIC_INTEGRITY.md).

## 3. ✅ Ami elkészült és FUT
| Réteg | Fájl(ok) | Állapot |
|-------|----------|---------|
| Konfiguráció | `config.yaml` | egyetlen igazságforrás (9 input, 22 output, talajok) |
| Adatszerződés | `DATA_CONTRACT.md` | fixture ↔ valódi drop-in azonos fejléc |
| Korrelációk | `plaxis/derive_hssmall.py` | talajtípus-függő HSsmall kaszkád ✔ |
| Mintavételezés | `plaxis/sampling.py` | LHS + rétegzett talaj → doe.csv ✔ |
| PLAXIS hurok | `plaxis/{plaxis_api,mock_plaxis_api,run_generation,extract_results}.py` | mock-first, checkpoint/resume ✔ |
| Fixture | `ml/make_smoke_fixture.py` | 50 jelölt, nem-fizikai sor ✔ |
| ML | `ml/{common,data_loader,train_xgb,metrics}.py` | 22 modell tanul, metrikák ✔ |
| Export | `export/{export_to_js,verify_export}.py` | m2cgen → JS + bundle + paritás ✔ |
| Web UI | `web/{index.html,app.js,chart.js,ec7.js}` | csúszkák, KPI-k, p–s grafikon, önteszt ✔ |

**Ellenőrzött végigfutás:** `sampling → mock hurok → train_xgb → export_to_js → verify_export` — mind zöld.
Paritás (Python ↔ transzpilált): relatív eltérés ~1e-6.

## 4. ⏭️ Következő lépések (fontossági sorrend)
1. **Valódi PLAXIS-backend bekötése** (`RealPlaxisBackend.simulate`) a ti verziótokban — docs/PLAXIS_TEMPLATE.md.
2. **Paramétertartományok kalibrálása** magyar talajokra (a config.yaml `inputs` és `soil_types`).
3. **Kvantilis modellek** (0.1/0.5/0.9) a bizonytalansági sávhoz — a config `ml.quantiles` már megvan.
4. **Optuna-hangolás + SHAP** (5–6. hónap) — a train_xgb bővítése.
5. **Payload-optimalizálás:** a `bundle.js` most ~4.7 MB (22×200 fa). Deploy előtt: kevesebb fa / p–s lazy-load.
6. **EC7 teljes motor portolása** (`sikalapok-teherbiras/index.html`) a mostani egyszerűsített `ec7.js` helyére.

## 5. ⚠️ Kockázatok (változatlanul)
- PLAXIS Scripting licenc; hallgató kiesése (fő + backup); HSsmall verzió-specifikus tulajdonságnevek.
- p–s monotonitás: a 20 független modellt a web UI kumulatív-max clamppel köti meg (később monoton XGBoost-kényszer).

## 6. Hogyan futtasd (0. hónap kész)
```powershell
py -m pip install -r requirements.txt          # egyszer
py ml/make_smoke_fixture.py                     # fixture
py plaxis/sampling.py --n 100                    # kísérlet-terv
py plaxis/run_generation.py --api mock           # (mock) adat
py ml/train_xgb.py --csv data/raw/plaxis_results.csv
py export/export_to_js.py                        # böngésző-modellek
py export/verify_export.py                       # paritás
start web\index.html                             # a felület
```
