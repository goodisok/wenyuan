/** 问元 · 前端 v2.0 */
const STORAGE_KEY = "wenyuan_chart";
const HISTORY_KEY = "wenyuan_history";
const INPUT_KEY = "wenyuan_input";
const CHART_CACHE_KEY = "wenyuan_chart_cache";
const MAX_HISTORY = 20;
const SHARE_VERSION = 1;
/** Bump when chart/insight shape changes so old session entries are ignored. */
const CHART_CACHE_SCHEMA = 4;
const CHART_CACHE_TTL = 3600000;

const AI_STYLE = "modern"; // API 兼容字段，后端提示词已统一
const DEFAULT_BIRTH = {
  date_type: "solar",
  birth_date: "1993-12-09",
  birth_time: "18:00",
  gender: "male",
};

const WUXING_MAP = { 木: "wood", 火: "fire", 土: "earth", 金: "metal", 水: "water" };

function pad2(n) {
  return String(n).padStart(2, "0");
}

function daysInMonth(year, month) {
  return new Date(Number(year), Number(month), 0).getDate();
}

function readBirthFromForm(form) {
  const y = birthField(form, "birth_year")?.value;
  const m = pad2(birthField(form, "birth_month")?.value || 1);
  const d = pad2(birthField(form, "birth_day")?.value || 1);
  const h = pad2(birthField(form, "birth_hour")?.value ?? 0);
  const mi = pad2(birthField(form, "birth_minute")?.value ?? 0);
  const dateType =
    form.querySelector('input[name="date_type"]:checked')?.value
    || form.date_type?.value
    || "solar";
  return {
    date_type: dateType,
    birth_date: `${y}-${m}-${d}`,
    birth_time: `${h}:${mi}`,
    gender: form.querySelector('input[name="gender"]:checked')?.value || "male",
    is_leap_month: form.is_leap_month?.checked || false,
  };
}

function applyBirthToForm(form, input) {
  if (!form || !input?.birth_date) return;
  const [y, m, d] = input.birth_date.split("-");
  const [h, mi] = (input.birth_time || "12:00").split(":");
  const yearEl = birthField(form, "birth_year");
  const monthEl = birthField(form, "birth_month");
  const dayEl = birthField(form, "birth_day");
  const hourEl = birthField(form, "birth_hour");
  const minuteEl = birthField(form, "birth_minute");
  if (yearEl) yearEl.value = y;
  if (monthEl) monthEl.value = String(Number(m));
  syncBirthDayOptions(form);
  if (dayEl) dayEl.value = String(Number(d));
  if (hourEl) hourEl.value = String(Number(h));
  if (minuteEl) {
    const mNum = Number(mi || 0);
    if (!minuteEl.querySelector(`option[value="${mNum}"]`)) {
      fillBirthMinuteOptions(minuteEl);
    }
    minuteEl.value = String(mNum);
  }
  if (form.date_type && input.date_type) {
    const dt = form.querySelector(`input[name="date_type"][value="${input.date_type}"]`);
    if (dt) dt.checked = true;
    else if (form.date_type.value !== undefined) form.date_type.value = input.date_type;
  }
  if (input.gender) {
    const g = form.querySelector(`input[name="gender"][value="${input.gender}"]`);
    if (g) g.checked = true;
  }
  if (form.is_leap_month) form.is_leap_month.checked = !!input.is_leap_month;
}

function syncBirthDayOptions(form) {
  const yearEl = birthField(form, "birth_year");
  const monthEl = birthField(form, "birth_month");
  const dayEl = birthField(form, "birth_day");
  if (!yearEl || !monthEl || !dayEl) return;
  const max = daysInMonth(yearEl.value, monthEl.value);
  const cur = Number(dayEl.value) || 1;
  dayEl.innerHTML = Array.from({ length: max }, (_, i) => {
    const v = i + 1;
    return `<option value="${v}"${v === cur ? " selected" : ""}>${v} 日</option>`;
  }).join("");
  if (cur > max) dayEl.value = String(max);
}

function fillBirthYearOptions(select, from = 1920, to = 2030) {
  if (!select) return;
  select.innerHTML = Array.from({ length: to - from + 1 }, (_, i) => {
    const y = to - i;
    return `<option value="${y}">${y} 年</option>`;
  }).join("");
}

function fillBirthMinuteOptions(select) {
  if (!select) return;
  select.innerHTML = Array.from({ length: 60 }, (_, i) =>
    `<option value="${i}">${pad2(i)} 分</option>`
  ).join("");
}

/** Reliable access to named birth fields (nested in form-row divs). */
function birthField(form, name) {
  if (!form) return null;
  return form.elements?.namedItem?.(name) || form.querySelector(`[name="${name}"]`);
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function hashInput(input) {
  const s = JSON.stringify(input);
  let h = 0;
  for (let i = 0; i < s.length; i += 1) {
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  }
  return `h${Math.abs(h)}`;
}

function encodeSharePayload(input) {
  const json = JSON.stringify({ v: SHARE_VERSION, ...input });
  const b64 = btoa(unescape(encodeURIComponent(json)));
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeSharePayload(raw) {
  let b64 = raw.replace(/-/g, "+").replace(/_/g, "/");
  while (b64.length % 4) b64 += "=";
  const json = decodeURIComponent(escape(atob(b64)));
  const data = JSON.parse(json);
  if (data.v !== SHARE_VERSION) throw new Error("链接版本不兼容");
  return data;
}

function getShareUrl(input) {
  const q = encodeSharePayload(input);
  return `${location.origin}/chart?s=${q}`;
}

function throttle(fn, wait) {
  let timer = null;
  let pending = null;
  return (...args) => {
    pending = args;
    if (timer) return;
    fn(...args);
    timer = setTimeout(() => {
      timer = null;
      if (pending && pending !== args) fn(...pending);
      pending = null;
    }, wait);
  };
}

function loadCachedChart(shareKey) {
  try {
    const cache = JSON.parse(sessionStorage.getItem(CHART_CACHE_KEY) || "{}");
    const entry = cache[shareKey];
    if (
      entry
      && entry.schema === CHART_CACHE_SCHEMA
      && Date.now() - entry.ts < CHART_CACHE_TTL
    ) {
      return entry.chart;
    }
  } catch {
    /* ignore */
  }
  return null;
}

function cacheChartPayload(shareKey, chart) {
  try {
    const cache = JSON.parse(sessionStorage.getItem(CHART_CACHE_KEY) || "{}");
    cache[shareKey] = { chart, schema: CHART_CACHE_SCHEMA, ts: Date.now() };
    sessionStorage.setItem(CHART_CACHE_KEY, JSON.stringify(cache));
  } catch {
    /* ignore */
  }
}

function clearAiCache(input) {
  try {
    localStorage.removeItem(aiCacheKey(input));
  } catch {
    /* ignore */
  }
}

function setBtnLoading(btn, loading, idleLabel) {
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle("is-loading", loading);
  const label = btn.querySelector(".btn-label");
  if (label) label.textContent = loading ? "排盘中…" : idleLabel;
  else if (!loading) btn.textContent = idleLabel;
}

function openModal(modal, trigger) {
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
  modal.dataset.trigger = trigger?.id || "";
  modal.querySelector("#modal-confirm, .btn-primary, button")?.focus();
}

function closeModal(modal) {
  if (!modal) return;
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
  const triggerId = modal.dataset.trigger;
  if (triggerId) document.getElementById(triggerId)?.focus();
}

function setupNavObserver() {
  const nav = document.getElementById("chart-nav");
  if (!nav) return;
  const sections = ["sec-meta", "sec-di", "sec-tian", "sec-ai"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);
  if (!sections.length) return;

  const setActive = (id) => {
    nav.querySelectorAll(".chart-nav-btn").forEach((btn) => {
      const active = btn.dataset.target === id;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
  };

  const isMobile = window.matchMedia("(max-width: 640px)").matches;
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
      if (visible[0]?.target?.id) setActive(visible[0].target.id);
    },
    {
      rootMargin: isMobile ? "-28% 0px -48% 0px" : "-20% 0px -55% 0px",
      threshold: [0, 0.25, 0.5],
    }
  );
  sections.forEach((sec) => observer.observe(sec));
}

function setupChartNavA11y() {
  const nav = document.getElementById("chart-nav");
  if (!nav) return;
  const tabs = [...nav.querySelectorAll(".chart-nav-btn")];
  if (!tabs.length) return;

  tabs.forEach((btn, i) => {
    btn.setAttribute("tabindex", i === 0 ? "0" : "-1");
    btn.setAttribute("aria-controls", btn.dataset.target || "");
  });

  const focusTab = (btn) => {
    tabs.forEach((t) => t.setAttribute("tabindex", t === btn ? "0" : "-1"));
    btn.focus();
  };

  const activateTab = (btn) => {
    const id = btn.dataset.target;
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    tabs.forEach((t) => {
      const active = t === btn;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", active ? "true" : "false");
    });
    focusTab(btn);
  };

  nav.addEventListener("keydown", (e) => {
    const idx = tabs.indexOf(document.activeElement);
    if (idx < 0) return;
    let next = idx;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      next = (idx + 1) % tabs.length;
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      next = (idx - 1 + tabs.length) % tabs.length;
    } else if (e.key === "Home") {
      next = 0;
    } else if (e.key === "End") {
      next = tabs.length - 1;
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      activateTab(tabs[idx]);
      return;
    } else {
      return;
    }
    e.preventDefault();
    focusTab(tabs[next]);
  });

  tabs.forEach((btn) => {
    btn.addEventListener("click", () => activateTab(btn));
  });
}

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(input, label) {
  const list = loadHistory().filter((h) => JSON.stringify(h.input) !== JSON.stringify(input));
  list.unshift({ input, label, ts: Date.now() });
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, MAX_HISTORY)));
}

function aiCacheKey(input) {
  return `wenyuan_ai_${hashInput(input)}`;
}

function loadAiCache(input) {
  try {
    return JSON.parse(localStorage.getItem(aiCacheKey(input)) || "null");
  } catch {
    return null;
  }
}

function saveAiCache(input, data) {
  localStorage.setItem(aiCacheKey(input), JSON.stringify({ analysis: data.analysis || "" }));
}

function normalizeAiCache(cache) {
  if (!cache) return { analysis: "" };
  if (typeof cache.analysis === "string") {
    return { analysis: cache.analysis };
  }
  const legacy = cache.analysis || {};
  return {
    analysis: legacy.modern || legacy.classic || "",
  };
}

async function parseJsonResponse(res) {
  const body = await res.json();
  if (!res.ok) {
    const detail = body.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail.map((d) => d.msg || d.message || String(d)).join("；") || `请求失败 (${res.status})`);
    }
    throw new Error(body.error || body.message || `请求失败 (${res.status})`);
  }
  return body;
}

async function consumeSSE(res, onChunk) {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let full = "";
  let error = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const block of parts) {
      const lines = block.split("\n");
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) event = line.slice(7).trim();
        if (line.startsWith("data: ")) data = line.slice(6);
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (event === "chunk" && parsed.text) {
          full += parsed.text;
          onChunk(full, parsed.text);
        } else if (event === "done") {
          full = parsed.analysis || parsed.answer || full;
        } else if (event === "error") {
          error = parsed.error || "流式请求失败";
        }
      } catch {
        /* ignore */
      }
    }
  }
  if (error) throw new Error(error);
  return full;
}

const API = {
  async chart(payload) {
    const res = await fetch("/api/chart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return parseJsonResponse(res);
  },
  async analyze(chart, style, insight, onChunk) {
    const body = { chart, insight: insight || chart.insight, style };
    if (onChunk) {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `请求失败 (${res.status})`);
      }
      return consumeSSE(res, onChunk);
    }
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await parseJsonResponse(res);
    if (!data.success) throw new Error(data.error || "分析失败");
    return data.analysis;
  },
  async ask(chart, question, style, insight, analysis, history, onChunk) {
    const body = {
      chart,
      insight: insight || chart.insight,
      question,
      style,
      analysis: analysis || "",
      history: history || [],
    };
    if (onChunk) {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });
      if (res.status === 503) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "AI 暂时关闭");
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `请求失败 (${res.status})`);
      }
      return consumeSSE(res, onChunk);
    }
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await parseJsonResponse(res);
    if (!data.success) throw new Error(data.error || "问答失败");
    return data.answer;
  },
};

function showError(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("hidden");
}

function hideError(el) {
  if (!el) return;
  el.classList.add("hidden");
}

function showToast(msg) {
  let t = document.getElementById("copy-toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "copy-toast";
    t.className = "copy-toast";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2000);
}

function inlineMarkdown(text) {
  return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function formatMarkdownBody(body) {
  const lines = body.split("\n");
  const parts = [];
  let listType = null;
  const closeList = () => {
    if (listType) {
      parts.push(`</${listType}>`);
      listType = null;
    }
  };
  for (const rawLine of lines) {
    const trimmed = rawLine.trimEnd().trim();
    if (!trimmed) {
      closeList();
      continue;
    }
    if (/^---+$/.test(trimmed)) {
      closeList();
      parts.push('<hr class="analysis-divider">');
      continue;
    }
    if (trimmed.startsWith("### ")) {
      closeList();
      parts.push(`<h4 class="analysis-subtitle">${inlineMarkdown(trimmed.slice(4))}</h4>`);
      continue;
    }
    if (trimmed.startsWith("> ")) {
      closeList();
      parts.push(`<blockquote class="analysis-quote">${inlineMarkdown(trimmed.slice(2))}</blockquote>`);
      continue;
    }
    if (/^[-*]\s+/.test(trimmed)) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        parts.push('<ul class="analysis-list">');
      }
      parts.push(`<li>${inlineMarkdown(trimmed.replace(/^[-*]\s+/, ""))}</li>`);
      continue;
    }
    if (/^\d+\.\s+/.test(trimmed)) {
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        parts.push('<ol class="analysis-list">');
      }
      parts.push(`<li>${inlineMarkdown(trimmed.replace(/^\d+\.\s+/, ""))}</li>`);
      continue;
    }
    closeList();
    parts.push(`<p class="analysis-paragraph">${inlineMarkdown(trimmed)}</p>`);
  }
  closeList();
  return parts.join("");
}

function markdownToHtml(markdown) {
  const escaped = escapeHtml(String(markdown || "").trim());
  if (!escaped) return "";
  return escaped
    .split(/\n(?=## )/)
    .map((block) => {
      const lines = block.split("\n");
      let title = "";
      let body = block;
      if (lines[0].startsWith("## ")) {
        title = lines[0].replace(/^#+\s*/, "");
        body = lines.slice(1).join("\n");
      }
      const inner = formatMarkdownBody(body);
      if (title) {
        return `<section class="analysis-block"><h3 class="analysis-block-title">${title}</h3>${inner}</section>`;
      }
      return `<section class="analysis-block">${inner}</section>`;
    })
    .join("");
}

function wuxingClass(color) {
  return color ? `wuxing-${color}` : "";
}

function renderWuxingChart(wx) {
  const entries = Object.entries(wx || {});
  const total = Math.max(entries.reduce((s, [, v]) => s + Number(v), 0), 1);
  const summary = entries.map(([k, v]) => `${k}${v}`).join(" ");
  return `<div class="wuxing-chart" role="img" aria-label="五行分布 ${escapeHtml(summary)}">${entries
    .map(([k, v]) => {
      const n = Number(v);
      const pct = Math.round((n / total) * 100);
      return `<div class="wuxing-bar-row">
        <span class="wuxing-bar-label wuxing-${WUXING_MAP[k] || ""}">${escapeHtml(k)}</span>
        <div class="wuxing-bar-track"><div class="wuxing-bar-fill wuxing-${WUXING_MAP[k] || ""}" style="width:${pct}%"></div></div>
        <span class="wuxing-bar-val">${n}<span class="wuxing-bar-pct"> ${pct}%</span></span>
      </div>`;
    })
    .join("")}</div>`;
}

function renderCangganCell(p) {
  return (p.dizhi.canggan || [])
    .map((c) => {
      const ss = c.shishen ? `<span class="cg-ss">${escapeHtml(c.shishen)}</span>` : "";
      return `<span class="cg-item ${wuxingClass(c.color)}">${escapeHtml(c.name)}${ss}</span>`;
    })
    .join("");
}

function renderPillarGrid(pillars) {
  if (!pillars?.length) return "";
  const colClass = (p) => (p.key === "day" ? "day-col" : "");
  const header = pillars
    .map((p) => `<th class="col-head ${colClass(p)}">${escapeHtml(p.label)}</th>`)
    .join("");
  const cells = (fn) =>
    pillars.map((p) => `<td class="${colClass(p)}">${fn(p)}</td>`).join("");
  const rows = [
    ["十神", (p) => escapeHtml(p.shishen || "—")],
    [
      "天干",
      (p) =>
        `<span class="gan-cell ${wuxingClass(p.tiangan.color)}">${escapeHtml(p.tiangan.name)}</span>`,
    ],
    [
      "地支",
      (p) =>
        `<span class="zhi-cell ${wuxingClass(p.dizhi.color)}">${escapeHtml(p.dizhi.name)}</span>`,
    ],
    ["藏干", (p) => `<div class="canggan-cell">${renderCangganCell(p) || "—"}</div>`],
    ["纳音", (p) => escapeHtml(p.nayin || "—")],
    ["空亡", (p) => escapeHtml(p.xunkong || "—")],
    ["星运", (p) => escapeHtml(p.changsheng || "—")],
  ];
  const body = rows
    .map(
      ([label, fn]) =>
        `<tr><th class="row-label" scope="row">${label}</th>${cells(fn)}</tr>`
    )
    .join("");
  return `<div class="table-wrap bazi-grid-wrap"><table class="bazi-grid"><thead><tr><th class="row-label"></th>${header}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function renderPillar(p) {
  const cg = (p.dizhi.canggan || [])
    .map((c) => {
      const ss = c.shishen ? `·${escapeHtml(c.shishen)}` : "";
      return `<span class="canggan-tag ${wuxingClass(c.color)}">${escapeHtml(c.name)}${ss}</span>`;
    })
    .join("");
  const cs = p.changsheng ? `<div class="pillar-changsheng">${escapeHtml(p.changsheng)}</div>` : "";
  const xk = p.xunkong ? `<div class="pillar-xunkong">旬空 ${escapeHtml(p.xunkong)}</div>` : "";
  return `
    <div class="pillar">
      <div class="pillar-label">${escapeHtml(p.label)}</div>
      <div class="pillar-ganzhi">${escapeHtml(p.ganzhi)}</div>
      <div class="stem ${wuxingClass(p.tiangan.color)}">${escapeHtml(p.tiangan.name)} · ${escapeHtml(p.tiangan.wuxing)}</div>
      <div class="branch ${wuxingClass(p.dizhi.color)}">${escapeHtml(p.dizhi.name)} · ${escapeHtml(p.dizhi.wuxing)}</div>
      <div class="canggan-list">${cg}</div>
      ${cs}
      ${xk}
      <div class="pillar-meta">${escapeHtml(p.shishen)}<br>${escapeHtml(p.nayin)}</div>
    </div>`;
}

function renderDayunStrip(dayun, insight) {
  if (!dayun?.length) return "";
  const cd = insight?.current_dayun;
  const cy = insight?.current_year_liunian;
  const nowYear = new Date().getFullYear();
  const items = dayun
    .map((d, i) => {
      const isCurrent = cd?.ganzhi === d.ganzhi;
      return `<button type="button" class="dayun-strip-item${isCurrent ? " is-current" : ""}" data-idx="${i}" aria-pressed="${isCurrent ? "true" : "false"}">
        <span class="dayun-strip-gz">${escapeHtml(d.ganzhi)}</span>
        <span class="dayun-strip-yrs">${d.start_year}—${d.end_year}</span>
        <span class="dayun-strip-age">${d.start_age}—${d.end_age}岁</span>
      </button>`;
    })
    .join("");
  const defaultIdx = Math.max(
    0,
    dayun.findIndex((d) => d.start_year <= nowYear && d.end_year >= nowYear)
  );
  const defaultDy = dayun[defaultIdx];
  const liuInit = (defaultDy?.liunian || [])
    .map((ln) => {
      const isCur = cy?.year === ln.year || ln.year === nowYear;
      return `<span class="liunian-chip${isCur ? " is-current" : ""}">${escapeHtml(ln.ganzhi)}<small>${ln.year}</small></span>`;
    })
    .join("");
  const banner = cd
    ? `<p class="yun-now-banner">当前大运 <strong>${escapeHtml(cd.ganzhi)}</strong>（${cd.start_year}—${cd.end_year}）${
        cy ? ` · 今年流年 <strong>${escapeHtml(cy.ganzhi)}</strong>（${cy.year}）` : ""
      }</p>`
    : "";
  return `${banner}<div class="dayun-strip-wrap"><p class="dayun-strip-label">大运</p><div class="dayun-strip" id="dayun-strip" data-default-idx="${defaultIdx}">${items}</div><p class="dayun-strip-label">流年</p><div class="liunian-strip" id="liunian-strip">${liuInit}</div></div>`;
}

function wireDayunStrip(dayun, insight) {
  const strip = document.getElementById("dayun-strip");
  const liuBox = document.getElementById("liunian-strip");
  if (!strip || !liuBox || !dayun?.length) return;
  const cy = insight?.current_year_liunian;
  const nowYear = new Date().getFullYear();
  const showLiunian = (idx) => {
    const d = dayun[idx];
    if (!d) return;
    strip.querySelectorAll(".dayun-strip-item").forEach((btn, i) => {
      const sel = i === idx;
      btn.classList.toggle("is-selected", sel);
      btn.setAttribute("aria-pressed", sel ? "true" : "false");
    });
    liuBox.innerHTML = (d.liunian || [])
      .map((ln) => {
        const isCur = cy?.year === ln.year || ln.year === nowYear;
        return `<span class="liunian-chip${isCur ? " is-current" : ""}">${escapeHtml(ln.ganzhi)}<small>${ln.year}</small></span>`;
      })
      .join("");
  };
  strip.querySelectorAll(".dayun-strip-item").forEach((btn) => {
    btn.addEventListener("click", () => showLiunian(Number(btn.dataset.idx)));
  });
  const defaultIdx = Number(strip.dataset.defaultIdx) || 0;
  showLiunian(defaultIdx);
  strip.querySelector(".is-current")?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
}

function renderDayunTable(dayun, insight) {
  const cd = insight?.current_dayun;
  const rows = (dayun || [])
    .map(
      (d, i) => `
      <tr class="dayun-row${cd?.ganzhi === d.ganzhi ? " is-current" : ""}" data-idx="${i}">
        <td><strong>${d.ganzhi}</strong></td>
        <td>${d.start_year} — ${d.end_year}</td>
        <td>${d.start_age} — ${d.end_age} 岁</td>
        <td class="liunian-cell">${(d.liunian || []).map((l) => `<span class="badge">${l.ganzhi}(${l.year})</span>`).join("")}</td>
      </tr>`
    )
    .join("");
  return `<div class="table-wrap dayun-table-desktop"><table><thead><tr><th>干支</th><th>年份</th><th>年龄</th><th>流年</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderDayunCards(dayun) {
  return (dayun || [])
    .map(
      (d, i) => `
      <div class="dayun-card" data-idx="${i}">
        <button type="button" class="dayun-card-head">
          <strong>${d.ganzhi}</strong>
          <span>${d.start_year}—${d.end_year} · ${d.start_age}—${d.end_age}岁</span>
        </button>
        <div class="liunian-badges hidden">${(d.liunian || []).map((l) => `<span class="badge">${l.ganzhi} ${l.year}</span>`).join("")}</div>
      </div>`
    )
    .join("");
}

function tierBadge(tier) {
  const map = {
    assert: { cls: "conf-badge-强", label: "直断" },
    hint: { cls: "conf-badge-中", label: "结构提示" },
    structure: { cls: "conf-badge-弱", label: "宫位" },
  };
  const b = map[tier] || { cls: "conf-badge-中", label: tier || "" };
  return `<span class="conf-badge ${b.cls}">${escapeHtml(b.label)}</span>`;
}

function renderDuanshi(duanshi) {
  if (!duanshi?.items?.length) return "";
  const blocks = duanshi.items.map((item) => {
    const reasons = (item.reasons || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
    const windows = (item.windows || []).map(
      (w) => `<li>大运 ${escapeHtml(w.dayun || "")}（${escapeHtml(w.years || "")} / ${escapeHtml(w.ages || "")}）${escapeHtml(w.note || "")}</li>`
    ).join("");
    const tier = item.display_tier || item.publish_tier || "";
    const verdict = item.display_verdict || item.verdict || "";
    const evidence = reasons && tier === "assert"
      ? `<details class="evidence-details" open><summary class="evidence-summary">依据（为何如此断）</summary><ul class="duanshi-reasons">${reasons}</ul></details>`
      : "";
    return `<div class="duanshi-item duanshi-tier-${escapeHtml(tier)}">
      <div class="duanshi-head">
        <span class="topic-badge">断·${escapeHtml(item.topic || "")}</span>
        ${tierBadge(tier)}
        <span class="duanshi-verdict">${escapeHtml(verdict)}</span>
      </div>
      ${evidence}
      ${windows && tier === "assert" ? `<p class="duanshi-windows-title">应期</p><ul class="duanshi-windows">${windows}</ul>` : ""}
    </div>`;
  }).join("");
  const note = duanshi.publish_note ? `<p class="rule-trust-note">${escapeHtml(duanshi.publish_note)}</p>` : "";
  return `<div class="panel-card duanshi-panel"><div class="panel-card-header"><h4 class="panel-card-title">断事</h4></div><div class="panel-card-body">${note}${blocks}</div></div>`;
}

function renderSanguan(sanguan) {
  if (!sanguan?.gates?.length) return "";
  const chuan = (sanguan.chuan || []).length
    ? `<p class="sanguan-chuan">盲派穿象：${escapeHtml(sanguan.chuan.join("、"))}</p>`
    : "";
  const blocks = sanguan.gates.map((g) => {
    const tier = g.display_tier || g.publish_tier || "";
    const verdict = g.display_verdict || g.verdict || "";
    const signals = (g.signals || []).map(
      (s) => `<li><span class="sanguan-school">${escapeHtml(s.school || "")}</span> ${escapeHtml(s.text || "")}</li>`
    ).join("");
    const windows = (g.windows || []).map(
      (w) => `<li>大运 ${escapeHtml(w.dayun || "")}（${escapeHtml(w.years || "")}）${escapeHtml(w.note || "")}</li>`
    ).join("");
    const evidence = signals && tier === "assert"
      ? `<details class="evidence-details" open><summary class="evidence-summary">各家印证</summary><ul class="sanguan-signals">${signals}</ul></details>`
      : "";
    return `<div class="sanguan-gate sanguan-tier-${escapeHtml(tier)}">
      <div class="sanguan-head">
        <span class="topic-badge">${escapeHtml(g.name || "")}</span>
        ${tierBadge(tier)}
        <span class="sanguan-verdict">${escapeHtml(verdict)}</span>
      </div>
      ${evidence}
      ${windows && tier === "assert" ? `<p class="sanguan-windows-title">应期</p><ul class="sanguan-windows">${windows}</ul>` : ""}
    </div>`;
  }).join("");
  const summary = sanguan.summary ? `<p class="sanguan-summary">${escapeHtml(sanguan.summary)}</p>` : "";
  const note = sanguan.publish_note
    ? `<p class="sanguan-publish-note">${escapeHtml(sanguan.publish_note)}</p>`
    : "";
  return `<div class="panel-card sanguan-panel"><div class="panel-card-header"><h4 class="panel-card-title">六亲人事 · 多维验证</h4></div><div class="panel-card-body"><p class="sanguan-role-note">在观命总观之后，对父母 / 兄弟 / 子女等作盲派、子平、千里交叉印证；仅展示高置信关。</p>${note}${summary}${chuan}${blocks}</div></div>`;
}

function renderGuanming(guanming) {
  if (!guanming?.layers?.length) return "";
  const layers = guanming.layers
    .filter((layer) => layer.id !== "shensha")
    .map((layer) => {
    const lines = (layer.lines || []).map((ln) => `<li>${escapeHtml(ln)}</li>`).join("");
    return `<div class="guanming-layer guanming-${escapeHtml(layer.id || "")}">
      <h5 class="guanming-layer-title">${escapeHtml(layer.name || "")} <span class="guanming-layer-sub">${escapeHtml(layer.subtitle || "")}</span></h5>
      <ul class="guanming-layer-lines">${lines}</ul>
    </div>`;
  }).join("");
  const verse = guanming.verse
    ? `<blockquote class="guanming-verse">${escapeHtml(guanming.verse)}</blockquote>`
    : "";
  return `<div class="panel-card guanming-panel">
    <div class="panel-card-header"><h4 class="panel-card-title">观命总观 · 滴天髓</h4></div>
    <div class="panel-card-body">
      <p class="guanming-summary">${escapeHtml(guanming.summary || "")}</p>
      <p class="guanming-method">${escapeHtml(guanming.method || "")}</p>
      ${verse}
      <div class="guanming-layers">${layers}</div>
    </div>
  </div>`;
}

function renderRuleDetails(insight) {
  const de = insight.de_ling || {};
  const tg = insight.tong_gen || {};
  const geju = insight.geju || {};
  const purity = geju.purity || {};
  const ys = insight.yongshen || {};
  const bodyPat = insight.pattern || {};
  const sn = insight.stem_nature || {};
  return `
    <p>得令：${escapeHtml(de.status || "—")} · 通根：${escapeHtml(tg.summary || "—")}</p>
    ${geju.type ? `<p><strong>格局</strong> ${escapeHtml(geju.type)}（${escapeHtml(geju.origin || "")}）清纯${escapeHtml(purity.level || "—")} — ${escapeHtml(geju.note || "")}</p>` : ""}
    ${bodyPat.type ? `<p><strong>体用</strong> ${escapeHtml(bodyPat.type)} — ${escapeHtml(bodyPat.note || "")}</p>` : ""}
    ${ys.summary ? `<p><strong>喜用倾向</strong> ${escapeHtml(ys.summary)}</p>` : ""}
    ${sn.verse ? `<div class="ditiansui-panel"><p class="ditiansui-panel-title">滴天髓</p><p class="ditiansui-verse">${escapeHtml(sn.verse)}</p></div>` : ""}
    <p><strong>调候</strong> ${escapeHtml(insight.tiao_hou || "")}</p>
    <p class="insight-note">${escapeHtml(insight.day_master_strength_note || "")}</p>`;
}

function renderLifeStage(lifeStage) {
  if (!lifeStage?.focus_areas?.length) return "";
  const chips = lifeStage.focus_areas
    .map((f) => {
      const pri = f.priority === "primary" ? " focus-chip-primary" : "";
      return `<span class="focus-chip${pri}">${escapeHtml(f.label)}</span>`;
    })
    .join("");
  return `<div class="panel-card lifestage-panel">
    <div class="panel-card-header"><h4 class="panel-card-title">人生阶段 · 当前关切</h4></div>
    <div class="panel-card-body">
      <p class="lifestage-summary">虚岁 <strong>${escapeHtml(String(lifeStage.age ?? ""))}</strong> · ${escapeHtml(lifeStage.stage_label || "")} · 侧重 ${escapeHtml(lifeStage.focus_summary || "")}</p>
      <p class="rule-trust-note">同一命盘结构完整计算；按年龄段调整解读侧重，童年不断婚育应期，晚年不强调学业。</p>
      <div class="focus-chips">${chips}</div>
    </div>
  </div>`;
}

function renderHighlightsPanel(insight) {
  const items = (insight.highlights || []).map(
    (h) => `<li class="highlight-item">${escapeHtml(h)}</li>`
  ).join("");
  const sources = (insight.sources || ["子平", "滴天髓", "穷通宝鉴"]).join(" · ");
  return `
    <div class="insight-stack">
      ${renderLifeStage(insight.life_stage)}
      ${renderGuanming(insight.guanming)}
      <div class="panel-card highlights-panel">
        <div class="panel-card-header"><h3 class="panel-card-title">命局要点</h3></div>
        <div class="panel-card-body">
          <p class="rule-trust-note">结构层据盘上可见信息直述；断事分「直断 / 结构提示 / 宫位」，与当前人生阶段一致。</p>
          <p class="highlights-source">综参 ${escapeHtml(sources)}</p>
          <ul class="highlights-list">${items || "<li class=\"highlight-item\">暂无摘要</li>"}</ul>
          <details class="details-more sub-panel-details" open>
            <summary>规则明细（体用 / 格局 / 调候）</summary>
            <div class="details-body">${renderRuleDetails(insight)}</div>
          </details>
        </div>
      </div>
      ${renderDuanshi(insight.duanshi)}
      ${renderSanguan(insight.sanguan)}
    </div>`;
}

function renderChart(data) {
  const m = data.meta || {};
  const wx = data.wuxing_stats || {};
  const insight = data.insight || {};
  const rel = (data.pillars_relations || [])
    .map((r) => `<span class="relation-tag">${escapeHtml(r)}</span>`)
    .join("");
  const qy = data.qiyun || {};

  const xyBlock = (data.xiaoyun || []).length
    ? `<div class="table-wrap"><table><thead><tr><th>年份</th><th>小运</th><th>年龄</th><th>流年</th></tr></thead><tbody>${data.xiaoyun
        .slice(0, 12)
        .map(
          (x) =>
            `<tr><td>${x.year}</td><td>${x.ganzhi}</td><td>${x.age} 岁</td><td>${x.liunian?.ganzhi || ""} (${x.liunian?.year || ""})</td></tr>`
        )
        .join("")}</tbody></table></div>`
    : "";

  return `
    <div class="chart-page">
    <header class="chart-topbar">
      <a href="/" class="chart-back">← 重新排盘</a>
      <div class="chart-topbar-actions">
        <button type="button" class="btn btn-secondary btn-sm" id="btn-copy-link">分享链接</button>
        <button type="button" class="btn btn-secondary btn-sm" id="btn-export-md">导出</button>
      </div>
    </header>
    <nav class="chart-nav" id="chart-nav" role="tablist" aria-label="命盘分区">
      <button type="button" class="chart-nav-btn active" role="tab" aria-selected="true" data-target="sec-meta">基本</button>
      <button type="button" class="chart-nav-btn" role="tab" aria-selected="false" data-target="sec-di">命盘</button>
      <button type="button" class="chart-nav-btn" role="tab" aria-selected="false" data-target="sec-tian">细盘</button>
      <button type="button" class="chart-nav-btn" role="tab" aria-selected="false" data-target="sec-ai">问 AI</button>
    </nav>
    <div id="chart-sticky-summary" class="chart-sticky-summary chart-info-strip">
      <span class="sticky-ganzhi">${(data.pillars || []).map((p) => p.ganzhi).join(" ")}</span>
      <span class="sticky-dm">${escapeHtml(m.gender_label || "")} · 日主 ${escapeHtml(m.day_master || "")} · ${escapeHtml(insight.geju?.type || insight.day_master_strength || "")}</span>
      <span class="sticky-birth">${escapeHtml(m.birth_time?.solar || "")}</span>
    </div>

    <section class="section-block section-card" id="sec-meta">
      <h2 class="section-title">基本信息</h2>
      <div class="meta-grid meta-grid-dense">
        <div class="meta-item"><div class="label">性别</div><div class="value">${escapeHtml(m.gender_label || "")}</div></div>
        <div class="meta-item"><div class="label">生肖</div><div class="value">${escapeHtml(m.zodiac || "")}</div></div>
        <div class="meta-item"><div class="label">虚岁</div><div class="value">${escapeHtml(String(m.age ?? ""))} 岁</div></div>
        <div class="meta-item"><div class="label">日主</div><div class="value">${escapeHtml(m.day_master || "")}（${escapeHtml(m.day_master_wuxing || "")}）</div></div>
        <div class="meta-item"><div class="label">胎元</div><div class="value">${escapeHtml(m.tai_yuan || "—")}</div></div>
        <div class="meta-item"><div class="label">命宫</div><div class="value">${escapeHtml(m.ming_gong || "—")}</div></div>
        <div class="meta-item"><div class="label">身宫</div><div class="value">${escapeHtml(m.shen_gong || "—")}</div></div>
        <div class="meta-item"><div class="label">十二长生</div><div class="value">${escapeHtml(m.day_dishi || "—")}</div></div>
      </div>
      <p class="birth-time-note">阳历 ${escapeHtml(m.birth_time?.solar || "")} · 农历 ${escapeHtml(m.birth_time?.lunar || "")}</p>
      <div class="insight-panel">
        <p>强弱 <strong>${insight.day_master_strength || "—"}</strong>（${insight.strength_score ?? "—"}）
        ${insight.geju?.type ? ` · 格局 <strong>${insight.geju.type}</strong>` : ""}
        ${insight.current_dayun ? ` · 当前大运 <strong>${insight.current_dayun.ganzhi}</strong>` : ""}</p>
        ${insight.yongshen?.summary ? `<p class="yongshen-line">喜用：${escapeHtml(insight.yongshen.summary)}</p>` : ""}
      </div>
      <h3 class="subsection-title">五行分析</h3>
      <div class="wuxing-chart">${renderWuxingChart(wx)}</div>
      ${renderHighlightsPanel(insight)}
    </section>

    <section class="section-block section-card" id="sec-di">
      <h2 class="section-title">基本命盘</h2>
      ${renderPillarGrid(data.pillars || [])}
      ${rel ? `<div class="relation-tags">${rel}</div>` : ""}
      <details class="bazi-cards-toggle">
        <summary>卡片视图</summary>
        <div class="bazi-board">${(data.pillars || []).map(renderPillar).join("")}</div>
      </details>
    </section>

    <section class="section-block section-card" id="sec-tian">
      <h2 class="section-title">专业细盘</h2>
      <p class="qiyun-desc">${escapeHtml(qy.description || "")}</p>
      ${renderDayunStrip(data.dayun, insight)}
      ${renderDayunTable(data.dayun, insight)}
      <div class="dayun-cards">${renderDayunCards(data.dayun)}</div>
      ${xyBlock}
    </section>

    <section class="section-block section-card section-ai ai-panel" id="sec-ai">
      <header class="ai-panel-head">
        <div class="ai-panel-intro">
          <h2 class="section-title">问 · AI · 子平直断</h2>
          <p class="ai-panel-desc">先依观命总观展开，再论已发布断事与六亲印证 · 非开放闲聊</p>
        </div>
        <span class="analysis-style-badge style-ziping">子平直断</span>
      </header>
      <div class="ai-panel-toolbar">
        <button type="button" class="btn btn-primary" id="btn-analyze">开始解读</button>
        <button type="button" class="btn btn-secondary hidden" id="btn-copy-analysis">复制解读</button>
      </div>
      <div id="ai-loading" class="ai-loading hidden" aria-live="polite">
        <div class="spinner"></div>
        <p class="ai-loading-title">问元解读中</p>
        <p class="ai-loading-desc">正在锚定观命总观与规则层…</p>
      </div>
      <div id="ai-error" class="alert alert-error hidden"></div>
      <div id="ai-empty" class="ai-empty-state">
        <p class="ai-empty-title">尚未解读</p>
        <p class="ai-empty-desc">点击「开始解读」，AI 将按八个章节流式输出 L1 直断。</p>
      </div>
      <div id="ai-result-wrap" class="ai-result-card hidden">
        <div class="ai-result-meta">
          <span id="ai-time" class="analysis-time"></span>
        </div>
        <div id="ai-result" class="analysis-content"></div>
      </div>
      <div class="ai-ask-block">
        <div class="ai-ask-head">
          <h3 class="ai-ask-title">就盘追问</h3>
        </div>
        <div class="l2-chips" id="l2-chips"></div>
        <div id="ask-history" class="ask-history"></div>
        <div class="ask-input-bar">
          <textarea id="ask-input" rows="2" placeholder="输入你想问的问题…" maxlength="500"></textarea>
          <button type="button" class="btn btn-primary" id="btn-ask">发送</button>
        </div>
      </div>
    </section>
    </div>`;
}

function renderAnalysis(text, streaming = false) {
  const wrap = document.getElementById("ai-result-wrap");
  const empty = document.getElementById("ai-empty");
  const timeEl = document.getElementById("ai-time");
  const result = document.getElementById("ai-result");
  const copyBtn = document.getElementById("btn-copy-analysis");
  if (!result) return;
  if (timeEl) timeEl.textContent = new Date().toLocaleString("zh-CN", { hour12: false });
  result.innerHTML = markdownToHtml(text) + (streaming ? '<span class="stream-cursor">▍</span>' : "");
  wrap?.classList.remove("hidden");
  empty?.classList.add("hidden");
  copyBtn?.classList.remove("hidden");
}

function appendAskMessage(role, content) {
  const box = document.getElementById("ask-history");
  if (!box) return;
  const div = document.createElement("div");
  div.className = `ask-msg ask-${role}`;
  if (role === "assistant") {
    div.innerHTML = markdownToHtml(content);
  } else {
    div.textContent = content;
  }
  box.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "nearest" });
}


function buildMarkdownExport(chart, insight, analysis, history) {
  const m = chart.meta || {};
  let md = `# 问元命盘\n\n`;
  md += `- 阳历：${m.birth_time?.solar || ""}\n`;
  md += `- 农历：${m.birth_time?.lunar || ""}\n`;
  md += `- 日主：${m.day_master}（${m.day_master_wuxing}）\n\n`;
  md += `## 四柱\n\n`;
  (chart.pillars || []).forEach((p) => {
    md += `- ${p.label} ${p.ganzhi} 十神${p.shishen} 长生${p.changsheng || ""} 旬空${p.xunkong || ""}\n`;
  });
  md += `\n## 命局要点（子平综参）\n\n`;
  md += `- 强弱：${insight?.day_master_strength}\n`;
  md += `- 格局：${insight?.geju?.type || ""}（${insight?.geju?.note || ""}）\n`;
  md += `- 喜用倾向：${insight?.yongshen?.summary || ""}\n`;
  md += `- 调候：${insight?.tiao_hou || ""}\n`;
  md += `- 体用：${insight?.pattern?.type || ""}\n`;
  (insight?.highlights || []).forEach((h) => { md += `- ${h}\n`; });
  const ds = insight?.duanshi?.items || [];
  if (ds.length) {
    md += `\n## 断事\n\n`;
    ds.forEach((item) => { md += `- **${item.topic}** [${item.level}] ${item.verdict}\n`; });
  }
  const sg = insight?.sanguan?.gates || [];
  if (sg.length) {
    md += `\n## 过三关\n\n`;
    sg.forEach((g) => { md += `- **${g.name}** [${g.confidence}] ${g.verdict}\n`; });
  }
  md += `\n`;
  if (analysis) md += `## AI 解读\n\n${analysis}\n\n`;
  if (history?.length) {
    md += `## 问答\n\n`;
    history.forEach((h) => { md += `**${h.role}**: ${h.content}\n\n`; });
  }
  md += `\n> 由问元导出，仅供文化参考。\n`;
  return md;
}

function wireChartInteractions(state) {
  setupNavObserver();
  setupChartNavA11y();

  wireDayunStrip(state.chart.dayun, state.chart.insight);

  document.querySelectorAll(".section-header").forEach((btn) => {
    const bodyId = btn.dataset.target;
    const body = document.getElementById(bodyId);
    const collapsed = body?.classList.contains("collapsed");
    btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    btn.addEventListener("click", () => {
      body?.classList.toggle("collapsed");
      const sec = btn.closest(".collapsible");
      sec?.classList.toggle("is-collapsed");
      btn.setAttribute("aria-expanded", body?.classList.contains("collapsed") ? "false" : "true");
    });
  });

  document.querySelectorAll(".dayun-card-head").forEach((btn) => {
    btn.addEventListener("click", () => {
      const card = btn.closest(".dayun-card");
      card?.classList.toggle("expanded");
      card?.querySelector(".liunian-badges")?.classList.toggle("hidden");
    });
  });

  document.getElementById("btn-export-md")?.addEventListener("click", () => {
    const md = buildMarkdownExport(state.chart, state.chart.insight, state.analysis || "", state.history);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `wenyuan-${state.input?.birth_date || "chart"}.md`;
    a.click();
    showToast("Markdown 已导出");
  });

  const copyLinkBtn = document.getElementById("btn-copy-link");
  const modal = document.getElementById("privacy-modal");
  copyLinkBtn?.addEventListener("click", () => {
    openModal(modal, copyLinkBtn);
  });
  document.getElementById("modal-confirm")?.addEventListener("click", () => {
    navigator.clipboard.writeText(getShareUrl(state.input)).then(() => showToast("链接已复制"));
    closeModal(modal);
  });
  document.getElementById("modal-cancel")?.addEventListener("click", () => closeModal(modal));
  modal?.querySelector(".modal-backdrop")?.addEventListener("click", () => closeModal(modal));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && !modal.classList.contains("hidden")) closeModal(modal);
  });

  document.getElementById("btn-copy-analysis")?.addEventListener("click", () => {
    const text = state.analysis || "";
    if (text) navigator.clipboard.writeText(text).then(() => showToast("解读已复制"));
  });

  async function runAnalyze() {
    const loading = document.getElementById("ai-loading");
    const err = document.getElementById("ai-error");
    const analyzeBtn = document.getElementById("btn-analyze");
    hideError(err);
    loading?.classList.remove("hidden");
    document.getElementById("ai-empty")?.classList.add("hidden");
    if (analyzeBtn) analyzeBtn.disabled = true;
    const result = document.getElementById("ai-result");
    if (result) result.innerHTML = "";
    document.getElementById("ai-result-wrap")?.classList.remove("hidden");

    try {
      const streamRender = throttle((full) => renderAnalysis(full, true), 80);
      const text = await API.analyze(state.chart, AI_STYLE, state.chart.insight, streamRender);
      state.analysis = text;
      renderAnalysis(text, false);
      saveAiCache(state.input, { analysis: state.analysis });
    } catch (e) {
      showError(err, e.message || "分析失败");
    } finally {
      loading?.classList.add("hidden");
      if (analyzeBtn) analyzeBtn.disabled = false;
    }
  }

  document.getElementById("btn-analyze")?.addEventListener("click", () => runAnalyze());

  const askInput = document.getElementById("ask-input");
  askInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      runAsk();
    }
  });

  async function runAsk(question) {
    const askInput = document.getElementById("ask-input");
    const askBtn = document.getElementById("btn-ask");
    const q = (question || document.getElementById("ask-input")?.value || "").trim();
    if (!q) return;
    appendAskMessage("user", q);
    if (askInput) askInput.value = "";
    if (askBtn) askBtn.disabled = true;
    if (askInput) askInput.disabled = true;
    state.history.push({ role: "user", content: q });

    const err = document.getElementById("ai-error");
    hideError(err);
    const placeholder = document.createElement("di" + "v");
    placeholder.className = "ask-msg ask-assistant is-pending";
    placeholder.innerHTML = '<span class="mini-spinner"></span><span>思考中…</span>';
    document.getElementById("ask-history")?.appendChild(placeholder);

    try {
      let answer = "";
      answer = await API.ask(
        state.chart,
        q,
        AI_STYLE,
        state.chart.insight,
        state.analysis || "",
        state.history.slice(0, -1),
        (full) => {
          placeholder.innerHTML = markdownToHtml(full);
        }
      );
      placeholder.innerHTML = markdownToHtml(answer);
      state.history.push({ role: "assistant", content: answer });
      saveAiCache(state.input, { analysis: state.analysis });
    } catch (e) {
      placeholder.remove();
      state.history.pop();
      showError(err, e.message || "问答失败");
    } finally {
      if (askBtn) askBtn.disabled = false;
      if (askInput) askInput.disabled = false;
    }
  }

  document.getElementById("btn-ask")?.addEventListener("click", () => runAsk());
  document.getElementById("ask-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      runAsk();
    }
  });

  const l2 = document.getElementById("l2-chips");
  const questions = state.chart.insight?.l2_questions || [];
  if (l2 && questions.length) {
    l2.innerHTML = questions.map(
      (q) => `<button type="button" class="l2-chip" data-q="${escapeHtml(q)}">${escapeHtml(q)}</button>`
    ).join("");
    l2.querySelectorAll(".l2-chip").forEach((btn) => {
      btn.addEventListener("click", () => {
        const askInput = document.getElementById("ask-input");
        if (askInput) askInput.value = btn.dataset.q || "";
        runAsk(btn.dataset.q || "");
      });
    });
  }

}


function historyLabel(chart, input) {
  const dm = chart?.meta?.day_master || "";
  const g = input?.gender === "female" ? "女" : "男";
  return `${input?.birth_date || ""} ${g} · ${dm}`;
}

function formatBirthSummary(form) {
  const p = readBirthFromForm(form);
  const cal = p.date_type === "lunar" ? "农历" : "公历";
  const leap = p.is_leap_month ? " · 闰月" : "";
  const g = p.gender === "female" ? "女" : "男";
  return `${p.birth_date} ${p.birth_time} · ${g} · ${cal}${leap}`;
}

function syncBirthSummary(form) {
  const el = document.getElementById("birth-summary");
  if (!el || !form) return;
  el.textContent = formatBirthSummary(form);
}

function wireBirthFormLive(form) {
  if (!form) return;
  const onChange = () => syncBirthSummary(form);
  form.querySelectorAll("select, input").forEach((el) => {
    el.addEventListener("change", onChange);
  });
  syncBirthSummary(form);
}

async function navigateWithChart(input, chart) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chart));
  sessionStorage.setItem(INPUT_KEY, JSON.stringify(input));
  cacheChartPayload(encodeSharePayload(input), chart);
  clearAiCache(input);
  saveHistory(input, historyLabel(chart, input));
  const url = getShareUrl(input);
  location.href = url;
}

function initIndexPage() {
  const form = document.getElementById("chart-form");
  const errEl = document.getElementById("form-error");
  const btn = document.getElementById("submit-btn");
  const lunarHint = document.getElementById("lunar-hint");
  const leapGroup = document.getElementById("leap-month-group");
  const leapBanner = document.getElementById("leap-month-banner");

  const yearEl = birthField(form, "birth_year");
  const monthEl = birthField(form, "birth_month");
  const hourEl = birthField(form, "birth_hour");
  const minuteEl = birthField(form, "birth_minute");

  fillBirthYearOptions(yearEl);
  if (monthEl) {
    monthEl.innerHTML = Array.from({ length: 12 }, (_, i) => {
      const v = i + 1;
      return `<option value="${v}">${v} 月</option>`;
    }).join("");
  }
  if (hourEl) {
    hourEl.innerHTML = Array.from({ length: 24 }, (_, i) =>
      `<option value="${i}">${pad2(i)} 时</option>`
    ).join("");
  }
  fillBirthMinuteOptions(minuteEl);
  applyBirthToForm(form, DEFAULT_BIRTH);
  syncBirthDayOptions(form);

  yearEl?.addEventListener("change", () => syncBirthDayOptions(form));
  monthEl?.addEventListener("change", () => syncBirthDayOptions(form));

  const renderHist = () => {
    const list = loadHistory();
    const card = document.getElementById("history-card");
    const ul = document.getElementById("history-list");
    if (!list.length || !ul) return;
    card?.classList.remove("hidden");
    ul.innerHTML = list
      .map(
        (h) =>
          `<li class="history-item"><a href="${getShareUrl(h.input)}" class="history-link"><span class="history-label">${escapeHtml(h.label || h.input.birth_date)}</span><span class="history-meta">${new Date(h.ts).toLocaleDateString("zh-CN")}</span></a></li>`
      )
      .join("");
  };
  renderHist();

  const syncLunarUi = () => {
    const lunar = form?.querySelector('input[name="date_type"]:checked')?.value === "lunar";
    lunarHint?.classList.toggle("hidden", !lunar);
    leapGroup?.classList.toggle("hidden", !lunar);
    leapBanner?.classList.toggle("hidden", !lunar);
  };
  form?.querySelectorAll('input[name="date_type"]').forEach((el) => {
    el.addEventListener("change", () => {
      syncLunarUi();
      syncBirthSummary(form);
    });
  });
  syncLunarUi();
  wireBirthFormLive(form);

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError(errEl);
    setBtnLoading(btn, true, "开始排盘");
    const payload = readBirthFromForm(form);
    try {
      const res = await API.chart(payload);
      if (!res.success) {
        showError(errEl, res.error || "排盘失败");
        return;
      }
      await navigateWithChart(payload, res.data);
    } catch (err) {
      showError(errEl, err.message || "网络错误");
    } finally {
      setBtnLoading(btn, false, "开始排盘");
    }
  });
}

async function initChartPage() {
  const root = document.getElementById("chart-root");
  const loading = document.getElementById("chart-loading");
  const params = new URLSearchParams(location.search);
  const share = params.get("s");
  const forceFresh = params.get("fresh") === "1";

  let input = null;
  let chart = null;

  try {
    if (share) {
      input = decodeSharePayload(share);
      chart = forceFresh ? null : loadCachedChart(share);
      if (!chart) {
        loading?.setAttribute("aria-busy", "true");
        const res = await API.chart(input);
        if (!res.success) throw new Error(res.error || "排盘失败");
        chart = res.data;
        cacheChartPayload(share, chart);
      }
    } else {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) throw new Error("暂无命盘数据");
      chart = JSON.parse(raw);
      input = JSON.parse(sessionStorage.getItem(INPUT_KEY) || "null");
    }
  } catch (e) {
    loading?.classList.add("hidden");
    root.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}，请先 <a href="/">排盘</a></div>`;
    return;
  }

  loading?.classList.add("hidden");
  loading?.setAttribute("aria-busy", "false");
  if (forceFresh && share) {
    const u = new URL(location.href);
    u.searchParams.delete("fresh");
    history.replaceState(null, "", u.pathname + u.search);
  }
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chart));
  if (input) sessionStorage.setItem(INPUT_KEY, JSON.stringify(input));

  const cache = input ? loadAiCache(input) : null;
  const normalized = normalizeAiCache(cache);
  const state = {
    chart,
    input: input || {},
    analysis: normalized.analysis,
    history: [],
  };

  root.innerHTML = renderChart(chart);
  root.querySelector(".chart-page")?.classList.add("is-ready");
  wireChartInteractions(state);

  if (state.analysis) renderAnalysis(state.analysis);
}

window.Wenyuan = {
  API,
  renderChart,
  renderAnalysis,
  showError,
  hideError,
  initIndexPage,
  initChartPage,
  encodeSharePayload,
  decodeSharePayload,
  getShareUrl,
  STORAGE_KEY,
};
