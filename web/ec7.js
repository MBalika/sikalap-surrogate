/* ec7.js — egyszerűsített, EC7-jellegű zárt képlet a törőteherre (kN/m).
 *
 * Ez a böngészőben futó "referenciagörbe" a surrogate MELLETT: drénezett
 * strip-alap teherbírás Vesic-féle Nc, Nq, Nγ tényezőkkel + egyszerű ferdeségi
 * és vízszint-korrekcióval. Szándékosan ugyanaz a modell, mint a mock-PLAXIS, hogy
 * a demóban a ML-görbe és a képlet nagyságrendileg egyezzen.
 *
 * FIGYELEM: ez EGYSZERŰSÍTETT képlet, nem a teljes EC7-eljárás. A projekt későbbi
 * fázisában ide portoljuk a meglévő, teljes EC7-motort
 * (sikalapok-teherbiras/index.html).
 */
(function () {
  "use strict";

  function bearingFactors(phiDeg) {
    var phi = (phiDeg * Math.PI) / 180;
    var Nq, Nc;
    if (phiDeg < 1e-6) {
      Nq = 1.0;
      Nc = 5.14;
    } else {
      Nq =
        Math.exp(Math.PI * Math.tan(phi)) *
        Math.pow(Math.tan((Math.PI / 180) * (45 + phiDeg / 2)), 2);
      Nc = (Nq - 1.0) / Math.tan(phi);
    }
    var Ng = 2.0 * (Nq + 1.0) * Math.tan(phi); // Vesic
    return { Nc: Nc, Nq: Nq, Ng: Ng };
  }

  /* inp: {B,D,phi,c,gamma,E,GWL,alpha}  → { R_k (kN/m), q_ult (kPa) } */
  function ec7BearingCapacity(inp) {
    var f = bearingFactors(inp.phi);
    var q = inp.gamma * inp.D;
    var gammaEff = inp.GWL >= inp.D + inp.B ? inp.gamma : Math.max(inp.gamma - 10.0, 6.0);
    var i = Math.pow(Math.max(1.0 - inp.alpha / 90.0, 0.05), 2);
    var qUlt = (inp.c * f.Nc + q * f.Nq + 0.5 * gammaEff * inp.B * f.Ng) * i;
    return { R_k: qUlt * inp.B, q_ult: qUlt };
  }

  window.EC7 = { bearingFactors: bearingFactors, ec7BearingCapacity: ec7BearingCapacity };
})();
