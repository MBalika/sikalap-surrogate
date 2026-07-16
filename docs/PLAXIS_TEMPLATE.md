# 🏗️ PLAXIS-sablon és a valódi backend bekötése

Ez az egyetlen kézi lépés a hurokban: **a hallgató egyszer megépít egy sablon-modellt**,
és bekötteti a `RealPlaxisBackend`-et. Utána a generálás teljesen automatikus.

## 1. A sablon-modell (egyszer, kézzel a PLAXIS 2D-ben)
Építs egy paraméterezhető síkalap-modellt drénezett HSsmall talajon:
- **Geometria:** homogén féltér, felül a merev alaptest (szélesség `B`, alapsík mélység `D`).
- **Talaj:** HSsmall anyagmodell (a paramétereket a script írja felül).
- **Vízszint:** vízszintes GWL a `GWL` mélységben.
- **Fázisok:** (1) K0-eljárás → (2) az alaptest aktiválása → (3) erővezérelt terhelés a törésig,
  fix `H/V = tan α` iránnyal.
- **Curve point:** az alaptest KÖZEPÉN egy pont, ahonnan a (teher, süllyedés) görbe kiolvasható.

## 2. A `RealPlaxisBackend.simulate()` bekötése
A váz itt van: `plaxis/plaxis_api.py`. A `simulate(case, hs, cfg)` lépései:

```python
from plxscripting.easy import new_server
s_i, g_i = new_server("localhost", PORT, password=PW)   # Remote Scripting

# 1) sablon megnyitása (vagy egy tiszta másolat)
# 2) HSsmall anyag felülírása a `hs` mezőiből:
#      E50ref, Eoedref, Euref, m, G0ref, gamma07, phi, c, psi, K0nc, nu_ur, Rf, p_ref, gamma
# 3) geometria: B, D beállítása; GWL vízszint
# 4) hálógenerálás
# 5) fázisok: K0 → terhelés H/V=tan(alpha) törésig, automatikus lépésközzel
# 6) konvergencia-ellenőrzés (ha nem konvergál → converged=False)
# 7) curve point kiolvasása: loads[], settlements[]
# 8) R_k = a törőteher függőleges komponense
# 9) from plaxis.extract_results import resample_ps
#    ps = resample_ps(loads, settlements, R_k, cfg.ps_load_fractions)
# 10) return {"R_k":..., "s_max":ps[-1], "ps_01":ps[0], ..., "converged":True, "source":"plaxis_real"}
```

> **FONTOS:** a HSsmall tulajdonságnevek **verzió-specifikusak** a Scripting API-ban.
> A hallgató a ti PLAXIS-verziótokban validálja őket (pl. `E50ref` vs `E50Ref`), és minden
> PLAXIS-hívást ebbe a fájlba zárjon — a hurok többi része nem függ a verziótól.

## 3. Futtatás valódi PLAXIS-szal
```powershell
py plaxis/sampling.py --n 6000                     # teljes kísérlet-terv
py plaxis/run_generation.py --api real             # valódi futások (checkpoint/resume)
py ml/train_xgb.py --csv data/raw/plaxis_results.csv --real-only
```
A `run_generation.py` minden sikeres futást azonnal a fájlba ír, a nem-konvergálókat
kihagyja és logolja, és megszakítás után folytatható (a kész `run_id`-ket átugorja).
