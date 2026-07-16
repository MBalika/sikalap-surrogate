"""
plaxis/extract_results.py — eredmény-kiolvasás és p–s újramintavételezés.

A PLAXIS a terhelés–süllyedés görbét sok, EGYENETLENÜL elosztott pontban adja. A
tanításhoz minden futásból UGYANARRA a 20 rögzített teher-szintre (p/R_k = 0.05..1.00)
mintavételezzük újra a süllyedést — így a p–s pontok futások között összevethetők.

Ezt a helpert a valódi PLAXIS-backend és a mock is használja.
"""
from __future__ import annotations

import numpy as np


def resample_ps(
    loads: np.ndarray,
    settlements: np.ndarray,
    R_k: float,
    fractions: list[float],
) -> list[float]:
    """
    A (loads, settlements) görbét a p = frac·R_k teher-szintekre interpolálja.

    Args:
        loads       : monoton növekvő teher-értékek (kN/m), 0-tól R_k-ig.
        settlements : a hozzájuk tartozó süllyedések (mm), monoton növekvő.
        R_k         : törőteher (kN/m) — a teher-szintek ehhez skálázódnak.
        fractions   : teher-arányok (pl. 0.05 ... 1.00).
    Returns:
        20 süllyedés-érték (mm), az `fractions` teher-szinteken.
    """
    loads = np.asarray(loads, dtype=float)
    settlements = np.asarray(settlements, dtype=float)

    # Biztosítjuk a monoton növekvő loads-ot az interpolációhoz.
    order = np.argsort(loads)
    loads, settlements = loads[order], settlements[order]

    targets = np.array([f * R_k for f in fractions])
    # np.interp: a tartományon kívüli célt a szélső értékre vágja (bal 0, jobb s_max).
    s = np.interp(targets, loads, settlements)
    return [float(round(v, 3)) for v in s]
