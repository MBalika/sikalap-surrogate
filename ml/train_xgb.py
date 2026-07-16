"""
ml/train_xgb.py — a 22 egy-kimenetű modell betanítása.

Minden kimenetre (R_k, s_max, ps_01..ps_20) külön modellt tanítunk:
  1. baseline: lineáris regresszió (viszonyítási alap),
  2. XGBoost regresszor (a tényleges surrogate).

A kis fixture-en (50 sor) ez csak a CSŐVEZETÉKET teszteli — a metrikák NEM
jelentenek geotechnikai pontosságot. Valódi adatnál jön az Optuna-hangolás,
a keresztvalidáció és a SHAP.

Kimenet:
  models/<kulcs>.pkl        — betanított XGBoost modellek (m2cgen exporthoz)
  models/metrics.csv        — kimenetenként baseline vs XGBoost R²/RMSE/MAE

Futtatás:  py ml/train_xgb.py
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config  # noqa: E402
from ml.data_loader import load_dataset  # noqa: E402
from ml import metrics  # noqa: E402

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def _make_xgb(random_state: int):
    """XGBoost regresszor józan alapbeállításokkal (kis adathoz visszafogva)."""
    from xgboost import XGBRegressor

    return XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=random_state,
        n_jobs=-1,
        objective="reg:squarederror",
        # FONTOS: explicit base_score, különben az XGBoost 3.x tanult intercept-je
        # `nan`-ként kerül az m2cgen-exportba (return nan + ...). base_score=0 esetén
        # a fák tanulják meg a teljes szintet, a JS-export pedig hibátlan lesz.
        base_score=0.0,
    )


def main(csv_path: str | None = None, real_only: bool = False) -> None:
    cfg = load_config()
    ml_cfg = cfg.ml

    X, Y, raw = load_dataset(csv_path, real_only=real_only, cfg=cfg)
    n = len(X)
    print(f"Tanítóadat: {n} sor, {X.shape[1]} jellemző, {Y.shape[1]} kimenet.")
    if raw.get("source") is not None and (raw["source"] == "smoke_fixture").any():
        print("⚠  FIXTURE-adat van a halmazban — a metrikák NEM geotechnikaiak!")

    X_tr, X_te, Y_tr, Y_te = train_test_split(
        X, Y, test_size=ml_cfg["test_size"], random_state=ml_cfg["random_state"]
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for key in cfg.output_keys:
        y_tr = Y_tr[key].to_numpy()
        y_te = Y_te[key].to_numpy()

        # 1) baseline lineáris
        lin = LinearRegression().fit(X_tr, y_tr)
        lin_m = metrics.summary(y_te, lin.predict(X_te))

        # 2) XGBoost
        xgb = _make_xgb(ml_cfg["random_state"]).fit(X_tr, y_tr)
        xgb_m = metrics.summary(y_te, xgb.predict(X_te))

        # mentés (a teljes X-en újratanítva, hogy a végső export a teljes adaton álljon)
        xgb_full = _make_xgb(ml_cfg["random_state"]).fit(X, Y[key].to_numpy())
        with (MODELS_DIR / f"{key}.pkl").open("wb") as fh:
            pickle.dump(xgb_full, fh)

        rows.append(
            {
                "output": key,
                "lin_R2": round(lin_m["R2"], 4),
                "xgb_R2": round(xgb_m["R2"], 4),
                "lin_RMSE": round(lin_m["RMSE"], 4),
                "xgb_RMSE": round(xgb_m["RMSE"], 4),
                "lin_MAE": round(lin_m["MAE"], 4),
                "xgb_MAE": round(xgb_m["MAE"], 4),
            }
        )
        print(
            f"  {key:7s}  baseline R²={lin_m['R2']:+.3f}   "
            f"XGB R²={xgb_m['R2']:+.3f}   XGB RMSE={xgb_m['RMSE']:.3f}"
        )

    metrics_df = pd.DataFrame(rows)
    metrics_path = MODELS_DIR / "metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    print(f"\n✔ {len(rows)} modell elmentve → {MODELS_DIR}")
    print(f"✔ Metrikák → {metrics_path}")
    print(f"  Átlag XGB R² (a fixture-ön, tájékoztató): {metrics_df['xgb_R2'].mean():.3f}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="A 22 surrogate-modell betanítása")
    ap.add_argument(
        "--csv", type=str, default=None,
        help="tanító CSV (alap: a smoke-fixture). Pl. data/raw/plaxis_results.csv",
    )
    ap.add_argument(
        "--real-only", action="store_true",
        help="csak source==plaxis_real sorok (ÉLES tanításnál kötelező!)",
    )
    args = ap.parse_args()
    main(csv_path=args.csv, real_only=args.real_only)
