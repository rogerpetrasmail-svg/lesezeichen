/* =====================================================================
   OBS MODULAR DASHBOARD  ·  obs-core.js
   ---------------------------------------------------------------------
   Gemeinsame Laufzeit-Bibliothek für ALLE Module + den Customizer.

   Aufgaben:
     1. Zentrale Settings (Farben, Linienstärke, Speed, Glow ...)
        - Defaults  ->  localStorage  ->  URL-Query-Parameter
     2. Live-Update-Kanäle, damit der Customizer ALLE Module sofort
        ändert:  storage-Event, BroadcastChannel, postMessage(iframe).
     3. Daten laden aus dashboard_data.json.
     4. Kleine SVG-/Mathe-Helfer (scale, polar, el) gegen Code-Doppelung.

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
    lineWidth: 2,   // px
    speed: 1,       // Faktor (1 = normal, 2 = doppelt so schnell)
    glow: 6,        // px
    frameOpacity: 0.18,
    frame: true     // Tech-Rahmen anzeigen
  };

  /* ---- kleine Helfer ---------------------------------------------- */
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

  /* CSS-Variablen auf :root schreiben -> wirkt sofort auf alle Module */
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

  /* ---- Settings speichern + an alle Empfänger broadcasten --------- */
  var channel = null;
  try { channel = new BroadcastChannel(CHANNEL_NAME); } catch (e) { channel = null; }

  function save(partial) {
    var merged = current();
    for (var k in partial) merged[k] = partial[k];
    try { global.localStorage.setItem(STORAGE_KEY, JSON.stringify(merged)); } catch (e) {}
    apply(merged);
    if (channel) { try { channel.postMessage(merged); } catch (e) {} }
    // an eingebettete iframes (Customizer-Vorschau) weiterreichen
    var frames = document.querySelectorAll("iframe");
    for (var i = 0; i < frames.length; i++) {
      try { frames[i].contentWindow.postMessage({ __obs: true, settings: merged }, "*"); } catch (e) {}
    }
    return merged;
  }

  /* ---- Live-Empfang in jedem Modul -------------------------------- */
  var listeners = [];
  function onChange(fn) { listeners.push(fn); }
  function emit(s) { for (var i = 0; i < listeners.length; i++) { try { listeners[i](s); } catch (e) {} } }

  function refreshFromExternal() {
    var s = current();
    apply(s);
    emit(s);
  }

  // 1) localStorage-Änderung in anderem Tab/Source
  global.addEventListener("storage", function (ev) {
    if (ev.key === STORAGE_KEY) refreshFromExternal();
  });
  // 2) BroadcastChannel (gleiche Browser-Instanz)
  if (channel) channel.onmessage = function () { refreshFromExternal(); };
  // 3) postMessage von der Customizer-Seite (iframe-Vorschau)
  global.addEventListener("message", function (ev) {
    if (ev.data && ev.data.__obs && ev.data.settings) {
      try { global.localStorage.setItem(STORAGE_KEY, JSON.stringify(ev.data.settings)); } catch (e) {}
      apply(ev.data.settings);
      emit(ev.data.settings);
    }
  });

  /* ---- Daten laden ------------------------------------------------- */
  /* Lädt dashboard_data.json relativ zum Modul. Fällt auf eingebettete
     Minimal-Dummydaten zurück, falls die Datei (noch) fehlt.          */
  var FALLBACK = {
    gauges: [{ id: "g1", label: "SYSTEM", value: 72, min: 0, max: 100, unit: "%" }],
    series: {
      line:  { label: "SIGNAL",  points: [40,55,48,70,62,80,75,90].map(function (y, i) { return { x: i, y: y }; }) },
      bar:   { label: "OUTPUT",  points: [{ label: "A", y: 40 }, { label: "B", y: 65 }, { label: "C", y: 52 }, { label: "D", y: 78 }, { label: "E", y: 60 }] },
      pie:   { label: "SHARE",   points: [{ label: "CORE", y: 35 }, { label: "AUX", y: 25 }, { label: "NET", y: 22 }, { label: "RES", y: 18 }] },
      area:  { label: "LOAD",    points: [30,45,40,60,55,72,68,85].map(function (y, i) { return { x: i, y: y }; }) },
      scatter: { label: "DATA",  points: Array.from({ length: 24 }, function (_, i) { return { x: Math.random() * 100, y: Math.random() * 100 }; }) },
      radar: { label: "PROFILE", axes: [{ label: "SPD", y: 80 }, { label: "PWR", y: 65 }, { label: "DEF", y: 50 }, { label: "ACC", y: 72 }, { label: "EFF", y: 60 }] },
      combo: { label: "TREND",   points: [{ label: "Q1", bar: 40, line: 30 }, { label: "Q2", bar: 55, line: 48 }, { label: "Q3", bar: 50, line: 62 }, { label: "Q4", bar: 72, line: 70 }] }
    }
  };

  function loadData() {
    return fetch("../dashboard_data.json", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("no file"); return r.json(); })
      .catch(function () {
        return fetch("dashboard_data.json", { cache: "no-store" })
          .then(function (r) { if (!r.ok) throw new Error("no file"); return r.json(); })
          .catch(function () { return FALLBACK; });
      });
  }

  /* ---- SVG-/Mathe-Helfer ------------------------------------------ */
  var SVGNS = "http://www.w3.org/2000/svg";

  function el(tag, attrs, parent) {
    var n = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  // lineare Skala domain -> range
  function scale(d0, d1, r0, r1) {
    return function (v) {
      if (d1 === d0) return r0;
      return r0 + (v - d0) * (r1 - r0) / (d1 - d0);
    };
  }

  // Polar-Koordinate (0° = oben, im Uhrzeigersinn)
  function polar(cx, cy, r, deg) {
    var a = (deg - 90) * Math.PI / 180;
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  }

  function extent(arr, acc) {
    var lo = Infinity, hi = -Infinity;
    for (var i = 0; i < arr.length; i++) {
      var v = acc(arr[i]);
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    return [lo, hi];
  }

  // Pfad-Länge messen (für draw-in Animation)
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
    el: el,
    scale: scale,
    polar: polar,
    extent: extent,
    pathLen: pathLen,
    // Beim Start die aktuellen Settings sofort anwenden
    init: function () { apply(current()); return current(); }
  };

  // Auto-Init für Module (Customizer ruft init selbst nach Bedarf)
  OBS.init();

  global.OBS = OBS;
})(window);
