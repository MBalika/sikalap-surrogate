"""
ml/data_loader.py — a tanítóadat betöltése az adatszerződés szerint.

Feladat:
  1. beolvassa a plaxis_results.csv-t (fixture VAGY valódi),
  2. kiszűri a nem-konvergált sorokat,
  3. (éles módban) kiszűri a nem valódi (smoke_fixture) sorokat,
  4. a `soil_type` kategorikus oszlopot one-hot kódolja (a config sorrendjében),
  5. visszaadja X (jellemzők) és Y (22 kimenet) DataFrame-eket.

A one-hot kódolást SAJÁT kézzel csináljuk (nem sklearn OneHotEncoder), mert így
a böngészőbe exportált modell bemenete pontosan ugyanilyen sorrendű oszlopokat
vár — és a web-UI is triviálisan reprodukálja.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config, Config  # noqa: E402

DEFAULT_CSV = (
    Path(__file__).resolve().parent.parent / "data" / "fixture" / "plaxis_results.csv"
)


def soil_onehot_columns(cfg: Config) -> list[str]:
    """A one-hot oszlopnevek: soil_homok, soil_iszap, soil_agyag (config-sorrend)."""
    return [f"soil_{v}" for v in cfg.soil_type_values]


def feature_columns(cfg: Config) -> list[str]:
    """A modell tényleges bemeneti oszlopai: 8 folytonos + 3 one-hot = 11 oszlop."""
    return cfg.continuous_keys + soil_onehot_columns(cfg)


def encode_features(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """A nyers 9 bemenetből a modell 11 jellemző-oszlopa (soil_type → one-hot)."""
    X = df[cfg.continuous_keys].copy()
    for v in cfg.soil_type_values:
        X[f"soil_{v}"] = (df["soil_type"] == v).astype(int)
    return X[feature_columns(cfg)]


def load_dataset(
    csv_path: str | Path | None = None,
    *,
    real_only: bool = False,
    cfg: Config | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Betölti és előkészíti az adatot.

    Args:
        csv_path : a CSV útvonala (alap: a fixture).
        real_only: ha True, csak `source == "plaxis_real"` sorok maradnak
                   (ÉLES tanításnál mindig True legyen!).
    Returns:
        (X, Y, raw)  ahol
          X   : jellemzők (11 oszlop),
          Y   : 22 kimenet,
          raw : a szűrt nyers DataFrame (audithoz).
    """
    if cfg is None:
        cfg = load_config()
    path = Path(csv_path) if csv_path is not None else DEFAULT_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Nem találom a tanítóadatot: {path}\n"
            f"Generálj smoke-fixture-t:  py ml/make_smoke_fixture.py"
        )

    df = pd.read_csv(path)

    # 1) csak konvergált futások
    if "converged" in df.columns:
        df = df[df["converged"].astype(bool)]

    # 2) éles módban csak valódi PLAXIS-adat
    if real_only:
        if "source" not in df.columns:
            raise ValueError("Hiányzik a 'source' oszlop — nem tudom kiszűrni a fixture-t.")
        df = df[df["source"] == "plaxis_real"]
        if len(df) == 0:
            raise ValueError(
                "real_only=True, de nincs egyetlen 'plaxis_real' sor sem. "
                "Még nem érkezett valódi PLAXIS-adat?"
            )

    df = df.reset_index(drop=True)

    X = encode_features(df, cfg)
    Y = df[cfg.output_keys].copy()
    return X, Y, df


if __name__ == "__main__":
    cfg = load_config()
    X, Y, raw = load_dataset(cfg=cfg)
    print(f"Sorok: {len(X)}")
    print(f"Jellemzők ({X.shape[1]}): {list(X.columns)}")
    print(f"Kimenetek ({Y.shape[1]}): {list(Y.columns)}")
    print(f"Forrás-eloszlás:\n{raw['source'].value_counts()}")
