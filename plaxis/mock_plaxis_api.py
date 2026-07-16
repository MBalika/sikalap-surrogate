"""
plaxis/mock_plaxis_api.py — hamis PLAXIS-backend a csővezeték teszteléséhez.

⚠ FONTOS: az itt számolt értékek NEM valódi PLAXIS-eredmények és NEM helyettesítik
a végeselemes számítást. Céljuk kizárólag, hogy a hurok (sampling → runner →
extract → ML → export → web) PLAXIS NÉLKÜL is végigfusson, és a ML-pipeline valódi,
bemenet-érzékeny jelen legyen tesztelhető. Minden sor `source = "mock_plaxis"`.

A képletek szándékosan egyszerűek (drénezett strip-alap teherbírás + hiperbolikus
p–s), hogy a bemenetekkel monoton, tanulható kapcsolatuk legyen — de fizikailag
csak nagyságrendileg hihetők.
"""
from __future__ import annotations

import math

import numpy as np

from plaxis.derive_hssmall import HSsmallSet
from plaxis.extract_results import resample_ps


def _bearing_factors(phi_deg: float) -> tuple[float, float, float]:
    """Nc, Nq, Nγ  (Vesic-féle közelítés) — drénezett strip-alap."""
    phi = math.radians(phi_deg)
    if phi_deg < 1e-6:
        Nq = 1.0
        Nc = 5.14
    else:
        Nq = math.exp(math.pi * math.tan(phi)) * (math.tan(math.radians(45 + phi_deg / 2)) ** 2)
        Nc = (Nq - 1.0) / math.tan(phi)
    Ng = 2.0 * (Nq + 1.0) * math.tan(phi)      # Vesic
    return Nc, Nq, Ng


class MockPlaxisBackend:
    """Hamis, de bemenet-érzékeny backend a plumbing-hoz."""

    name = "mock_plaxis"

    def simulate(self, case: dict, hs: HSsmallSet, cfg) -> dict:
        B = float(case["B"])
        D = float(case["D"])
        phi = float(case["phi"])
        c = float(case["c"])
        gamma = float(case["gamma"])
        E = float(case["E"])          # MPa
        GWL = float(case["GWL"])
        alpha = float(case["alpha"])  # °

        # --- Effektív térfogatsúly a vízszint miatt (durva) ---
        gamma_eff = gamma if GWL >= D + B else max(gamma - 10.0, 6.0)  # víz alatt ~-10 kN/m³

        Nc, Nq, Ng = _bearing_factors(phi)
        q = gamma * D                                   # felszíni teher (kPa)

        # --- Ferdeségi redukció (egyszerű i-faktor) ---
        i = max(1.0 - alpha / 90.0, 0.05) ** 2

        # q_ult (kPa), strip:
        q_ult = (c * Nc + q * Nq + 0.5 * gamma_eff * B * Ng) * i

        # R_k = a törőteher FÜGGŐLEGES komponense, folyóméterre (kN/m):
        # q_ult a talpra merőleges átlagos feszültség; strip szélessége B.
        R_k = q_ult * B

        # --- p–s görbe: NORMÁLT hiperbolikus (Duncan–Chang jellegű lágyulással) ---
        # 1) a törésnél várható süllyedés durva rugalmas becslése, reális sávba vágva:
        E_kpa = E * 1000.0
        s_ref = q_ult * B / E_kpa * 1000.0 * 0.5        # mm nagyságrend
        s_ref = float(np.clip(s_ref, 3.0, 100.0))       # tartsuk 3–100 mm közt

        # 2) a görbe ALAKJA hiperbolikus, úgy normálva, hogy s(p=R_k) = s_ref:
        Rf = hs.Rf
        n_dense = 200
        p = np.linspace(0.0, R_k, n_dense)
        frac = np.clip(p / R_k, 0.0, 1.0)
        shape = frac / (1.0 - Rf * frac)                # 0 → 1/(1-Rf)
        shape_max = 1.0 / (1.0 - Rf)
        s = s_ref * shape / shape_max                   # 0 → s_ref, monoton, lágyuló

        fractions = cfg.ps_load_fractions
        ps = resample_ps(p, s, R_k, fractions)
        s_max = ps[-1]

        result = {
            "R_k": float(round(R_k, 1)),
            "s_max": float(round(s_max, 2)),
            "converged": True,
            "source": "mock_plaxis",
        }
        for key, val in zip(cfg.ps_keys, ps):
            result[key] = float(val)
        return result
