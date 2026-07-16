"""
plaxis/run_generation.py — az adatgeneráló hurok.

Végigmegy a doe.csv sorain, mindegyikre származtatja a HSsmall-készletet, lefuttatja
a választott backendet (mock vagy real), és a DATA_CONTRACT.md szerinti fejléccel
kiírja a plaxis_results.csv-t.

Robusztusság:
  - checkpoint/resume: ha a kimenet már létezik, a kész run_id-ket kihagyja,
  - részeredmény-append: minden sikeres futás AZONNAL a fájlba kerül (nem vész el),
  - nem-konvergáló / hibás futások logolva és kihagyva (converged=False nem tanít).

Futtatás:
  py plaxis/run_generation.py --api mock                 # teljes doe.csv mockkal
  py plaxis/run_generation.py --api mock --limit 20      # csak az első 20
  py plaxis/run_generation.py --api real                 # valódi PLAXIS (ha bekötve)
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.common import load_config  # noqa: E402
from plaxis.derive_hssmall import derive_hssmall  # noqa: E402
from plaxis.plaxis_api import get_backend  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DOE = RAW_DIR / "doe.csv"
OUT = RAW_DIR / "plaxis_results.csv"


def _completed_run_ids(out_path: Path) -> set[int]:
    if not out_path.exists():
        return set()
    try:
        done = pd.read_csv(out_path, usecols=["run_id"])
        return set(done["run_id"].astype(int).tolist())
    except Exception:
        return set()


def main() -> None:
    ap = argparse.ArgumentParser(description="PLAXIS adatgeneráló hurok")
    ap.add_argument("--api", choices=["mock", "real"], default="mock")
    ap.add_argument("--limit", type=int, default=None, help="legfeljebb ennyi ÚJ futás")
    ap.add_argument("--doe", type=str, default=str(DOE))
    args = ap.parse_args()

    cfg = load_config()
    backend = get_backend(args.api)

    doe_path = Path(args.doe)
    if not doe_path.exists():
        raise FileNotFoundError(f"Nincs kísérlet-terv: {doe_path}. Futtasd: py plaxis/sampling.py")
    doe = pd.read_csv(doe_path)

    fieldnames = (
        ["run_id"] + cfg.input_keys + ["R_k", "s_max"] + cfg.ps_keys + ["converged", "source"]
    )

    done = _completed_run_ids(OUT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_header = not OUT.exists()

    n_ok = n_skip = n_fail = 0
    with OUT.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for _, r in doe.iterrows():
            rid = int(r["run_id"])
            if rid in done:
                n_skip += 1
                continue
            if args.limit is not None and n_ok + n_fail >= args.limit:
                break

            try:
                hs = derive_hssmall(
                    phi=float(r["phi"]), c=float(r["c"]), gamma=float(r["gamma"]),
                    E=float(r["E"]), soil_type=str(r["soil_type"]), cfg=cfg,
                )
                res = backend.simulate(r.to_dict(), hs, cfg)
            except NotImplementedError as e:
                print(f"⚠  A(z) '{args.api}' backend nincs bekötve:\n{e}")
                return
            except Exception as e:  # noqa: BLE001 — egy futás hibája ne állítsa le a kört
                print(f"  ✗ run_id={rid} hiba: {e}")
                n_fail += 1
                continue

            if not res.get("converged", False):
                print(f"  ⚠ run_id={rid} nem konvergált — kihagyva")
                n_fail += 1
                continue

            row = {"run_id": rid}
            for k in cfg.input_keys:
                row[k] = r[k]
            row.update({k: res[k] for k in (["R_k", "s_max"] + cfg.ps_keys)})
            row["converged"] = True
            row["source"] = res["source"]
            writer.writerow(row)
            fh.flush()                                  # azonnal lemezre (resume-biztos)
            n_ok += 1

    print(f"\n✔ Kész. Új sikeres: {n_ok}, kihagyott (már kész): {n_skip}, hibás: {n_fail}")
    print(f"  Eredmény → {OUT}")
    if n_ok:
        print(f"  Tanításhoz:  py ml/train_xgb.py   (a runner kimenetére mutatva)")


if __name__ == "__main__":
    main()
