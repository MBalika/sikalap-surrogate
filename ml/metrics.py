"""
ml/metrics.py — egyszerű regressziós metrikák.

A geotechnikában nem elég a statisztikai pontosság, de az alap-metrikák (R², RMSE,
MAE) a modellfejlesztés minimuma. Ezek stdlib + numpy alapúak.
"""
from __future__ import annotations

import numpy as np


def rmse(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def r2(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0.0:
        return float("nan")  # konstans célváltozó — R² nem értelmezett
    return float(1.0 - ss_res / ss_tot)


def summary(y_true, y_pred) -> dict[str, float]:
    """A három fő metrika egy szótárban."""
    return {"R2": r2(y_true, y_pred), "RMSE": rmse(y_true, y_pred), "MAE": mae(y_true, y_pred)}
