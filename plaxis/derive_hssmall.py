"""
plaxis/derive_hssmall.py — a HSsmall korrelációs kaszkád.

A 9 bemenetből (8 folytonos + talajtípus) DETERMINISZTIKUSAN előállítja a teljes
PLAXIS HSsmall paraméterkészletet. A surrogate inputtere 9 dimenziós marad — ezt
a kibővített készletet csak a PLAXIS-modell látja, a betanított modell nem.

A típusonkénti alapértékek (m, γ0.7, Eoed/E50 arány, G0/Gur, dilatancia) a
config.yaml `soil_types` blokkjából jönnek — így egy helyen hangolhatók.

Források:
  ψ  = max(φ'−30°, 0)          Bolton (csak súrlódó talajra; iszap/agyag ψ≈0)
  K0 = 1 − sin(φ')             Jáky (normálisan konszolidált)
  E50ref                       = a bemeneti E' (definíció szerint, @100 kPa)
  Eoedref = ratio · E50ref     típusfüggő arány
  Euref   = ratio · E50ref     ≈ 3·E50ref
  m                            típusfüggő feszültség-kitevő (Janbu/HS)
  G0ref   = (G0/Gur) · Gur     Benz (2007);  Gur = Euref / (2·(1+ν_ur))
  γ0.7                         típusfüggő small-strain referencia-alakváltozás
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

# A common.py-t a projektgyökérből importáljuk. Ha közvetlenül futtatod ezt a
# fájlt (py plaxis/derive_hssmall.py), a lenti sys.path-trükk gondoskodik róla.
try:
    from ml.common import load_config, Config
except ModuleNotFoundError:  # közvetlen futtatás a plaxis/ mappából
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ml.common import load_config, Config


@dataclass
class HSsmallSet:
    """Egy teljes HSsmall paraméterkészlet (egy talajréteg)."""
    # Szilárdság
    phi: float          # ° — belső súrlódási szög
    c: float            # kPa — kohézió
    psi: float          # ° — dilatancia
    # Merevség (mind kPa-ban, hogy a PLAXIS-nak közvetlenül átadható legyen)
    E50ref: float
    Eoedref: float
    Euref: float
    m: float            # feszültség-kitevő
    G0ref: float
    gamma07: float      # nyírási referencia-alakváltozás (dimenziótlan)
    # Egyéb
    nu_ur: float
    Rf: float
    K0nc: float
    p_ref: float        # kPa
    gamma: float        # kN/m³ — térfogatsúly (a bemenetből, változatlan)

    def as_dict(self) -> dict:
        return asdict(self)


def derive_hssmall(
    *,
    phi: float,
    c: float,
    gamma: float,
    E: float,
    soil_type: str,
    cfg: Config | None = None,
) -> HSsmallSet:
    """
    A 4 talaj-bemenetből (φ', c', γ, E') + a talajtípusból a teljes HSsmall-készlet.

    Megjegyzés: B, D, GWL, α geometriai/terhelési bemenetek — azok NEM a
    talajkészletbe, hanem a PLAXIS-modell geometriájába/terhelésébe mennek, ezért
    itt nem szerepelnek.

    Paraméterek:
        phi   : belső súrlódási szög [°]
        c     : kohézió [kPa]
        gamma : térfogatsúly [kN/m³]
        E     : E' = E50ref [MPa]  ← FIGYELEM: MPa-ban jön, itt kPa-ra váltjuk
        soil_type : 'homok' | 'iszap' | 'agyag'
    """
    if cfg is None:
        cfg = load_config()

    sp = cfg.soil_params(soil_type)          # típusfüggő arányok
    common = cfg.hssmall_common
    p_ref = float(common["p_ref"])           # kPa

    # --- Merevségek (MPa → kPa) ---
    E50ref = E * 1000.0                       # MPa → kPa
    Eoedref = sp["Eoed_over_E50"] * E50ref
    Euref = sp["Eur_over_E50"] * E50ref

    nu_ur = float(sp["nu_ur"])
    # Gur a rugalmas terhelés-tehermentesítés nyírómodulusa:
    Gur = Euref / (2.0 * (1.0 + nu_ur))
    G0ref = sp["G0_over_Gur"] * Gur

    # --- Szilárdság / dilatancia ---
    psi = max(phi - 30.0, 0.0) if sp["dilatancy_from_phi"] else 0.0

    # --- K0 (Jáky, NC) ---
    K0nc = 1.0 - math.sin(math.radians(phi))

    return HSsmallSet(
        phi=phi,
        c=c,
        psi=psi,
        E50ref=E50ref,
        Eoedref=Eoedref,
        Euref=Euref,
        m=float(sp["m"]),
        G0ref=G0ref,
        gamma07=float(sp["gamma07"]),
        nu_ur=nu_ur,
        Rf=float(sp["Rf"]),
        K0nc=K0nc,
        p_ref=p_ref,
        gamma=gamma,
    )


# Kézi gyorsteszt:  py plaxis/derive_hssmall.py
if __name__ == "__main__":
    cfg = load_config()
    for st in cfg.soil_type_values:
        hs = derive_hssmall(phi=30.0, c=10.0, gamma=19.0, E=20.0, soil_type=st, cfg=cfg)
        print(f"\n=== {st} (φ'=30°, c'=10 kPa, E'=20 MPa) ===")
        for k, v in hs.as_dict().items():
            print(f"  {k:10s} = {v:.4g}")
