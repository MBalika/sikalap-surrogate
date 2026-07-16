"""
export/export_to_js.py — a betanított modellek → tiszta JavaScript.

Minden models/<kulcs>.pkl XGBoost-modellt az m2cgen tiszta JS-kóddá fordít, amely
NEM igényel könyvtárat a böngészőben (csak sima aritmetika a fák leveleiből).

Kimenet:
  web/models/<kulcs>.js   — mindegyik egy globális regiszterbe teszi a score-fv-t:
                            window.PLAXIS_MODELS["<kulcs>"] = function(input){...}
  web/models/manifest.json — a jellemzők SORRENDJE + a 22 kimenet listája + fájlnevek

A `manifest.json` a szerződés a Python és a böngésző között: az `input` tömb
oszlopsorrendje PONTOSAN a manifest `feature_order` mezője.

Futtatás:  py export/export_to_js.py
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import m2cgen as m2c

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config  # noqa: E402
from ml.data_loader import feature_columns  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
WEB_MODELS_DIR = ROOT / "web" / "models"


def wrap_js(inner_code: str, key: str) -> str:
    """Az m2cgen `score` függvényét izolált IIFE-be zárja és regiszterbe teszi."""
    return (
        "// AUTOGENERÁLT — ne szerkeszd kézzel! Forrás: export/export_to_js.py\n"
        "window.PLAXIS_MODELS = window.PLAXIS_MODELS || {};\n"
        "(function () {\n"
        f"{inner_code}\n"
        f'  window.PLAXIS_MODELS["{key}"] = score;\n'
        "})();\n"
    )


def main() -> None:
    cfg = load_config()
    feats = feature_columns(cfg)
    WEB_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    exported = []
    for key in cfg.output_keys:
        pkl = MODELS_DIR / f"{key}.pkl"
        if not pkl.exists():
            raise FileNotFoundError(f"Hiányzik a modell: {pkl}. Futtasd előbb: py ml/train_xgb.py")
        with pkl.open("rb") as fh:
            model = pickle.load(fh)

        js_inner = m2c.export_to_javascript(model, function_name="score", indent=2)
        (WEB_MODELS_DIR / f"{key}.js").write_text(wrap_js(js_inner, key), encoding="utf-8")
        exported.append(key)
        print(f"  ✔ {key}.js")

    # A csúszkákhoz kell a bemenetek teljes megjelenítési metaadata.
    inputs_meta = [
        {
            "key": p["key"], "jel": p["jel"], "nev": p["nev"],
            "egyseg": p["egyseg"], "min": p["min"], "max": p["max"],
        }
        for p in cfg.continuous
    ]
    soil_meta = next((c for c in cfg.categorical if c["key"] == "soil_type"), None)

    manifest = {
        "feature_order": feats,               # a böngésző ilyen sorrendben adja az input tömböt
        "continuous_keys": cfg.continuous_keys,
        "inputs_meta": inputs_meta,
        "soil_type_values": cfg.soil_type_values,
        "soil_meta": soil_meta,
        "output_scalars": cfg.scalar_output_keys,
        "output_ps": cfg.ps_keys,
        "ps_load_fractions": cfg.ps_load_fractions,
        "model_files": {k: f"models/{k}.js" for k in exported},
    }
    (WEB_MODELS_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # --- bundle.js: MINDEN modell + a manifest EGY fájlban, hogy az index.html
    #     szerver nélkül (file://) is betölthesse egyetlen <script>-tel. ---
    parts = [
        "// AUTOGENERÁLT bundle — mind a 22 modell + manifest. Forrás: export/export_to_js.py",
        "window.PLAXIS_MANIFEST = " + json.dumps(manifest, ensure_ascii=False) + ";",
    ]
    for key in exported:
        parts.append((WEB_MODELS_DIR / f"{key}.js").read_text(encoding="utf-8"))
    (WEB_MODELS_DIR / "bundle.js").write_text("\n".join(parts) + "\n", encoding="utf-8")

    print(f"\n✔ {len(exported)} JS-modell + manifest.json + bundle.js → {WEB_MODELS_DIR}")
    print(f"  Jellemző-sorrend ({len(feats)}): {feats}")


if __name__ == "__main__":
    main()
