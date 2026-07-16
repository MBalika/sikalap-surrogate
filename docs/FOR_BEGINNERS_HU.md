# 👶 Áttekintés kezdőknek — hogyan áll össze az egész

Ez a dokumentum egyben magyarázza el, mit csinál a rendszer, mérnöki fejjel.

## A nagy kép egy ábrában
```
   config.yaml  ── az EGYETLEN igazságforrás (9 bemenet, 22 kimenet, talajok)
        │
        ▼
 [1] sampling.py ───► doe.csv          (sok paraméter-kombináció, LHS-sel)
        │
        ▼
 [2] run_generation.py ──(derive_hssmall + PLAXIS/mock)──► plaxis_results.csv
        │                                                    (a TANÍTÓADAT)
        ▼
 [3] train_xgb.py ───► models/*.pkl    (22 betanított XGBoost modell)
        │
        ▼
 [4] export_to_js.py ───► web/models/bundle.js   (a modellek tiszta JS-ként)
        │
        ▼
 [5] index.html ───► a böngészőben futó felület (csúszkák + grafikon)
```

## Mi micsoda?
- **Surrogate (helyettesítő) modell:** egy gyors közelítő, ami a lassú PLAXIS-számítás
  helyett azonnal válaszol. Nem helyettesíti a geotechnikai gondolkodást — csak a drága
  számítást teszi sokszor futtathatóvá.
- **HSsmall:** a talaj anyagmodellje a PLAXIS-ban (a süllyedésre pontos, ezért ezt használjuk).
- **derive_hssmall:** a 9 „emberi" bemenetből kiszámolja a PLAXIS-nak kellő ~15 HSsmall-paramétert,
  determinisztikus mérnöki korrelációkkal (Jáky, Bolton, Benz…). Így a felhasználónak csak
  9 dolgot kell állítania.
- **one-hot kódolás:** a talajtípus (szöveg) helyett 3 db 0/1 oszlop (`soil_homok`, `soil_iszap`,
  `soil_agyag`), mert a gépi tanulás számokkal dolgozik.
- **m2cgen:** a betanított modellt tiszta JavaScript-té fordítja, ami könyvtár nélkül fut a
  böngészőben — így a felhasználó gépén, adat feltöltése nélkül számol.
- **paritás-ellenőrzés:** biztosítja, hogy a böngészőbe exportált modell UGYANAZT számolja,
  mint a Python (a kis eltérés csak float32/float64 kerekítés).

## A „mock" mint ideiglenes PLAXIS
Amíg nincs valódi PLAXIS-adat, a `mock_plaxis_api.py` egy egyszerű képlettel „úgy tesz,
mintha" PLAXIS lenne — így az egész lánc tesztelhető. **Ez nem valódi eredmény**, és a
web-felület ezt figyelmeztetésként ki is írja. A valódi adat érkezésekor egyetlen kapcsoló
(`--api real`) a különbség, a kód többi része változatlan.

## Mit állíts, ha valamit módosítani akarsz?
- **Más paramétertartomány / új egység?** → `config.yaml`, az `inputs` blokk. Minden követi.
- **Más talajkorreláció?** → `config.yaml`, a `soil_types` blokk (m, γ0.7, arányok).
- **Több/kevesebb p–s pont?** → `config.yaml`, `outputs.ps_curve.n_points`.
- **Más XGBoost-beállítás?** → `ml/train_xgb.py`, a `_make_xgb()` függvény.

## Aranyszabály
Oszlopneveket, tartományokat SOHA ne írj át kézzel több helyen — csak a `config.yaml`-ben.
A kód, az adatszerződés és a web-felület onnan veszi az igazságot.
