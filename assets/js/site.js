// Small, dependency-free behaviour: theme, tooltips, copy, journey filter, reveal, TOC.
(function () {
  "use strict";
  var root = document.documentElement;
  var lang = root.lang || "es";
  var T = {
    es: { copy: "Copiar", copied: "Copiado", theme: "Cambiar tema", showAll: "Ver todos" },
    en: { copy: "Copy", copied: "Copied", theme: "Toggle theme", showAll: "Show all" }
  }[lang.slice(0, 2)] || {};

  // ---------- Theme ----------
  function storedTheme() { try { return localStorage.getItem("theme"); } catch (e) { return null; } }
  function saveTheme(v) { try { localStorage.setItem("theme", v); } catch (e) { /* private mode */ } }
  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.setAttribute("aria-pressed", currentTheme() === "dark" ? "true" : "false");
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      saveTheme(next);
      toggle.setAttribute("aria-pressed", next === "dark" ? "true" : "false");
      var meta = document.querySelector('meta[name="theme-color"]:not([media])');
      if (meta) meta.setAttribute("content", next === "dark" ? "#121211" : "#f7f6f2");
    });
  }
  if (!storedTheme()) {
    // keep following the OS if the visitor never chose
  }

  // ---------- Header border on scroll ----------
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---------- Tooltip ----------
  var tip = document.createElement("div");
  tip.className = "tip";
  tip.setAttribute("role", "status");
  tip.setAttribute("aria-live", "off");
  document.body.appendChild(tip);
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.classList.add("on");
    var r = tip.getBoundingClientRect();
    var left = Math.min(window.innerWidth - r.width - 8, Math.max(8, x - r.width / 2));
    var top = y - r.height - 12;
    if (top < 8) top = y + 16;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }
  function hideTip() { tip.classList.remove("on"); }
  document.querySelectorAll("[data-tip]").forEach(function (el) {
    el.addEventListener("pointerenter", function (e) { showTip(el.getAttribute("data-tip"), e.clientX, e.clientY); });
    el.addEventListener("pointermove", function (e) { showTip(el.getAttribute("data-tip"), e.clientX, e.clientY); });
    el.addEventListener("pointerleave", hideTip);
  });

  // Line charts: crosshair + nearest point
  document.querySelectorAll("svg.linechart").forEach(function (svg) {
    var pts;
    try { pts = JSON.parse(svg.getAttribute("data-points")); } catch (e) { return; }
    var xh = svg.querySelector(".xh"), hov = svg.querySelector(".hov");
    var vb = svg.viewBox.baseVal;
    function move(e) {
      var r = svg.getBoundingClientRect();
      var x = (e.clientX - r.left) * (vb.width / r.width);
      var best = 0, bd = Infinity;
      for (var i = 0; i < pts.length; i++) { var d = Math.abs(pts[i][0] - x); if (d < bd) { bd = d; best = i; } }
      var p = pts[best];
      xh.setAttribute("x1", p[0]); xh.setAttribute("x2", p[0]);
      hov.setAttribute("cx", p[0]); hov.setAttribute("cy", p[1]);
      svg.classList.add("active");
      var sx = r.left + p[0] * (r.width / vb.width), sy = r.top + p[1] * (r.height / vb.height);
      showTip(p[2], sx, sy);
    }
    svg.addEventListener("pointermove", move);
    svg.addEventListener("pointerdown", move);
    svg.addEventListener("pointerleave", function () { svg.classList.remove("active"); hideTip(); });
  });

  // ---------- Copy buttons ----------
  document.querySelectorAll("pre[data-copy]").forEach(function (pre) {
    var wrap = pre.parentElement;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "copy";
    b.textContent = T.copy;
    b.addEventListener("click", function () {
      var text = pre.innerText;
      var done = function () {
        b.textContent = T.copied; b.classList.add("done");
        setTimeout(function () { b.textContent = T.copy; b.classList.remove("done"); }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      }
    });
    wrap.appendChild(b);
  });

  // ---------- Data journey filter ----------
  var stages = document.querySelectorAll(".stage[data-stage]");
  var cards = document.querySelectorAll("[data-stages]");
  var reset = document.querySelector("[data-journey-reset]");
  function applyStage(s) {
    stages.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-stage") === s ? "true" : "false"); });
    cards.forEach(function (c) {
      var has = (" " + c.getAttribute("data-stages") + " ").indexOf(" " + s + " ") > -1;
      c.classList.toggle("dim", !!s && !has);
      c.classList.toggle("lit", !!s && has);
    });
    if (reset) reset.hidden = !s;
  }
  stages.forEach(function (b) {
    b.addEventListener("click", function () {
      var s = b.getAttribute("data-stage");
      applyStage(b.getAttribute("aria-pressed") === "true" ? "" : s);
    });
  });
  if (reset) reset.addEventListener("click", function () { applyStage(""); });

  // ---------- Reveal on scroll ----------
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var targets = document.querySelectorAll(".rv, .reveal");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    targets.forEach(function (t) { io.observe(t); });
  } else {
    targets.forEach(function (t) { t.classList.add("in"); });
  }

  // ---------- TOC scrollspy ----------
  var tocLinks = document.querySelectorAll(".toc a[href^='#']");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          tocLinks.forEach(function (a) { a.classList.remove("on"); });
          var a = map[en.target.id]; if (a) a.classList.add("on");
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) spy.observe(s); });
  }
})();
