"""
plaxis/plaxis_api.py — a PLAXIS-backend absztrakciója.

A hurok (run_generation.py) NEM tudja, valódi PLAXIS-szal vagy mockkal fut-e — csak
a `PlaxisBackend.simulate(...)` metódust hívja. Így a teljes csővezeték PLAXIS
NÉLKÜL végigtesztelhető, a hallgató gépén pedig egyetlen kapcsoló (`--api real`) a
különbség.

A valódi backend (RealPlaxisBackend) a `plxscripting` Remote Scripting-et használja;
ez a modul azt CSAK vázként tartalmazza — a tulajdonságneveket a hallgató a ti
PLAXIS-verziótokban validálja (lásd docs/PLAXIS_TEMPLATE.md).
"""
from __future__ import annotations

from typing import Protocol

from plaxis.derive_hssmall import HSsmallSet


class PlaxisBackend(Protocol):
    """A hurok által elvárt szerződés. Bármely backend ezt teljesíti."""

    name: str

    def simulate(self, case: dict, hs: HSsmallSet, cfg) -> dict:
        """
        Egy esetet lefuttat és visszaadja az eredményt.

        Args:
            case : egy doe.csv sor szótárként (run_id, B, D, phi, ..., soil_type).
            hs   : a származtatott HSsmall-készlet (derive_hssmall).
            cfg  : a betöltött Config.
        Returns:
            dict a következő kulcsokkal:
              R_k (float, kN/m), s_max (float, mm),
              ps_01..ps_20 (float, mm), converged (bool), source (str).
        """
        ...


def get_backend(kind: str):
    """Backend-gyár. kind: 'mock' | 'real'."""
    if kind == "mock":
        from plaxis.mock_plaxis_api import MockPlaxisBackend
        return MockPlaxisBackend()
    if kind == "real":
        return RealPlaxisBackend()
    raise ValueError(f"Ismeretlen backend: {kind!r} (várt: 'mock' vagy 'real')")


class RealPlaxisBackend:
    """
    VÁZ — a valódi PLAXIS Remote Scripting backend.

    A hallgató tölti fel élettel a ti PLAXIS-verziótokban. A lépések vázlata a
    `simulate`-ben kommentként adott. Amíg nincs kész, NotImplementedError-t dob,
    hogy sose keverjük össze mock-adattal.
    """

    name = "real"

    def __init__(self) -> None:
        # Itt jön majd: from plxscripting.easy import new_server; s_i, g_i = new_server(...)
        self._connected = False

    def simulate(self, case: dict, hs: HSsmallSet, cfg) -> dict:
        raise NotImplementedError(
            "A RealPlaxisBackend még nincs bekötve. Lásd docs/PLAXIS_TEMPLATE.md.\n"
            "Lépések: sablon megnyit → 8 input + derive_hssmall felülír → geometria+GWL\n"
            "→ hálóz → K0 → terhelés (H/V=tanα) törésig → curve point kiolvas → resample_ps."
        )
