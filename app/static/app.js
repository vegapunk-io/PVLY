/* Provenably UI — plain JS, no dependencies. All calls use relative URLs. */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));

  async function postJSON(url, body) {
    const r = await fetch(url, {method: "POST", headers: {"content-type": "application/json", "accept": "application/json"}, body: JSON.stringify(body)});
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) : r.statusText);
    return data;
  }

  // ---- tabs ------------------------------------------------------------------------------------
  $$("[data-tabs]").forEach((tabs) => {
    const buttons = $$("button[data-tab]", tabs);
    buttons.forEach((b) => b.addEventListener("click", () => {
      buttons.forEach((x) => x.classList.toggle("active", x === b));
      $$(".tabpanel").forEach((p) => p.classList.toggle("active", p.dataset.panel === b.dataset.tab));
    }));
  });

  // ---- drop zone -------------------------------------------------------------------------------
  const drop = $("#drop");
  if (drop) {
    const input = $("#file-input");
    ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
    ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
    drop.addEventListener("drop", (e) => {
      if (e.dataTransfer && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; $("#file-form").requestSubmit(); }
    });
  }

  // ---- report polling --------------------------------------------------------------------------
  const pending = $("#pending[data-scan]");
  if (pending && !$("#pending .dot.bad")) {
    const id = pending.dataset.scan;
    let tries = 0;
    const tick = async () => {
      tries++;
      try {
        const r = await fetch(`/v1/scans/${id}`, {headers: {accept: "application/json"}});
        const d = await r.json();
        if (d.status === "done" || d.status === "error") { location.reload(); return; }
        const s = $("#status"); if (s) s.textContent = d.status;
      } catch (e) { /* retry */ }
      if (tries < 120) setTimeout(tick, tries < 10 ? 700 : 2000);
    };
    setTimeout(tick, 600);
  }

  // ---- disclosure page -------------------------------------------------------------------------
  function disclosurePage() {
    const form = $("#disc-form"), out = $("#disc-result");
    if (!form) return;
    const qs = new URLSearchParams(location.search);
    if (qs.get("ct")) form.content_type.value = qs.get("ct");
    if (qs.has("ai")) form.is_ai_generated.checked = qs.get("ai") === "true";
    if (qs.has("c2pa")) form.has_c2pa.checked = qs.get("c2pa") === "true";
    const run = async () => {
      const fd = new FormData(form);
      const body = {content_type: fd.get("content_type"), jurisdictions: fd.getAll("jurisdictions")};
      ["is_ai_generated", "is_ai_edited", "depicts_real_person", "public_interest_text", "human_reviewed", "artistic", "has_c2pa", "has_visible_label", "has_metadata_id"].forEach((k) => body[k] = form[k].checked);
      out.innerHTML = '<p class="muted small">Checking…</p>';
      try {
        const d = await postJSON("/v1/disclosure/check", body);
        const tag = (st) => st === "todo" ? '<span class="tag warn">to do</span>' : st === "done" ? '<span class="tag ok">satisfied</span>' : st === "exempt" ? '<span class="tag">exempt</span>' : '<span class="tag">optional</span>';
        let h = `<div class="box"><strong>${d.open_items} open item${d.open_items === 1 ? "" : "s"}</strong> for ${esc(d.content_type)} · ${d.synthetic ? "synthetic content" : "not declared synthetic"}`;
        if (d.recommendations.length) h += `<ul class="plain small" style="margin-top:8px">${d.recommendations.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`;
        h += "</div>";
        d.jurisdictions.forEach((j) => {
          h += `<div class="box"><div class="row" style="justify-content:space-between"><strong>${esc(j.jurisdiction)}</strong><span class="small muted">effective ${esc(j.effective)} · ${esc(j.penalty)}</span></div>`;
          if (!j.items.length) h += '<p class="small muted" style="margin-top:6px">No obligation triggered by these facts.</p>';
          else h += `<table class="small" style="margin-top:8px">${j.items.map((i) => `<tr><td style="width:90px">${tag(i.status)}</td><td><span class="mono">${esc(i.key)}</span><br>${esc(i.requirement)}${i.note ? `<br><span class="muted">${esc(i.note)}</span>` : ""}</td></tr>`).join("")}</table>`;
          h += `<p class="small muted" style="margin:6px 0 0">confidence ${esc(j.confidence)} · verified ${esc(j.last_verified)}</p></div>`;
        });
        h += `<p class="small muted" style="margin-top:8px">${esc(d.disclaimer)}</p>`;
        out.innerHTML = h;
      } catch (e) { out.innerHTML = `<p class="notice">${esc(e.message)}</p>`; }
    };
    $("#disc-run").addEventListener("click", run);
    if (qs.get("from")) run();
  }

  // ---- tools page ------------------------------------------------------------------------------
  function toolsPage() {
    const inp = $("#u-in"), outp = $("#u-out"), res = $("#u-result");
    if (!inp) return;
    $("#u-sample").addEventListener("click", async () => {
      const r = await fetch("/demo-assets/text_hidden_chars.txt"); inp.value = await r.text();
    });
    $("#u-copy").addEventListener("click", () => { outp.select(); document.execCommand("copy"); });
    $("#u-run").addEventListener("click", async () => {
      res.innerHTML = '<p class="muted small">Scanning…</p>';
      try {
        const d = await postJSON("/v1/text/unicode", {text: inp.value, keep_joiners: $("#u-joiners").checked, ascii_dashes: $("#u-dashes").checked});
        outp.value = d.cleaned;
        const s = d.scan;
        let h = `<div class="box small"><strong>${s.count} suspicious code point${s.count === 1 ? "" : "s"}</strong> in ${s.stats.chars} characters${d.changed ? " · cleaned text differs" : " · nothing to clean"}`;
        const types = Object.entries(s.by_type || {});
        if (types.length) h += `<table style="margin-top:8px"><tr><th>Category</th><th>Count</th></tr>${types.map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v}</td></tr>`).join("")}</table>`;
        if (s.findings && s.findings.length) h += `<table style="margin-top:8px"><tr><th>Code point</th><th>Name</th><th>Position</th><th>Context</th></tr>${s.findings.slice(0, 25).map((x) => `<tr><td class="mono">${esc(x.cp)}</td><td>${esc(x.name)}</td><td class="num">${x.pos}</td><td class="mono">${esc(inp.value.slice(Math.max(0, x.pos - 12), x.pos))}<mark>·</mark>${esc(inp.value.slice(x.pos + 1, x.pos + 13))}</td></tr>`).join("")}</table>`;
        const st = s.stats || {};
        h += `<p class="muted" style="margin-top:8px">typography: ${st.em_dashes} em dashes · ${st.curly_quotes} curly quotes · ${st.double_spaces} double spaces · ${st.trailing_space_lines} lines with trailing spaces</p>`;
        h += "</div>";
        res.innerHTML = h;
      } catch (e) { res.innerHTML = `<p class="notice">${esc(e.message)}</p>`; }
    });
  }

  // ---- lab page --------------------------------------------------------------------------------
  function labPage() {
    if (!$("#g-run")) return;
    const stats = (s) => {
      if (s.error) return `<p class="notice">${esc(s.error)}</p>`;
      const cls = s.z > 4 ? "ok" : s.z > 2 ? "warn" : "";
      return `<div class="box"><span class="tag ${cls}">${esc(s.verdict)}</span> &nbsp; z = <strong>${s.z}</strong> · green ${s.green}/${s.scored_tokens} tokens · one-sided p = ${Number(s.p_one_sided).toExponential(2)}</div>`;
    };
    $("#g-run").addEventListener("click", async () => {
      try {
        const d = await postJSON("/v1/lab/greenlist", {action: "generate", key: $("#g-key").value, gamma: +$("#g-gamma").value, strength: +$("#g-strength").value, n: +$("#g-n").value});
        $("#d-text").value = d.text; $("#d-key").value = $("#g-key").value;
        $("#g-stats").innerHTML = "Generated. Detection with the same key: " + stats(d.stats);
        $("#d-stats").innerHTML = "";
      } catch (e) { $("#g-stats").innerHTML = `<p class="notice">${esc(e.message)}</p>`; }
    });
    const detect = async (key) => {
      try {
        const d = await postJSON("/v1/lab/greenlist", {action: "detect", key: key, gamma: +$("#g-gamma").value, text: $("#d-text").value});
        $("#d-stats").innerHTML = `<p class="small muted">key "${esc(key)}"</p>` + stats(d.stats);
      } catch (e) { $("#d-stats").innerHTML = `<p class="notice">${esc(e.message)}</p>`; }
    };
    $("#d-run").addEventListener("click", () => detect($("#d-key").value));
    $("#d-wrongkey").addEventListener("click", () => detect("not-the-key"));
  }

  // ---- sanitize page ---------------------------------------------------------------------------
  function sanitizePage() {
    const form = $("#san-form");
    if (!form) return;
    const drop = $("#san-drop"), input = $("#san-file");
    if (drop) {
      ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
      ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
      drop.addEventListener("drop", (e) => { if (e.dataTransfer && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; form.requestSubmit(); } });
    }
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const out = $("#san-result");
      if (!input.files.length) { out.innerHTML = '<p class="notice">Choose an image, PDF or DOCX first.</p>'; return; }
      const fd = new FormData();
      fd.append("file", input.files[0]);
      fd.append("keep_icc", $("#san-icc").checked ? "true" : "false");
      fd.append("reencode", $("#san-reencode").checked ? "true" : "false");
      out.innerHTML = '<p class="muted small">Removing metadata…</p>';
      try {
        const r = await fetch("/v1/sanitize", {method: "POST", body: fd, headers: {accept: "application/json"}});
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail ? (typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail)) : r.statusText);
        const det = d.detected || {}, ver = d.verify || {}, aft = ver.after || {};
        const has = (v) => Array.isArray(v) ? v.length > 0 : (v && typeof v === "object" ? Object.keys(v).some((k) => has(v[k])) : !!v);
        const fmt = (d.file && d.file.format) || "jpeg";
        const keys = fmt === "pdf" ? ["info", "xmp", "attachments", "c2pa"]
          : fmt === "docx" ? ["core", "app", "custom_properties", "comments", "tracked_changes", "media_metadata", "c2pa"]
          : ["c2pa", "exif", "xmp", "iptc", "icc"];
        const rows = keys.map((k) => {
          const was = has(det[k]), now = has(aft[k]);
          return `<tr><td class="mono">${k.toUpperCase()}</td><td>${was ? '<span class="tag warn">present</span>' : '<span class="muted">absent</span>'}</td><td>${now ? '<span class="tag warn">residual</span>' : '<span class="tag ok">absent</span>'}</td></tr>`;
        }).join("");
        let h = `<div class="box"><div class="row" style="justify-content:space-between"><strong>${esc(d.file.filename)}</strong>${ver.verdict === "clean" ? '<span class="tag ok">clean</span>' : '<span class="tag warn">residual</span>'}</div>`;
        h += `<table style="margin-top:10px"><tr><th>Group</th><th>Before</th><th>After</th></tr>${rows}</table>`;
        h += `<p class="small muted" style="margin-top:8px">${d.file.bytes_in} B → ${d.file.bytes_out} B · lossless: ${d.lossless ? "yes" : "no"}${d.pixels_identical === true ? " · pixels identical" : ""}</p>`;
        if (d.removed && d.removed.length) h += `<p class="small">Removed: ${d.removed.map((x) => esc(x.field) + (x.count > 1 ? " ×" + x.count : "")).join(", ")}</p>`;
        (d.warnings || []).forEach((w) => { h += `<p class="notice small">${esc(w)}</p>`; });
        h += `<p class="small muted">${esc(d.watermark_note)}</p>`;
        h += `<p style="margin-top:10px"><a class="btn small" href="${d.download_url}">Download sanitized file</a></p></div>`;
        out.innerHTML = h;
      } catch (err) { out.innerHTML = `<p class="notice">${esc(err.message)}</p>`; }
    });
  }

  window.Provenably = {disclosurePage, toolsPage, labPage, sanitizePage};
})();
