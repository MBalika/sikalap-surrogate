"""
export/verify_export.py — Python↔transzpilált paritás-ellenőrzés (Node nélkül).

Az m2cgen ugyanabból a modell-reprezentációból generál JS-t és Python-kódot is.
Ha a Python-export bitre követi az eredeti XGBoost-predikciót, akkor a JS-export is
(azonos backend). Ez az ellenőrzés tehát Node telepítése nélkül igazolja a
transzpiláció hűségét.

Ezen felül kiír egy `web/models/parity_cases.json` fájlt: N véletlen bemenet + a
Python-predikciók, amit a web-UI a BÖNGÉSZŐBEN használ önellenőrzésre (a valódi
JS-en futtatva, lásd web/app.js).

Futtatás:  py export/verify_export.py
"""
from __future__ import annotations

import json
import pickle
import types
from pathlib import Path

import numpy as np
import m2cgen as m2c

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config  # noqa: E402
from ml.data_loader import feature_columns  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
WEB_MODELS_DIR = ROOT / "web" / "models"

N_CASES = 12
# Az XGBoost belül float32-ben számol, az m2cgen-kód float64-ben összegez, ezért
# ~1e-3 nagyságú eltérés természetes. Relatív + abszolút toleranciát használunk
# (np.allclose szemantika): |a−b| ≤ ATOL + RTOL·|a|.
RTOL = 1e-4
ATOL = 1e-2
SEED = 777


def _load_python_scorer(model) -> "types.FunctionType":
    """Az m2cgen Python-exportját betölti és visszaadja a `score(input)` fv-t.

    Az XGBoost hiányzó-érték ágai miatt a generált kód `nan`/`inf` literálokra
    hivatkozhat — a böngésző-JS-ben ezek globálisak (NaN/Infinity), az `exec`
    névterébe viszont kézzel kell betenni. (Valódi bemenetnél nincs hiányzó érték,
    így a `x >= nan` mindig False, ugyanúgy, ahogy a JS-ben.)
    """
    import math

    code = m2c.export_to_python(model, function_name="score")
    module = types.ModuleType("m2c_exported")
    module.__dict__.update(
        {"nan": float("nan"), "inf": float("inf"), "math": math, "np": np}
    )
    exec(code, module.__dict__)  # noqa: S102 — saját generált kód, biztonságos
    return module.score


def main() -> None:
    cfg = load_config()
    feats = feature_columns(cfg)
    rng = np.random.default_rng(SEED)

    # Véletlen, de reális bemenetek a tartományokból (a soil one-hot pontosan 1 db 1-es)
    cases = []
    for _ in range(N_CASES):
        row = []
        for k in cfg.continuous_keys:
            lo, hi = cfg.bounds(k)
            row.append(float(rng.uniform(lo, hi)))
        # one-hot talajtípus
        onehot = [0, 0, 0]
        onehot[int(rng.integers(0, 3))] = 1
        row.extend(onehot)
        cases.append(row)
    X = np.array(cases, dtype=float)

    max_abs_overall = 0.0
    max_rel_overall = 0.0
    parity = {"feature_order": feats, "cases": [c for c in cases], "expected": {}}

    print(f"Paritás-ellenőrzés {N_CASES} eseten (rtol={RTOL:g}, atol={ATOL:g}):")
    all_ok = True
    for key in cfg.output_keys:
        with (MODELS_DIR / f"{key}.pkl").open("rb") as fh:
            model = pickle.load(fh)

        y_native = model.predict(X).astype(float)
        scorer = _load_python_scorer(model)
        y_trans = np.array([scorer(list(x)) for x in X], dtype=float)

        abs_diff = np.abs(y_native - y_trans)
        rel_diff = abs_diff / np.maximum(np.abs(y_native), 1e-9)
        max_abs = float(np.max(abs_diff))
        max_rel = float(np.max(rel_diff))
        max_abs_overall = max(max_abs_overall, max_abs)
        max_rel_overall = max(max_rel_overall, max_rel)

        ok = bool(np.allclose(y_native, y_trans, rtol=RTOL, atol=ATOL))
        all_ok = all_ok and ok
        parity["expected"][key] = [round(float(v), 6) for v in y_native]
        if not ok:
            print(f"  ✗ {key:7s}  max_abs={max_abs:.3e}  max_rel={max_rel:.3e}  ← TÚL NAGY!")

    WEB_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (WEB_MODELS_DIR / "parity_cases.json").write_text(
        json.dumps(parity, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # JS-globális változat is (file:// alól fetch nélkül elérhető a böngésző-önteszthez):
    (WEB_MODELS_DIR / "parity_cases.js").write_text(
        "window.PLAXIS_PARITY = " + json.dumps(parity, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    print(f"\nLegnagyobb abszolút eltérés: {max_abs_overall:.3e}   "
          f"relatív: {max_rel_overall:.3e}")
    if all_ok:
        print("✔ PARITÁS OK — a transzpiláció hű (float32↔float64 kerekítésen belül).")
    else:
        print("✗ PARITÁS HIBA — nézd át a fenti sorokat.")
        sys.exit(1)
    print(f"✔ Böngésző-önellenőrző esetek → {WEB_MODELS_DIR / 'parity_cases.json'}")


if __name__ == "__main__":
    main()
