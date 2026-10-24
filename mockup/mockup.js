/* Provenably mockup interactions — dummy only, no network calls. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.from((r || document).querySelectorAll(s)); };

  // Tabs
  $$("[data-tabs]").forEach(function (tabs) {
    var buttons = $$("button[data-tab]", tabs);
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        buttons.forEach(function (x) { x.classList.toggle("active", x === b); });
        $$(".tabpanel").forEach(function (p) { p.classList.toggle("active", p.dataset.panel === b.dataset.tab); });
      });
    });
  });

  // Dropzones: show selected filename (no upload happens)
  $$(".drop").forEach(function (drop) {
    var input = $("input[type=file]", drop);
    var label = $(".drop-file", drop);
    ["dragenter", "dragover"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files.length && label) {
        label.textContent = "Selected: " + e.dataTransfer.files[0].name + "  (mockup — nothing is uploaded)";
      }
    });
    if (input) input.addEventListener("change", function () {
      if (input.files.length && label) label.textContent = "Selected: " + input.files[0].name + "  (mockup — nothing is uploaded)";
    });
  });

  // Platform preset cards: single-select highlight + summary echo
  var presetOut = $("#preset-summary");
  $$(".platcard[data-preset]").forEach(function (card) {
    card.addEventListener("click", function () {
      $$(".platcard[data-preset]").forEach(function (c) { c.classList.toggle("sel", c === card); });
      if (presetOut) presetOut.textContent = card.dataset.preset;
    });
  });

  // Fake primary actions: turn into mock progress then done-state
  $$("[data-mock-action]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = $(btn.dataset.mockAction);
      if (!target) return;
      target.classList.remove("hidden");
      target.innerHTML = '<div class="box"><strong>Working…</strong><div class="progress indet" style="margin-top:10px"><span></span></div><p class="small muted" style="margin-top:8px">Mockup state only — backend will be connected later (see WIREFRAME.md backend contract).</p></div>';
      setTimeout(function () {
        target.innerHTML = '<div class="box"><span class="tag ok">mock: done</span> <strong>Result state preview</strong><p class="small muted" style="margin-top:6px">This box represents the finished result. Real data arrives when the backend endpoint in WIREFRAME.md is wired to this page.</p></div>';
      }, 1100);
    });
  });
})();
