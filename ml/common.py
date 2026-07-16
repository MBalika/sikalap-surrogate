"""
ml/common.py — közös segédek: config-betöltés és oszlopnevek.

Ez a modul az EGYETLEN hely, ahol a config.yaml-t beolvassuk, és ahonnan a
pipeline összes többi része megkapja a bemeneti/kimeneti oszlopneveket. Így ha a
config.yaml-ben átírsz egy nevet vagy tartományt, az egész rendszer követi.

Kezdő programozónak: a `Config` osztály egy „okos szótár" a beállítások köré.
Példa használat:
    from ml.common import load_config
    cfg = load_config()
    print(cfg.continuous_keys)   # ['B','D','phi','c','gamma','E','GWL','alpha']
    print(cfg.output_keys)       # ['R_k','s_max','ps_01',...,'ps_20']
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Windows-konzol UTF-8 kényszerítése: a magyar szövegek, a ° és a φ különben
# cp1250 alatt UnicodeEncodeError-t dobnának. Mivel MINDEN modul ezt importálja,
# elég itt egyszer beállítani. (Csak best-effort; ha nem megy, csendben kihagyja.)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

# A projekt gyökere: ez a fájl a  <gyökér>/ml/  alatt van, tehát két szint fel.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class Config:
    """A config.yaml betöltött tartalma + kényelmi property-k."""

    raw: dict[str, Any] = field(repr=False)

    # ---- Bemenetek -------------------------------------------------------
    @property
    def continuous(self) -> list[dict]:
        return self.raw["inputs"]["continuous"]

    @property
    def continuous_keys(self) -> list[str]:
        return [p["key"] for p in self.continuous]

    @property
    def categorical(self) -> list[dict]:
        return self.raw["inputs"].get("categorical", [])

    @property
    def soil_type_values(self) -> list[str]:
        for cat in self.categorical:
            if cat["key"] == "soil_type":
                return list(cat["values"])
        return []

    @property
    def input_keys(self) -> list[str]:
        """A 9 bemeneti oszlop neve, a config sorrendjében (folytonos + kategorikus)."""
        return self.continuous_keys + [c["key"] for c in self.categorical]

    def bounds(self, key: str) -> tuple[float, float]:
        """(min, max) egy folytonos paraméterhez."""
        for p in self.continuous:
            if p["key"] == key:
                return float(p["min"]), float(p["max"])
        raise KeyError(f"Nincs ilyen folytonos paraméter: {key!r}")

    # ---- Kimenetek -------------------------------------------------------
    @property
    def scalar_output_keys(self) -> list[str]:
        return [o["key"] for o in self.raw["outputs"]["scalars"]]

    @property
    def n_ps_points(self) -> int:
        return int(self.raw["outputs"]["ps_curve"]["n_points"])

    @property
    def ps_keys(self) -> list[str]:
        """A p–s görbe oszlopnevei: ps_01 ... ps_20 (mindig 2 számjegy, nullás)."""
        prefix = self.raw["outputs"]["ps_curve"]["key_prefix"]
        return [f"{prefix}{i:02d}" for i in range(1, self.n_ps_points + 1)]

    @property
    def ps_load_fractions(self) -> list[float]:
        """A p–s pontok teher-szintjei p/R_k arányban: 0.05, 0.10, ... 1.00."""
        ps = self.raw["outputs"]["ps_curve"]
        start = float(ps["load_fractions_start"])
        end = float(ps["load_fractions_end"])
        n = self.n_ps_points
        step = (end - start) / (n - 1)
        return [round(start + step * i, 6) for i in range(n)]

    @property
    def output_keys(self) -> list[str]:
        """Mind a 22 kimeneti oszlop: R_k, s_max, ps_01..ps_20."""
        return self.scalar_output_keys + self.ps_keys

    # ---- Talajtípusok ----------------------------------------------------
    def soil_params(self, soil_type: str) -> dict:
        try:
            return self.raw["soil_types"][soil_type]
        except KeyError:
            raise KeyError(
                f"Ismeretlen talajtípus: {soil_type!r}. "
                f"Engedélyezett: {self.soil_type_values}"
            )

    @property
    def hssmall_common(self) -> dict:
        return self.raw["hssmall_common"]

    # ---- ML / sampling ---------------------------------------------------
    @property
    def ml(self) -> dict:
        return self.raw["ml"]

    @property
    def sampling(self) -> dict:
        return self.raw["sampling"]


def load_config(path: str | Path | None = None) -> Config:
    """Beolvassa a config.yaml-t és visszaad egy Config objektumot."""
    p = Path(path) if path is not None else CONFIG_PATH
    if not p.exists():
        raise FileNotFoundError(f"Nem találom a config-ot: {p}")
    with p.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return Config(raw=raw)


# Kézi gyorsteszt:  py ml/common.py
if __name__ == "__main__":
    cfg = load_config()
    print("Bemenetek (9):", cfg.input_keys)
    print("Talajtípusok:", cfg.soil_type_values)
    print("Kimenetek (22):", cfg.output_keys)
    print("p–s teher-szintek:", cfg.ps_load_fractions)
    print("B tartomány:", cfg.bounds("B"))
