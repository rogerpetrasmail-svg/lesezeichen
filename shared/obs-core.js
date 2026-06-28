/* =====================================================================
   OBS MODULAR DASHBOARD  ·  obs-core.js
   ---------------------------------------------------------------------
   Gemeinsame Laufzeit-Bibliothek für ALLE Module + den Customizer.

   Aufgaben:
     1. Zentrale Settings (Farben, Linienstärke, Speed, Glow ...)
        - Defaults  ->  localStorage  ->  URL-Query-Parameter
     2. Live-Update-Kanäle (Customizer ändert alle Module sofort):
        storage-Event, BroadcastChannel, postMessage(iframe).
     3. Daten laden aus der NEUEN sheets/datasets-Struktur.
        - Bevorzugt window.OBS_DATA (per <script src="dashboard_data.js">)
          => läuft über file:// OHNE CORS-Fehler.
        - Fallback: fetch(dashboard_data.json) für den Server-Betrieb.
        - URL-Parameter ?sheet=Blattname wählt das aktive Blatt
          (ohne Angabe: erstes Blatt der JSON).
     4. Helfer für Multi-Serien-Charts:
        normalizeSheet(), seriesStyle(), gaugeFromSheet(), scale, polar, el.

   Bewusst dependency-frei (Vanilla JS), damit es 1:1 in einer OBS
   Browser Source läuft.
   ===================================================================== */
(function (global) {
  "use strict";

  var STORAGE_KEY = "obsDashboardSettings";
  var CHANNEL_NAME = "obs-dashboard";

  /* ---- Default-Design (= Standard Industrial-Orange) -------------- */
  var DEFAULTS = {
    primary: "#d35400",
    accent: "#e67e22",
    text: "#ffd9b3",
    grid: "rgba(211,84,0,0.22)",
    lineWidth: 2,
    speed: 1,
    glow: 6,
    frameOpacity: 0.18,
    frame: true
  };

  /* ================================================================= *
   *  TEIL 1+2 · SETTINGS & LIVE-UPDATE  (unverändert/bewährt)
   * ================================================================= */
  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  function readStorage() {
    try {
      var raw = global.localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }

  function readURL() {
    var out = {};
    var q = new URLSearchParams(global.location.search);
    if (q.has("primary"))      out.primary = "#" + q.get("primary").replace(/^#/, "");
    if (q.has("accent"))       out.accent = "#" + q.get("accent").replace(/^#/, "");
    if (q.has("text"))         out.text = "#" + q.get("text").replace(/^#/, "");
    if (q.has("lineWidth"))    out.lineWidth = parseFloat(q.get("lineWidth"));
    if (q.has("speed"))        out.speed = parseFloat(q.get("speed"));
    if (q.has("glow"))         out.glow = parseFloat(q.get("glow"));
    if (q.has("frameOpacity")) out.frameOpacity = parseFloat(q.get("frameOpacity"));
    if (q.has("frame"))        out.frame = q.get("frame") !== "0" && q.get("frame") !== "false";
    return out;
  }

  /* Wirksame Settings = Defaults < localStorage < URL-Parameter */
  function current() {
    var s = clone(DEFAULTS);
    var st = readStorage();
    var u = readURL();
    for (var k in st) if (st[k] !== undefined && st[k] !== null) s[k] = st[k];
    for (var k2 in u) if (u[k2] !== undefined && u[k2] !== null) s[k2] = u[k2];
    return s;
  }

  function apply(s) {
    var r = document.documentElement.style;
    r.setProperty("--c-primary", s.primary);
    r.setProperty("--c-accent", s.accent);
    r.setProperty("--c-text", s.text);
    if (s.grid) r.setProperty("--c-grid", s.grid);
    r.setProperty("--line-width", s.lineWidth + "px");
    r.setProperty("--speed", s.speed);
    r.setProperty("--glow", s.glow + "px");
    r.setProperty("--frame-opacity", s.frameOpacity);
    r.setProperty("--frame-show", s.frame ? "block" : "none");
  }

  var channel = null;
  try { channel = new BroadcastChannel(CHANNEL_NAME); } catch (e) { channel = null; }

  function save(partial) {
    var merged = current();
    for (var k in partial) merged[k] = partial[k];
    try { global.localStorage.setItem(STORAGE_KEY, JSON.stringify(merged)); } catch (e) {}
    apply(merged);
    if (channel) { try { channel.postMessage(merged); } catch (e) {} }
    var frames = document.querySelectorAll("iframe");
    for (var i = 0; i < frames.length; i++) {
      try { frames[i].contentWindow.postMessage({ __obs: true, settings: merged }, "*"); } catch (e) {}
    }
    return merged;
  }

  var listeners = [];
  function onChange(fn) { listeners.push(fn); }
  function emit(s) { for (var i = 0; i < listeners.length; i++) { try { listeners[i](s); } catch (e) {} } }

  function refreshFromExternal() { var s = current(); apply(s); emit(s); }

  global.addEventListener("storage", function (ev) {
    if (ev.key === STORAGE_KEY) refreshFromExternal();
  });
  if (channel) channel.onmessage = function () { refreshFromExternal(); };
  global.addEventListener("message", function (ev) {
    if (ev.data && ev.data.__obs && ev.data.settings) {
      try { global.localStorage.setItem(STORAGE_KEY, JSON.stringify(ev.data.settings)); } catch (e) {}
      apply(ev.data.settings);
      emit(ev.data.settings);
    }
  });

  /* ================================================================= *
   *  TEIL 3 · DATEN LADEN  (sheets/datasets, file://-tauglich)
   * ================================================================= */

  /* Minimaler Fallback in der NEUEN Struktur (falls weder JS noch JSON da). */
  var FALLBACK = {
    meta: { source: "fallback", sheets_found: ["Demo"] },
    sheets: {
      Demo: {
        labels: ["A", "B", "C", "D", "E", "F", "G", "H"],
        datasets: {
          "Var 1": [40, 55, 48, 70, 62, 80, 75, 90],
          "Var 2": [20, 30, 35, 28, 40, 33, 45, 50]
        }
      }
    }
  };

  /* Skript dynamisch nachladen – funktioniert über file:// (anders als fetch). */
  function injectScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = function () { res(true); };
      s.onerror = function () { rej(new Error("script " + src)); };
      document.head.appendChild(s);
    });
  }

  function tryScripts(list) {
    return list.reduce(function (p, src) {
      return p.then(function (done) {
        if (done || global.OBS_DATA) return true;
        return injectScript(src).then(function () { return true; })
          .catch(function () { return false; });
      });
    }, Promise.resolve(false));
  }

  function tryFetch(list) {
    return list.reduce(function (p, url) {
      return p.then(function (data) {
        if (data) return data;
        return fetch(url, { cache: "no-store" })
          .then(function (r) { if (!r.ok) throw 0; return r.json(); })
          .catch(function () { return null; });
      });
    }, Promise.resolve(null));
  }

  /* loadData() liefert IMMER das vollständige Datenobjekt {meta, sheets}. */
  function loadData() {
    // 1) bereits per <script> eingebunden?
    if (global.OBS_DATA && global.OBS_DATA.sheets) return Promise.resolve(global.OBS_DATA);

    // 2) JS-Variante nachladen (kein CORS über file://)
    return tryScripts(["../dashboard_data.js", "dashboard_data.js"]).then(function () {
      if (global.OBS_DATA && global.OBS_DATA.sheets) return global.OBS_DATA;
      // 3) Server-Fallback: JSON per fetch
      return tryFetch(["../dashboard_data.json", "dashboard_data.json"]).then(function (j) {
        return (j && j.sheets) ? j : FALLBACK;
      });
    });
  }

  /* ================================================================= *
   *  TEIL 4 · SHEET-/SERIEN-HELFER
   * ================================================================= */

  /* aktiven Sheet-Namen aus ?sheet= bestimmen (sonst erstes Blatt). */
  function activeSheetName(data) {
    var q = new URLSearchParams(global.location.search);
    var sheets = (data && data.sheets) || {};
    var keys = Object.keys(sheets);
    var want = q.get("sheet");
    if (want && sheets[want]) return want;
    return keys[0] || null;
  }

  /* Rohes Sheet-Objekt holen (per Name oder aktivem ?sheet=). */
  function getSheet(data, name) {
    var sheets = (data && data.sheets) || {};
    var n = (name && sheets[name]) ? name : activeSheetName(data);
    var s = (n && sheets[n]) || { labels: [], datasets: {} };
    return { name: n || "", labels: s.labels || [], datasets: s.datasets || {} };
  }

  /* Sheet so aufbereiten, dass labels + ALLE Datenreihen iterierbar sind
     und min/max GLOBAL über alle Reihen bekannt sind (gemeinsame Skala). */
  function normalizeSheet(data, name) {
    var s = getSheet(data, name);
    var series = Object.keys(s.datasets).map(function (k) {
      return { name: k, values: (s.datasets[k] || []).map(Number) };
    });
    var all = [];
    series.forEach(function (se) {
      se.values.forEach(function (v) { if (isFinite(v)) all.push(v); });
    });
    var min = all.length ? Math.min.apply(null, all) : 0;
    var max = all.length ? Math.max.apply(null, all) : 1;
    return {
      name: s.name,
      labels: s.labels,
      series: series,
      seriesCount: series.length,
      min: min,
      max: max
    };
  }

  /* Stil pro Datenreihe – konsequent an die CSS-Variablen gekoppelt,
     damit der Customizer alle Reihen LIVE umfärbt:
       Reihe 0 -> primary, 1 -> accent, 2 -> text  (deine Vorgaben)
       ab Reihe 3 wiederholen sich die Farben mit Strich-Muster,
       damit die Linien optisch getrennt bleiben.                     */
  var SERIES_COLORS = ["var(--c-primary)", "var(--c-accent)", "var(--c-text)"];
  var SERIES_DASH = ["none", "7 5", "2 6", "10 4 2 4"];
  function seriesStyle(i) {
    return {
      color: SERIES_COLORS[i % SERIES_COLORS.length],
      dash: SERIES_DASH[Math.floor(i / SERIES_COLORS.length) % SERIES_DASH.length],
      opacity: i < SERIES_COLORS.length ? 1 : 0.85
    };
  }

  /* Einzelwert für ein Gauge aus einem Sheet ziehen.
     Steuerung per URL: ?sheet=, ?dataset=Var 1, ?agg=last|max|min|avg|sum|first,
     optional ?min= ?max= ?unit= ?label=.                              */
  function aggregate(vals, mode) {
    if (!vals.length) return 0;
    switch (mode) {
      case "max": return Math.max.apply(null, vals);
      case "min": return Math.min.apply(null, vals);
      case "sum": return vals.reduce(function (a, b) { return a + b; }, 0);
      case "avg": return vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
      case "first": return vals[0];
      case "last":
      default: return vals[vals.length - 1];
    }
  }
  function niceMax(m) {
    if (!isFinite(m) || m <= 0) return 100;
    var p = Math.pow(10, Math.floor(Math.log10(m)));
    return Math.ceil(m / p) * p;
  }
  function gaugeFromSheet(data) {
    var q = new URLSearchParams(global.location.search);
    var s = getSheet(data, q.get("sheet"));
    var keys = Object.keys(s.datasets);
    var dsName = q.get("dataset");
    var key = (dsName && s.datasets[dsName] !== undefined) ? dsName : keys[0];
    var vals = ((s.datasets && s.datasets[key]) || []).map(Number).filter(isFinite);
    var value = aggregate(vals, q.get("agg") || "last");
    var min = q.has("min") ? parseFloat(q.get("min")) : 0;
    var max = q.has("max") ? parseFloat(q.get("max"))
                           : niceMax(vals.length ? Math.max.apply(null, vals) : 100);
    return {
      label: q.get("label") || (s.name + (key ? " · " + key : "")),
      id: key || s.name,
      value: value,
      min: min,
      max: (max <= min ? min + 1 : max),
      unit: q.get("unit") || ""
    };
  }

  /* ================================================================= *
   *  SVG-/MATHE-HELFER
   * ================================================================= */
  var SVGNS = "http://www.w3.org/2000/svg";

  function el(tag, attrs, parent) {
    var n = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function scale(d0, d1, r0, r1) {
    return function (v) { if (d1 === d0) return r0; return r0 + (v - d0) * (r1 - r0) / (d1 - d0); };
  }
  function polar(cx, cy, r, deg) {
    var a = (deg - 90) * Math.PI / 180;
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  }
  function extent(arr, acc) {
    var lo = Infinity, hi = -Infinity;
    for (var i = 0; i < arr.length; i++) { var v = acc(arr[i]); if (v < lo) lo = v; if (v > hi) hi = v; }
    return [lo, hi];
  }
  function pathLen(node) { try { return node.getTotalLength(); } catch (e) { return 1000; } }

  /* ---- Public API -------------------------------------------------- */
  var OBS = {
    DEFAULTS: DEFAULTS,
    STORAGE_KEY: STORAGE_KEY,
    current: current,
    apply: apply,
    save: save,
    onChange: onChange,
    loadData: loadData,
    // Sheet-/Serien-API
    activeSheetName: activeSheetName,
    getSheet: getSheet,
    normalizeSheet: normalizeSheet,
    seriesStyle: seriesStyle,
    gaugeFromSheet: gaugeFromSheet,
    // SVG-Helfer
    el: el, scale: scale, polar: polar, extent: extent, pathLen: pathLen,
    init: function () { apply(current()); return current(); }
  };

  OBS.init();
  global.OBS = OBS;
})(window);
