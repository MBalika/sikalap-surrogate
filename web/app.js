/* app.js — a surrogate oktatóeszköz vezérlője.
 *
 * Felhasznált globálisok (mind a <script>-ekből töltődik, szerver nélkül is):
 *   window.PLAXIS_MANIFEST  — bemenetek/kimenetek metaadata (models/bundle.js)
 *   window.PLAXIS_MODELS    — { "R_k": fn(input[]), ... } a 22 modell (bundle.js)
 *   window.PLAXIS_PARITY    — böngésző-önteszt esetek (models/parity_cases.js)
 *   window.EC7              — egyszerűsített zárt képlet (ec7.js)
 *   window.PSChart          — canvas p–s grafikon (chart.js)
 */
(function () {
  "use strict";

  var M = window.PLAXIS_MANIFEST;
  var MODELS = window.PLAXIS_MODELS;
  var state = {}; // aktuális csúszka-értékek + talajtípus
  var last = null; // utolsó számítás: {sur, R_k, s_max}
  var fieldState = { mode: "disp", loadFrac: 1 }; // metszet-nézet állapota

  // ---- Segédek --------------------------------------------------------------
  function fmt(x, d) {
    if (!isFinite(x)) return "–";
    return x.toLocaleString("hu-HU", { minimumFractionDigits: d, maximumFractionDigits: d });
  }

  function featureVector() {
    // A manifest.feature_order SORRENDJÉBEN építjük az input tömböt.
    return M.feature_order.map(function (k) {
      if (k.indexOf("soil_") === 0) {
        return state.soil_type === k.slice(5) ? 1 : 0;
      }
      return state[k];
    });
  }

  function predictAll() {
    var x = featureVector();
    var out = {};
    M.output_scalars.concat(M.output_ps).forEach(function (key) {
      out[key] = MODELS[key](x);
    });
    return out;
  }

  // p–s pontok a surrogate kimenetből, kumulatív-max clamppel (monotonitás),
  // mert a 20 modell egymástól függetlenül tanult.
  function psSeries(out, R_k) {
    var fr = M.ps_load_fractions;
    var pts = [];
    var prev = 0;
    for (var i = 0; i < M.output_ps.length; i++) {
      var s = Math.max(prev, out[M.output_ps[i]]);
      prev = s;
      pts.push({ p: fr[i] * R_k, s: s });
    }
    return pts;
  }

  // ---- Renderelés -----------------------------------------------------------
  function recompute() {
    var out = predictAll();
    var R_k = out.R_k;
    var s_max = out.s_max;

    // EC7 zárt képlet ugyanazokra a bemenetekre
    var inp = {};
    M.continuous_keys.forEach(function (k) { inp[k] = state[k]; });
    var ec7 = window.EC7.ec7BearingCapacity(inp);
    var diffPct = ec7.R_k ? ((R_k - ec7.R_k) / ec7.R_k) * 100 : NaN;

    document.getElementById("out_Rk").textContent = fmt(R_k, 0);
    document.getElementById("out_smax").textContent = fmt(s_max, 1);
    document.getElementById("out_ec7").textContent = fmt(ec7.R_k, 0);
    var d = document.getElementById("out_diff");
    d.textContent = (diffPct >= 0 ? "+" : "") + fmt(diffPct, 1) + " %";
    d.className = "kpi-val " + (Math.abs(diffPct) < 15 ? "ok" : "warn");

    var sur = psSeries(out, R_k);
    var series = [
      { label: "Surrogate (ML)", color: "#3b82f6", points: sur },
      // EC7 törőteher függőleges vonalként: a surrogate görbe végpontjának s-énél
      {
        label: "EC7 törőteher",
        color: "#ef4444",
        dashed: true,
        points: [{ p: ec7.R_k, s: 0 }, { p: ec7.R_k, s: sur.length ? sur[sur.length - 1].s : 0 }],
      },
    ];
    last = { sur: sur, R_k: R_k, s_max: s_max, series: series, ec7R: ec7.R_k };
    renderPS();
    redrawField();
    updateReadout();
  }

  // A p–s görbe kirajzolása az aktuális teher-szint pont-jelölőjével.
  function renderPS() {
    if (!last) return;
    var f = fieldState.loadFrac;
    var marker = {
      color: "#f59e0b", markerOnly: true, markerSize: 6,
      points: [{ p: f * last.R_k, s: settlementAtFrac(f) }],
    };
    window.PSChart.drawPS(document.getElementById("psCanvas"), last.series.concat([marker]));
  }

  // Az élő kijelző (teher / süllyedés / %) frissítése.
  function updateReadout() {
    if (!last) return;
    var f = fieldState.loadFrac;
    document.getElementById("ro_p").textContent = fmt(f * last.R_k, 0);
    document.getElementById("ro_s").textContent = fmt(settlementAtFrac(f), 1);
    document.getElementById("ro_pct").textContent = Math.round(f * 100) + " %";
  }

  // Egy teher-szint beállítása és MINDEN nézet frissítése (mező + p–s + kijelző).
  function setLoadFrac(f, fromSlider) {
    fieldState.loadFrac = Math.max(0, Math.min(1, f));
    var pct = Math.round(fieldState.loadFrac * 100);
    document.getElementById("loadVal").textContent = pct + " %";
    if (!fromSlider) document.getElementById("loadSlider").value = pct;
    redrawField();
    renderPS();
    updateReadout();
  }

  // Süllyedés tetszőleges teher-szinten (a p–s görbe lineáris interpolációja).
  function settlementAtFrac(f) {
    if (!last) return 0;
    var fr = M.ps_load_fractions;
    var s = last.sur.map(function (p) { return p.s; });
    if (f <= 0) return 0;
    if (f >= fr[fr.length - 1]) return s[s.length - 1];
    var prevF = 0, prevS = 0;
    for (var i = 0; i < fr.length; i++) {
      if (f <= fr[i]) {
        var t = (f - prevF) / (fr[i] - prevF || 1);
        return prevS + t * (s[i] - prevS);
      }
      prevF = fr[i]; prevS = s[i];
    }
    return s[s.length - 1];
  }

  function redrawField() {
    if (!last || !window.FieldViz) return;
    var f = fieldState.loadFrac;
    window.FieldViz.draw({
      canvas: document.getElementById("fieldCanvas"),
      B: state.B, D: state.D, phi: state.phi,
      mode: fieldState.mode, loadFrac: f,
      sCurrent: settlementAtFrac(f), sRef: last.s_max,
    });
  }

  // ---- Csúszkák építése -----------------------------------------------------
  function buildControls() {
    var wrap = document.getElementById("controls");
    M.inputs_meta.forEach(function (p) {
      var mid = (p.min + p.max) / 2;
      state[p.key] = Math.round(mid * 100) / 100;

      var row = document.createElement("div");
      row.className = "ctrl";
      var step = (p.max - p.min) / 100;

      row.innerHTML =
        '<label>' +
        '<span class="ctrl-name">' + p.jel + " — " + p.nev + "</span>" +
        '<output id="val_' + p.key + '" class="ctrl-val nowrap"></output>' +
        "</label>" +
        '<input type="range" id="sl_' + p.key + '" min="' + p.min +
        '" max="' + p.max + '" step="' + step + '" value="' + state[p.key] + '">' +
        '<div class="ctrl-range nowrap"><span>' + p.min + " " + p.egyseg +
        "</span><span>" + p.max + " " + p.egyseg + "</span></div>";
      wrap.appendChild(row);

      var sl = row.querySelector("input");
      var vo = row.querySelector("output");
      var unit = p.egyseg;
      function upd() {
        state[p.key] = parseFloat(sl.value);
        vo.textContent = fmt(state[p.key], step < 0.5 ? 2 : 1) + " " + unit;
        recompute();
      }
      sl.addEventListener("input", upd);
      vo.textContent = fmt(state[p.key], step < 0.5 ? 2 : 1) + " " + unit;
    });

    // Talajtípus-kapcsoló
    var soil = M.soil_meta;
    state.soil_type = soil.values[0];
    var srow = document.createElement("div");
    srow.className = "ctrl soil";
    var btns = soil.values
      .map(function (v, i) {
        return '<button type="button" class="soil-btn' + (i === 0 ? " active" : "") +
          '" data-v="' + v + '">' + v + "</button>";
      })
      .join("");
    srow.innerHTML = '<span class="ctrl-name">' + soil.jel + "</span>" +
      '<div class="soil-btns">' + btns + "</div>";
    wrap.appendChild(srow);
    srow.querySelectorAll(".soil-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        srow.querySelectorAll(".soil-btn").forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        state.soil_type = b.getAttribute("data-v");
        recompute();
      });
    });
  }

  // ---- Animáció: a törési folyamat lejátszása -------------------------------
  var anim = { playing: false, raf: 0, start: 0, dur: 7000 };
  function smoothstep(p) { return p * p * (3 - 2 * p); } // lassú start és lassú vég

  function stopAnim() {
    anim.playing = false;
    if (anim.raf) cancelAnimationFrame(anim.raf);
    anim.raf = 0;
    var b = document.getElementById("playBtn");
    b.classList.remove("playing");
    b.textContent = "▶ Törési folyamat lejátszása";
  }

  function playAnim() {
    if (anim.playing) { stopAnim(); return; }
    // ha a végén állunk, kezdjük elölről
    if (fieldState.loadFrac >= 0.999) setLoadFrac(0, false);
    anim.playing = true;
    anim.start = 0;
    var b = document.getElementById("playBtn");
    b.classList.add("playing");
    b.textContent = "⏸ Szünet";
    var frac0 = fieldState.loadFrac;
    function step(ts) {
      if (!anim.playing) return;
      if (!anim.start) anim.start = ts;
      var p = frac0 + (ts - anim.start) / anim.dur; // haladás (0..1), a jelenlegi állásból
      if (p >= 1) { setLoadFrac(1, false); stopAnim(); return; }
      setLoadFrac(smoothstep(p), false);
      anim.raf = requestAnimationFrame(step);
    }
    anim.raf = requestAnimationFrame(step);
  }

  // ---- Metszet-vezérlők -----------------------------------------------------
  function wireFieldControls() {
    var fm = document.getElementById("fieldMode");
    fm.querySelectorAll(".seg-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        fm.querySelectorAll(".seg-btn").forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        fieldState.mode = b.getAttribute("data-mode");
        redrawField(); // csak a mező-nézet vált, a teher marad
      });
    });

    var ls = document.getElementById("loadSlider");
    ls.addEventListener("input", function () {
      stopAnim(); // kézi állításnál megáll az animáció
      setLoadFrac(parseInt(ls.value, 10) / 100, true);
    });

    document.getElementById("playBtn").addEventListener("click", playAnim);
    document.getElementById("resetBtn").addEventListener("click", function () {
      stopAnim();
      setLoadFrac(0, false);
    });
  }

  // ---- Böngésző-önteszt (paritás) ------------------------------------------
  function browserSelfTest() {
    var badge = document.getElementById("selftest");
    if (!window.PLAXIS_PARITY) { badge.textContent = "önteszt: nincs adat"; return; }
    var P = window.PLAXIS_PARITY;
    var maxRel = 0;
    var keys = Object.keys(P.expected);
    P.cases.forEach(function (x, ci) {
      keys.forEach(function (key) {
        var got = MODELS[key](x);
        var exp = P.expected[key][ci];
        var rel = Math.abs(got - exp) / Math.max(Math.abs(exp), 1e-9);
        if (rel > maxRel) maxRel = rel;
      });
    });
    var ok = maxRel < 1e-3;
    badge.textContent = (ok ? "✔ böngésző-paritás OK" : "✗ paritás hiba") +
      " (max eltérés " + maxRel.toExponential(1) + ")";
    badge.className = "selftest " + (ok ? "ok" : "warn");
  }

  // ---- Indítás --------------------------------------------------------------
  function init() {
    if (!M || !MODELS) {
      document.getElementById("controls").textContent =
        "Hiba: a modell-bundle nem töltődött be (web/models/bundle.js).";
      return;
    }
    buildControls();
    wireFieldControls();
    browserSelfTest();
    recompute();
    // téma-váltásnál újrarajzol
    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", recompute);
    }
    window.addEventListener("resize", recompute);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
