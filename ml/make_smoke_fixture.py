"""
ml/make_smoke_fixture.py — smoke-test fixture generátor.

FONTOS: az itt generált sorok **NEM valódi geotechnikai eredmények**. Céljuk
kizárólag a szoftver-csővezeték (betöltés → tanítás → export → web) végigfuttatása
valódi PLAXIS-adat NÉLKÜL. Minden sor `source = "smoke_fixture"` jelölést kap, és
az éles tanításnál ki KELL szűrni.

A fájl szándékosan csak a Python-alapkönyvtárat használja (random, csv), így már
egy frissen telepített Python-nal, pip-csomagok előtt is lefut.

Kimenet:  data/fixture/plaxis_results.csv   (a DATA_CONTRACT.md szerinti fejléc)

Futtatás:  py ml/make_smoke_fixture.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

# Projektgyökér a sys.path-ra, hogy a common.py importálható legyen közvetlen
# futtatáskor is.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config  # noqa: E402

N_ROWS = 50
SEED = 20260715
OUT = Path(__file__).resolve().parent.parent / "data" / "fixture" / "plaxis_results.csv"


def _rand_in(rng: random.Random, lo: float, hi: float, ndigits: int = 3) -> float:
    return round(rng.uniform(lo, hi), ndigits)


def make_row(rng: random.Random, cfg, run_id: int) -> dict:
    """Egy jelölt, NEM fizikai sor a 9 bemenettel és 22 kimenettel."""
    row: dict[str, object] = {"run_id": run_id}

    # --- 9 bemenet, a config tartományain belül (hogy legalább az UI-hoz reális
    #     legyen a skála; az OUTPUT-ok viszont nem fizikaiak) ---
    for p in cfg.continuous:
        row[p["key"]] = _rand_in(rng, p["min"], p["max"])
    row["soil_type"] = rng.choice(cfg.soil_type_values)

    # --- Kimenetek (kitalált, de belsőleg konzisztens: monoton p–s görbe) ---
    # R_k: durva, dimenzióhelyes nagyságrend csak a skála kedvéért.
    R_k = round(rng.uniform(150.0, 3000.0), 1)          # kN/m
    s_max = round(rng.uniform(5.0, 60.0), 2)            # mm

    # p–s: monoton növekvő süllyedés a 20 teher-szinten, ps_20 == s_max.
    # Enyhén konvex („lágyuló") alak, hogy grafikonnak kinézzen.
    fractions = cfg.ps_load_fractions                   # 0.05 ... 1.00
    ps_vals = []
    for f in fractions:
        # konvexitás: s ~ s_max * f^1.6  + kis zaj, majd a végén pontosan s_max
        val = s_max * (f ** 1.6)
        ps_vals.append(val)
    # a zajt úgy tesszük hozzá, hogy a monotonitás megmaradjon
    noisy = []
    prev = 0.0
    for v in ps_vals:
        v = max(prev, v + rng.uniform(-0.3, 0.3))
        noisy.append(v)
        prev = v
    # utolsó pont pontosan s_max
    noisy[-1] = s_max
    for key, v in zip(cfg.ps_keys, noisy):
        row[key] = round(v, 3)

    row["R_k"] = R_k
    row["s_max"] = s_max
    row["converged"] = True
    row["source"] = "smoke_fixture"
    return row


def main() -> None:
    cfg = load_config()
    rng = random.Random(SEED)

    # Oszlopsorrend = pontosan a DATA_CONTRACT.md szerint.
    fieldnames = (
        ["run_id"]
        + cfg.input_keys
        + ["R_k", "s_max"]
        + cfg.ps_keys
        + ["converged", "source"]
    )

    rows = [make_row(rng, cfg, i) for i in range(N_ROWS)]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✔ {len(rows)} smoke-sor kiírva → {OUT}")
    print(f"  Oszlopok ({len(fieldnames)}): {', '.join(fieldnames)}")
    print("  FIGYELEM: ezek NEM valódi eredmények (source=smoke_fixture).")


if __name__ == "__main__":
    main()
