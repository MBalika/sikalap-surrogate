"""
plaxis/sampling.py — a kísérlet-terv (Design of Experiments) generálása.

A 8 folytonos paramétert Latin Hypercube Sampling-gel (LHS) mintavételezzük a
config.yaml tartományain, a talajtípust pedig RÉTEGZETTEN (minden típusra közel
azonos számú minta). Így a bemeneti tér egyenletesen le van fedve.

Kimenet:
  data/raw/doe.csv          — 1 sor = 1 tervezett futás (a 9 bemenet + run_id)
  data/raw/doe_hssmall.csv  — ugyanaz + a származtatott teljes HSsmall-készlet (audit)

Futtatás:
  py plaxis/sampling.py --n 100          # pilot
  py plaxis/sampling.py --n 6000         # teljes kör
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config  # noqa: E402
from plaxis.derive_hssmall import derive_hssmall  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"


def sample_doe(n: int, cfg, seed: int) -> pd.DataFrame:
    """n mintás LHS a folytonos paraméterekre + rétegzett talajtípus."""
    cont = cfg.continuous
    d = len(cont)

    sampler = qmc.LatinHypercube(d=d, seed=seed)
    unit = sampler.random(n=n)                      # [0,1]^d
    lows = np.array([p["min"] for p in cont])
    highs = np.array([p["max"] for p in cont])
    scaled = qmc.scale(unit, lows, highs)           # a tartományokra skálázva

    df = pd.DataFrame(scaled, columns=cfg.continuous_keys)
    # kerekítés józan tizedesekre (a PLAXIS-nak úgyis elég)
    df = df.round(3)

    # Rétegzett talajtípus: körkörösen kiosztva, majd megkeverve determinisztikusan.
    soils = cfg.soil_type_values
    st = np.array([soils[i % len(soils)] for i in range(n)])
    rng = np.random.default_rng(seed + 1)
    rng.shuffle(st)
    df.insert(0, "soil_type", st)

    df.insert(0, "run_id", np.arange(n))
    # oszlopsorrend: run_id + 8 folytonos + soil_type (a DATA_CONTRACT szerint)
    df = df[["run_id"] + cfg.continuous_keys + ["soil_type"]]
    return df


def audit_hssmall(doe: pd.DataFrame, cfg) -> pd.DataFrame:
    """A doe minden sorához a származtatott HSsmall-készlet (átláthatóság)."""
    records = []
    for _, r in doe.iterrows():
        hs = derive_hssmall(
            phi=float(r["phi"]), c=float(r["c"]), gamma=float(r["gamma"]),
            E=float(r["E"]), soil_type=str(r["soil_type"]), cfg=cfg,
        )
        rec = {"run_id": int(r["run_id"]), "soil_type": r["soil_type"]}
        rec.update(hs.as_dict())
        records.append(rec)
    return pd.DataFrame(records)


def main() -> None:
    ap = argparse.ArgumentParser(description="LHS kísérlet-terv generálása")
    ap.add_argument("--n", type=int, default=None, help="minták száma (alap: config n_pilot)")
    ap.add_argument("--seed", type=int, default=None, help="véletlen mag (alap: config seed)")
    args = ap.parse_args()

    cfg = load_config()
    n = args.n if args.n is not None else int(cfg.sampling["n_pilot"])
    seed = args.seed if args.seed is not None else int(cfg.sampling["seed"])

    doe = sample_doe(n, cfg, seed)
    hss = audit_hssmall(doe, cfg)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    doe.to_csv(RAW_DIR / "doe.csv", index=False)
    hss.to_csv(RAW_DIR / "doe_hssmall.csv", index=False)

    print(f"✔ {n} mintás kísérlet-terv → {RAW_DIR / 'doe.csv'}")
    print(f"✔ HSsmall audit          → {RAW_DIR / 'doe_hssmall.csv'}")
    print("\nTalajtípus-eloszlás:")
    print(doe["soil_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
