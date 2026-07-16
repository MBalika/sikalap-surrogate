/* chart.js — pehelysúlyú canvas p–s grafikon (külső könyvtár nélkül).
 *
 * A terhelés–süllyedés görbét rajzolja: X = teher p (kN/m), Y = süllyedés s (mm),
 * lefelé növekvő (geotechnikai konvenció). Több sorozatot is tud (surrogate + EC7).
 */
(function () {
  "use strict";

  function niceCeil(x) {
    if (x <= 0) return 1;
    var exp = Math.floor(Math.log10(x));
    var base = Math.pow(10, exp);
    var f = x / base;
    var nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
    return nf * base;
  }

  /* series: [{label, color, points:[{p,s}], dashed?}]  */
  function drawPS(canvas, series) {
    var dpr = window.devicePixelRatio || 1;
    var cssW = canvas.clientWidth || 600;
    var cssH = canvas.clientHeight || 380;
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    var isDark = document.documentElement.getAttribute("data-theme") === "dark" ||
      (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches &&
        document.documentElement.getAttribute("data-theme") !== "light");
    var ink = isDark ? "#e7e9ee" : "#1b2330";
    var grid = isDark ? "rgba(255,255,255,.12)" : "rgba(20,30,50,.10)";
    var axisCol = isDark ? "rgba(255,255,255,.35)" : "rgba(20,30,50,.35)";

    var m = { l: 56, r: 16, t: 16, b: 44 };
    var W = cssW - m.l - m.r;
    var H = cssH - m.t - m.b;

    var maxP = 0, maxS = 0;
    series.forEach(function (se) {
      se.points.forEach(function (pt) {
        if (pt.p > maxP) maxP = pt.p;
        if (pt.s > maxS) maxS = pt.s;
      });
    });
    maxP = niceCeil(maxP || 1);
    maxS = niceCeil(maxS || 1);

    var xOf = function (p) { return m.l + (p / maxP) * W; };
    var yOf = function (s) { return m.t + (s / maxS) * H; }; // lefelé nő

    // rács + tengelycímkék
    ctx.font = "12px system-ui, sans-serif";
    ctx.fillStyle = ink;
    ctx.strokeStyle = grid;
    ctx.lineWidth = 1;
    var nx = 5, ny = 5, i;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (i = 0; i <= nx; i++) {
      var px = m.l + (i / nx) * W;
      ctx.beginPath(); ctx.moveTo(px, m.t); ctx.lineTo(px, m.t + H); ctx.stroke();
      ctx.fillText(Math.round((i / nx) * maxP), px, m.t + H + 6);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (i = 0; i <= ny; i++) {
      var py = m.t + (i / ny) * H;
      ctx.beginPath(); ctx.moveTo(m.l, py); ctx.lineTo(m.l + W, py); ctx.stroke();
      ctx.fillText(Math.round((i / ny) * maxS), m.l - 8, py);
    }

    // tengelyek
    ctx.strokeStyle = axisCol;
    ctx.beginPath();
    ctx.moveTo(m.l, m.t); ctx.lineTo(m.l, m.t + H); ctx.lineTo(m.l + W, m.t + H);
    ctx.stroke();

    // tengelyfeliratok
    ctx.fillStyle = ink;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText("p  [kN/m]", m.l + W / 2, cssH - 4);
    ctx.save();
    ctx.translate(14, m.t + H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = "top";
    ctx.fillText("s  [mm]", 0, 0);
    ctx.restore();

    // sorozatok
    series.forEach(function (se) {
      if (!se.points.length) return;

      // kiemelt egyetlen pont-jelölő (pl. az aktuális teher animáció közben)
      if (se.markerOnly) {
        var pt0 = se.points[0];
        var mx = xOf(pt0.p), my = yOf(pt0.s);
        ctx.fillStyle = se.color;
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(mx, my, se.markerSize || 6, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
        return;
      }

      ctx.strokeStyle = se.color;
      ctx.lineWidth = 2.2;
      ctx.setLineDash(se.dashed ? [6, 5] : []);
      ctx.beginPath();
      se.points.forEach(function (pt, k) {
        var X = xOf(pt.p), Y = yOf(pt.s);
        if (k === 0) ctx.moveTo(X, Y); else ctx.lineTo(X, Y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
      // pontok
      ctx.fillStyle = se.color;
      se.points.forEach(function (pt) {
        ctx.beginPath();
        ctx.arc(xOf(pt.p), yOf(pt.s), 2.6, 0, 2 * Math.PI);
        ctx.fill();
      });
    });
  }

  window.PSChart = { drawPS: drawPS };
})();
