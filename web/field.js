/* field.js — illusztratív metszeti mező-vizualizáció (PLAXIS-szerű).
 *
 * ⚠ SZEMLÉLTETÉS, NEM valódi végeselemes mező. Két nézet:
 *   - 'disp'  : elmozdulás- (süllyedés-) hagyma — a felszíni értéket a surrogate
 *               p–s görbéje adja az aktuális teher-szinten.
 *   - 'shear' : inkrementális nyírásalakváltozás — a klasszikus Prandtl-féle
 *               törőmechanizmus (aktív ék + radiális nyírózóna + passzív ékek),
 *               ami a törés közeledtével "kigyullad".
 *
 * A geometria VALÓS: B (alapszélesség) és D (alapsík mélység) méretarányosan.
 * A valódi ROM-mezőre később kódtörés nélkül átválthatunk (ugyanaz a rajzoló API).
 */
(function () {
  "use strict";

  // --- Színskála: klasszikus FE-szivárvány (kék=kicsi → piros=nagy) ---
  var STOPS = [
    [0.0, [30, 60, 150]],
    [0.25, [40, 170, 200]],
    [0.5, [70, 190, 90]],
    [0.72, [240, 210, 60]],
    [1.0, [210, 55, 45]],
  ];
  function ramp(t) {
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    for (var i = 1; i < STOPS.length; i++) {
      if (t <= STOPS[i][0]) {
        var a = STOPS[i - 1], b = STOPS[i];
        var f = (t - a[0]) / (b[0] - a[0] || 1);
        return [
          Math.round(a[1][0] + f * (b[1][0] - a[1][0])),
          Math.round(a[1][1] + f * (b[1][1] - a[1][1])),
          Math.round(a[1][2] + f * (b[1][2] - a[1][2])),
        ];
      }
    }
    return STOPS[STOPS.length - 1][1];
  }

  var DEG = Math.PI / 180;

  // --- A Prandtl-törőmechanizmus vázpontjai (nyíráshoz) ---
  // Visszaad egy pontlistát [x,z] (méter), amely mentén a nyírás koncentrálódik.
  // Robusztus, kvadratikus Bézier-alapú konstrukció (nem érzékeny a trig-előjelekre):
  //   - aktív "V" ék: mindkét alap-él → közös apex az alap alatt,
  //   - két külső törőfelület: az élektől lefelé-kifelé ívelve a felszínig.
  function slipSkeleton(B, D, phi) {
    var a = B / 2;
    var actHalf = (45 + phi / 2) * DEG;         // aktív ék dőlése
    var apexZ = D + a * Math.tan(actHalf);       // az ék csúcsa az alap alatt
    var pts = [];
    function line(x0, z0, x1, z1, n) {
      for (var i = 0; i <= n; i++) {
        var t = i / n;
        pts.push([x0 + (x1 - x0) * t, z0 + (z1 - z0) * t]);
      }
    }
    function quad(x0, z0, cx, cz, x1, z1, n) {  // kvadratikus Bézier
      for (var i = 0; i <= n; i++) {
        var t = i / n, u = 1 - t;
        pts.push([
          u * u * x0 + 2 * u * t * cx + t * t * x1,
          u * u * z0 + 2 * u * t * cz + t * t * z1,
        ]);
      }
    }

    // a törőfelület kifutása a felszínen és mélysége (φ-vel nő)
    var reach = a + 0.9 * a + 0.6 * D + apexZ * 0.4;
    var bulge = apexZ + 0.5 * a;                 // az ív legmélyebb pontja

    for (var side = -1; side <= 1; side += 2) {
      var ex = side * a;
      // 1) aktív ék: él → apex
      line(ex, D, 0, apexZ, 22);
      // 2) külső törőfelület: él → (lefelé-kifelé ívelve) → felszíni kifutás
      quad(ex, D, side * (a + 0.4 * reach), bulge, side * reach, 0.0, 40);
    }
    return pts;
  }

  /* opts: {canvas, B, D, phi, mode:'disp'|'shear', loadFrac(0..1),
            sCurrent(mm), sRef(mm)} */
  function draw(opts) {
    var canvas = opts.canvas;
    var B = opts.B, D = opts.D, phi = opts.phi;
    var mode = opts.mode || "disp";
    var lf = Math.max(0, Math.min(1, opts.loadFrac));

    var dpr = window.devicePixelRatio || 1;
    var cssW = canvas.clientWidth || 640;
    var cssH = canvas.clientHeight || 380;
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    var isDark =
      document.documentElement.getAttribute("data-theme") === "dark" ||
      (window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches &&
        document.documentElement.getAttribute("data-theme") !== "light");
    var ink = isDark ? "#e7e9ee" : "#1b2330";
    var line = isDark ? "rgba(255,255,255,.5)" : "rgba(20,30,50,.6)";

    // --- világ-tartomány (méter) ---
    var Xhalf = Math.max(3 * B, B / 2 + 2.5 * B, 3);
    var Zdepth = D + Math.max(3.2 * B, 4);
    var m = { l: 46, r: 74, t: 14, b: 34 };   // jobb oldalon hely a színskálának
    var W = cssW - m.l - m.r;
    var H = cssH - m.t - m.b;
    var sx = W / (2 * Xhalf);                  // m → px vízszintesen
    var sz = H / Zdepth;                        // m → px függőlegesen
    var X0 = m.l + W / 2;                        // világ x=0 képernyő-x
    var Z0 = m.t;                               // világ z=0 (felszín) képernyő-y
    var wx = function (x) { return X0 + x * sx; };
    var wz = function (z) { return Z0 + z * sz; };

    // --- mező kiszámítása durva rácson, majd felskálázva rajzoljuk ---
    var GW = 220, GH = Math.round(GW * (H / W));
    var off = document.createElement("canvas");
    off.width = GW; off.height = GH;
    var octx = off.getContext("2d");
    var img = octx.createImageData(GW, GH);
    var data = img.data;

    var a = B / 2;
    var skel = mode === "shear" ? slipSkeleton(B, D, phi) : null;
    // shear intenzitás: a teher-arány nemlineárisan emeli (törés közelében gyúl ki)
    var shearGain = Math.pow(lf, 1.5);

    for (var gy = 0; gy < GH; gy++) {
      for (var gx = 0; gx < GW; gx++) {
        // rács → világ
        var xw = -Xhalf + (gx / (GW - 1)) * (2 * Xhalf);
        var zw = (gy / (GH - 1)) * Zdepth;
        var val = 0;

        if (mode === "disp") {
          if (zw >= D) {
            var zeta = zw - D;                 // mélység a talp alatt
            var lat = Math.max(0, Math.abs(xw) - a);
            // süllyedés-hagyma: talpon max, mélységgel/oldalirányban csökken
            var infl =
              1 /
              (1 +
                Math.pow(zeta / (1.4 * B + 0.4), 2) +
                Math.pow(lat / (1.0 * B + 0.3), 2));
            val = infl * lf;                    // teherrel arányosan
          }
        } else {
          // nyírás: távolság a törővázhoz + általános izzás az aktív ékben
          var best = 1e9;
          for (var s = 0; s < skel.length; s++) {
            var dx = xw - skel[s][0], dz = zw - skel[s][1];
            var d2 = dx * dx + dz * dz;
            if (d2 < best) best = d2;
          }
          var w = 0.10 * B + 0.10;              // sáv-szélesség
          var band = Math.exp(-best / (w * w));
          val = band * shearGain;
        }
        var col = ramp(val);
        var o = (gy * GW + gx) * 4;
        data[o] = col[0]; data[o + 1] = col[1]; data[o + 2] = col[2];
        // alfa: kis érték → áttetsző (a háttér átüt), nagy → tömör
        data[o + 3] = Math.round(255 * (0.12 + 0.88 * Math.min(1, val * 1.15)));
      }
    }
    octx.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(off, m.l, m.t, W, H);

    // --- felszín vonala ---
    ctx.strokeStyle = line;
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(m.l, wz(0)); ctx.lineTo(m.l + W, wz(0)); ctx.stroke();

    // --- alaptest (valós méret), a süllyedéssel lefelé tolva (nagyítva) ---
    var exagg = 8;                              // süllyedés-nagyítás a láthatóságért
    var sPx = Math.min((opts.sCurrent / 1000) * sz * exagg, D * sz * 0.8);
    ctx.fillStyle = isDark ? "rgba(200,210,225,.92)" : "rgba(60,72,92,.92)";
    ctx.strokeStyle = ink;
    ctx.lineWidth = 1.2;
    var fx = wx(-a), fw = 2 * a * sx, fTop = wz(0), fBot = wz(D) + sPx;
    ctx.fillRect(fx, fTop, fw, fBot - fTop);
    ctx.strokeRect(fx, fTop, fw, fBot - fTop);

    // teher-nyíl az alapra
    ctx.strokeStyle = "#ef4444";
    ctx.fillStyle = "#ef4444";
    ctx.lineWidth = 2;
    var ax = X0, ay0 = fTop - 26, ay1 = fTop - 3;
    ctx.beginPath(); ctx.moveTo(ax, ay0); ctx.lineTo(ax, ay1); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ax - 5, ay1 - 7); ctx.lineTo(ax, ay1);
    ctx.lineTo(ax + 5, ay1 - 7); ctx.fill();

    // --- színskála (jobb oldalt) ---
    var lgX = m.l + W + 18, lgY = m.t + 6, lgW = 14, lgH = H - 20;
    for (var iy = 0; iy < lgH; iy++) {
      var tt = 1 - iy / lgH;
      var c = ramp(tt);
      ctx.fillStyle = "rgb(" + c[0] + "," + c[1] + "," + c[2] + ")";
      ctx.fillRect(lgX, lgY + iy, lgW, 1);
    }
    ctx.strokeStyle = line; ctx.lineWidth = 1;
    ctx.strokeRect(lgX, lgY, lgW, lgH);
    ctx.fillStyle = ink;
    ctx.font = "11px system-ui, sans-serif";
    ctx.textAlign = "left"; ctx.textBaseline = "middle";
    var topLab, botLab, unit;
    if (mode === "disp") {
      topLab = opts.sCurrent.toFixed(1); botLab = "0"; unit = "mm";
    } else {
      topLab = "nagy"; botLab = "0"; unit = "γ";
    }
    ctx.fillText(topLab + (mode === "disp" ? "" : ""), lgX + lgW + 5, lgY + 6);
    ctx.fillText(botLab, lgX + lgW + 5, lgY + lgH - 6);
    ctx.fillText(unit, lgX + lgW + 5, lgY + lgH / 2);

    // --- tengelycímkék ---
    ctx.fillStyle = ink;
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    ctx.fillText("szélesség  B = " + B.toFixed(2) + " m", X0, m.t + H + 8);
    ctx.save();
    ctx.translate(m.l - 34, m.t + H / 2); ctx.rotate(-Math.PI / 2);
    ctx.fillText("mélység [m]", 0, 0);
    ctx.restore();
  }

  window.FieldViz = { draw: draw };
})();
