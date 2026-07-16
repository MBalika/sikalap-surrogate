# 🐍 Python-környezet beállítása (kezdőknek)

A konzulens gépén a Python **3.14.6** már telepítve van, a szükséges csomagokkal együtt.
Ez az útmutató a **hallgató gépéhez** (és emlékeztetőnek), lépésről lépésre.

## 1. Python telepítése
1. Töltsd le: <https://www.python.org/downloads/> → „Download Python 3.12" (a 3.12 a
   legbiztosabb a `plxscripting`-hez; a 3.14 is jó a ML-részhez).
2. A telepítőben **pipáld be a „Add python.exe to PATH"** dobozt!
3. Telepítés után ellenőrizd (PowerShell):
   ```powershell
   py --version
   ```
   Ha `Python 3.x.x` jön, jó. Ha a Microsoft Store nyílik meg, akkor a valódi Python
   nincs telepítve — a Store-„placeholder"-t kell kikapcsolni:
   **Beállítások → Alkalmazások → Speciális alkalmazásbeállítások →
   Alkalmazás-végrehajtási aliasok →** kapcsold KI a `python.exe` és `python3.exe` aliast.

## 2. A projekt függőségei
A projekt mappájában (`d:\CLAUDE\SURROGATE MODELL`):
```powershell
py -m pip install -r requirements.txt
```
Ez telepíti: numpy, pandas, scikit-learn, xgboost, m2cgen, scipy, pyyaml, pytest.

## 3. Első „száraz" futtatás (PLAXIS nélkül)
```powershell
py ml/make_smoke_fixture.py                       # 50 teszt-sor
py ml/train_xgb.py                                 # tanítás a fixture-ön
py export/export_to_js.py                          # böngésző-modellek
py export/verify_export.py                         # paritás-ellenőrzés
```
Ha ezek végigfutnak, a környezet kész.

## 4. Gyakori hibák
- **„A Python nem található"** → a PATH/alias beállítás hiányzik (lásd 1. pont).
- **`UnicodeEncodeError` a konzolon** → a projekt ezt már kezeli (a `common.py` UTF-8-ra
  állítja a kimenetet). Ha máshol jönne elő: `$env:PYTHONUTF8=1` a PowerShellben.
- **`plxscripting` nem található** → az CSAK a PLAXIS-os gépen kell, a Bentley-telepítőből
  jön, nem pip-ből (lásd requirements.txt megjegyzés).
