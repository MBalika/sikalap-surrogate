# 📄 ADATSZERZŐDÉS (DATA_CONTRACT)

> **Ez a fájl rögzíti a CSV-k pontos formátumát.** A smoke-fixture és a valódi
> PLAXIS-eredmény **bitre azonos fejlécű** — így a valódi adat érkezésekor a
> fixture egyszerűen kicserélhető (drop-in), a pipeline egy sort sem változik.
>
> Az oszlopnevek forrása a [`config.yaml`](config.yaml). Kézzel itt NE térj el tőle.

---

## 1. `doe.csv` — a kísérlet-terv (sampling.py írja)

Egy sor = egy tervezett PLAXIS-futás. A 9 bemenet + egy futás-azonosító.

| oszlop | típus | egység | leírás |
|--------|-------|--------|--------|
| `run_id` | int | – | 0-tól növekvő, egyedi futásazonosító |
| `B` | float | m | alapszélesség |
| `D` | float | m | alapsík mélysége |
| `phi` | float | ° | belső súrlódási szög φ' |
| `c` | float | kPa | kohézió c' |
| `gamma` | float | kN/m³ | térfogatsúly |
| `E` | float | MPa | E' = E₅₀ʳᵉᶠ @100 kPa |
| `GWL` | float | m | talajvízszint mélysége |
| `alpha` | float | ° | teherferdeség |
| `soil_type` | str | – | `homok` \| `iszap` \| `agyag` |

## 2. `doe_hssmall.csv` — audit (derive_hssmall.py írja)

A `doe.csv` + a belőle **determinisztikusan** származtatott teljes HSsmall-készlet
(ψ, K0nc, E50ref, Eoedref, Euref, m, G0ref, γ0.7, ν_ur, Rf, p_ref). Csak
átláthatóság/ellenőrzés céljából — a surrogate ezt **nem** látja.

## 3. `plaxis_results.csv` — a nyers eredmény (extract_results.py írja)

A `doe.csv` minden sikeres futásához az eredmény. **Ez a tanítóhalmaz.**

| oszlop | típus | egység | leírás |
|--------|-------|--------|--------|
| `run_id` | int | – | kulcs a `doe.csv`-hez |
| *(a 9 bemenet ismét, ellenőrzésre)* | | | `B,D,phi,c,gamma,E,GWL,alpha,soil_type` |
| `R_k` | float | kN/m | törőteher függőleges komponense |
| `s_max` | float | mm | süllyedés a törésnél |
| `ps_01` … `ps_20` | float | mm | p–s görbe süllyedései a 20 rögzített teher-szinten |
| `converged` | bool | – | `True`, ha a futás konvergált (csak ezek tanítanak) |
| `source` | str | – | `plaxis_real` \| `smoke_fixture` |

**Teher-szintek:** `ps_i` a `p/R_k = 0.05·i` (i = 1..20) teher-szinthez tartozó
süllyedés. Tehát `ps_20` ≡ `s_max`.

---

## 🔒 Tudományos integritás

- A **valódi** modell **kizárólag** `source = plaxis_real` sorokból tanulhat.
- A `smoke_fixture` sorok **nem fizikaiak** — csak a pipeline (betöltés →
  tanítás → export → web) végigfuttatására valók. A tanításból éles használatnál
  ki kell szűrni őket (`source == "plaxis_real"`).
- Lásd: [`docs/SCIENTIFIC_INTEGRITY.md`](docs/SCIENTIFIC_INTEGRITY.md).
