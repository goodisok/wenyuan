/** 问元 · 前端 v1.2 · 子平综参 */
const STORAGE_KEY = "wenyuan_chart";
const HISTORY_KEY = "wenyuan_history";
const INPUT_KEY = "wenyuan_input";
const MAX_HISTORY = 20;
const L3_MAX_ROUNDS = 8;
const SHARE_VERSION = 1;

const L2_FIXED = ["当前大运对我意味着什么？", "我的五行平衡吗？"];

const WUXING_MAP = { 木: "wood", 火: "fire", 土: "earth", 金: "metal", 水: "water" };

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
  localStorage.setItem(aiCacheKey(input), JSON.stringify(data));
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
  const max = Math.max(...Object.values(wx || {}), 1);
  return Object.entries(wx || {})
    .map(([k, v]) => {
      const pct = Math.round((Number(v) / max) * 100);
      return `<div class="wuxing-bar-row">
        <span class="wuxing-bar-label wuxing-${WUXING_MAP[k] || ""}">${k}</span>
        <div class="wuxing-bar-track"><div class="wuxing-bar-fill wuxing-${WUXING_MAP[k] || ""}" style="width:${pct}%"></div></div>
        <span class="wuxing-bar-val">${v}</span>
      </div>`;
    })
    .join("");
}

function renderPillar(p) {
  const cg = (p.dizhi.canggan || [])
    .map((c) => {
      const ss = c.shishen ? `·${c.shishen}` : "";
      return `<span class="canggan-tag ${wuxingClass(c.color)}">${c.name}${ss}</span>`;
    })
    .join("");
  const cs = p.changsheng ? `<div class="pillar-changsheng">${escapeHtml(p.changsheng)}</div>` : "";
  const xk = p.xunkong ? `<div class="pillar-xunkong">旬空 ${escapeHtml(p.xunkong)}</div>` : "";
  return `
    <div class="pillar">
      <div class="pillar-label">${p.label}</div>
      <div class="pillar-ganzhi">${p.ganzhi}</div>
      <div class="stem ${wuxingClass(p.tiangan.color)}">${p.tiangan.name} · ${p.tiangan.wuxing}</div>
      <div class="branch ${wuxingClass(p.dizhi.color)}">${p.dizhi.name} · ${p.dizhi.wuxing}</div>
      <div class="canggan-list">${cg}</div>
      ${cs}
      ${xk}
      <div class="pillar-meta">${p.shishen}<br>${p.nayin}</div>
    </div>`;
}

function renderDayunTable(dayun) {
  const rows = (dayun || [])
    .map(
      (d, i) => `
      <tr class="dayun-row" data-idx="${i}">
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

function renderDuanshi(duanshi) {
  if (!duanshi?.items?.length) return "";
  const blocks = duanshi.items.map((item) => {
    const reasons = (item.reasons || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
    const windows = (item.windows || []).map(
      (w) => `<li>大运 ${escapeHtml(w.dayun || "")}（${escapeHtml(w.years || "")} / ${escapeHtml(w.ages || "")}）${escapeHtml(w.note || "")}</li>`
    ).join("");
    return `<div class="duanshi-item duanshi-level-${escapeHtml(item.level || "")}">
      <p><strong>断·${escapeHtml(item.topic || "")}</strong>
        <span class="duanshi-verdict">${escapeHtml(item.verdict || "")}</span>
        <span class="duanshi-level">[${escapeHtml(item.level || "")}]</span></p>
      ${reasons ? `<ul class="duanshi-reasons">${reasons}</ul>` : ""}
      ${windows ? `<p class="duanshi-windows-title">应期</p><ul class="duanshi-windows">${windows}</ul>` : ""}
    </div>`;
  }).join("");
  return `<div class="duanshi-panel"><h4 class="subsection-title">断事</h4>${blocks}</div>`;
}

function renderRuleDetails(insight) {
  const de = insight.de_ling || {};
  const tg = insight.tong_gen || {};
  const geju = insight.geju || {};
  const purity = geju.purity || {};
  const ys = insight.yongshen || {};
  const sh = insight.shensha || {};
  const bodyPat = insight.pattern || {};
  const sn = insight.stem_nature || {};
  const shenshaItems = (sh.items || []).map(
    (i) => `<li><strong>${escapeHtml(i.name)}</strong> ${escapeHtml(i.position || "")} — ${escapeHtml(i.note || "")}</li>`
  ).join("");
  return `
    <p>得令：${escapeHtml(de.status || "—")} · 通根：${escapeHtml(tg.summary || "—")}</p>
    ${geju.type ? `<p><strong>格局</strong> ${escapeHtml(geju.type)}（${escapeHtml(geju.origin || "")}）清纯${escapeHtml(purity.level || "—")} — ${escapeHtml(geju.note || "")}</p>` : ""}
    ${bodyPat.type ? `<p><strong>体用</strong> ${escapeHtml(bodyPat.type)} — ${escapeHtml(bodyPat.note || "")}</p>` : ""}
    ${ys.summary ? `<p><strong>喜用倾向</strong> ${escapeHtml(ys.summary)}</p>` : ""}
    <p class="ditiansui-verse">${escapeHtml(sn.verse || "")}</p>
    <p><strong>调候</strong> ${escapeHtml(insight.tiao_hou || "")}</p>
    ${shenshaItems ? `<ul class="shensha-list">${shenshaItems}</ul>` : ""}
    <p class="insight-note">${escapeHtml(insight.day_master_strength_note || "")}</p>
    ${renderCitations(insight.citations)}`;
}

function renderCitations(citations) {
  if (!citations?.length) return "";
  const items = citations.map((c) => {
    const chapter = c.chapter ? `<span class="citation-chapter">${escapeHtml(c.chapter)}</span>` : "";
    const pillars = c.pillars ? `<span class="citation-pillars">例 ${escapeHtml(c.pillars)}</span> ` : "";
    const kind = c.kind === "case" ? "命例" : (c.kind === "tiao_hou" ? "调候" : "");
    const kindTag = kind ? `<span class="citation-kind">${kind}</span> ` : "";
    const commentary = c.commentary ? `<p class="citation-commentary">按：${escapeHtml(c.commentary)}</p>` : "";
    return `<li>
      <span class="citation-source">${escapeHtml(c.source || "")}</span>${chapter ? " " + chapter : ""}
      ${kindTag}${pillars}${escapeHtml(c.text || "")}
      ${commentary}
    </li>`;
  }).join("");
  return `
    <div class="citations-block">
      <h4 class="citations-title">典籍语料</h4>
      <ul class="citations-list">${items}</ul>
    </div>`;
}

function renderHighlightsPanel(insight) {
  const items = (insight.highlights || []).map(
    (h) => `<li class="highlight-item">${escapeHtml(h)}</li>`
  ).join("");
  const sources = (insight.sources || ["子平", "滴天髓", "穷通宝鉴"]).join(" · ");
  const corpusTotal = insight.corpus_meta?.total;
  const corpusNote = corpusTotal ? `<p class="corpus-meta">语料库 ${corpusTotal} 条 · 本次召回 ${(insight.citations || []).length} 条</p>` : "";
  return `
    <div class="highlights-panel">
      <h3 class="subsection-title">命局要点</h3>
      <p class="highlights-source">综参 ${escapeHtml(sources)}</p>
      ${corpusNote}
      <ul class="highlights-list">${items || "<li>暂无摘要</li>"}</ul>
      ${renderDuanshi(insight.duanshi)}
      <details class="details-more">
        <summary>查看规则明细</summary>
        <div class="details-body">${renderRuleDetails(insight)}</div>
      </details>
    </div>`;
}

function suggestL2Questions(insight) {
  const dynamic = [];
  const ds = insight?.duanshi?.items || [];
  const parent = ds.find((i) => i.topic === "父母" && (i.level === "强" || i.level === "中"));
  if (parent) dynamic.push(`父母宫断「${parent.verdict}」，应期在何运？`);
  const geju = insight?.geju || {};
  if (geju.type) dynamic.push(`「${geju.type}」对我事业与人事有何倾向？`);
  if (insight?.tiao_hou) dynamic.push("此盘寒暖调候上，日常宜注意什么？");
  if (insight?.yongshen?.summary) dynamic.push("喜用倾向与当前大运是否相合？");
  const cd = insight?.current_dayun;
  if (cd?.ganzhi) dynamic.push(`大运${cd.ganzhi}阶段的重点是什么？`);
  if ((insight?.tong_gen || {}).summary === "无根") dynamic.push("日主根气较弱，行事风格有何特点？");
  const strongest = insight?.wuxing_strongest || [];
  if (strongest.length) dynamic.push(`命局${strongest[0]}偏旺，日常宜如何调适？`);
  return [...L2_FIXED, ...dynamic.slice(0, 4)].slice(0, 6);
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

  const chips = suggestL2Questions(insight)
    .map((q) => `<button type="button" class="chip-btn" data-q="${escapeHtml(q)}">${escapeHtml(q)}</button>`)
    .join("");

  return `
    <nav class="chart-nav" id="chart-nav" aria-label="命盘分区">
      <button type="button" class="chart-nav-btn active" data-target="sec-meta">概览</button>
      <button type="button" class="chart-nav-btn" data-target="sec-di">四柱</button>
      <button type="button" class="chart-nav-btn" data-target="sec-tian">运势</button>
      <button type="button" class="chart-nav-btn" data-target="sec-ren">本命</button>
      <button type="button" class="chart-nav-btn" data-target="sec-ai">问 AI</button>
    </nav>
    <div id="chart-sticky-summary" class="chart-sticky-summary">
      <span class="sticky-ganzhi">${(data.pillars || []).map((p) => p.ganzhi).join(" ")}</span>
      <span class="sticky-dm">日主 ${m.day_master} · ${insight.geju?.type || insight.day_master_strength || ""}</span>
    </div>

    <section class="section-block" id="sec-meta">
      <h2 class="section-title">命主概览</h2>
      <div class="meta-grid">
        <div class="meta-item"><div class="label">性别</div><div class="value">${m.gender_label}</div></div>
        <div class="meta-item"><div class="label">生肖</div><div class="value">${m.zodiac}</div></div>
        <div class="meta-item"><div class="label">虚岁</div><div class="value">${m.age} 岁</div></div>
        <div class="meta-item"><div class="label">日主</div><div class="value">${m.day_master}（${m.day_master_wuxing}）</div></div>
        <div class="meta-item"><div class="label">十二长生</div><div class="value">${m.day_dishi || "—"}</div></div>
      </div>
      <p class="birth-time-note">阳历 ${m.birth_time?.solar || ""}<br>农历 ${m.birth_time?.lunar || ""}</p>
      <div class="meta-actions">
        <button type="button" class="btn btn-secondary" id="btn-copy-link">复制链接</button>
        <button type="button" class="btn btn-secondary" id="btn-export-md">导出 Markdown</button>
      </div>
      <div class="insight-panel">
        <p>日主 <strong>${m.day_master}</strong> 强弱 <strong>${insight.day_master_strength || "—"}</strong>
        （评分 ${insight.strength_score ?? "—"}）
        ${insight.geju?.type ? ` · 格局 <strong>${insight.geju.type}</strong>` : ""}</p>
        ${insight.yongshen?.summary ? `<p class="yongshen-line">喜用倾向：${escapeHtml(insight.yongshen.summary)}</p>` : ""}
        ${insight.current_dayun ? `<p>当前大运 ${insight.current_dayun.ganzhi}（${insight.current_dayun.start_year}-${insight.current_dayun.end_year}）</p>` : ""}
      </div>
      ${renderHighlightsPanel(insight)}
    </section>

    <section class="section-block" id="sec-di">
      <h2 class="section-title">地 · 四柱根基</h2>
      <div class="bazi-board">${(data.pillars || []).map(renderPillar).join("")}</div>
      ${rel ? `<div class="relation-tags">${rel}</div>` : ""}
      <h3 class="subsection-title">五行分布</h3>
      <div class="wuxing-chart">${renderWuxingChart(wx)}</div>
    </section>

    <section class="section-block collapsible" id="sec-tian">
      <button type="button" class="section-header" data-target="sec-tian-body">
        <h2 class="section-title">天 · 运势节律</h2><span class="section-chevron">▼</span>
      </button>
      <div class="section-body" id="sec-tian-body">
        <p class="qiyun-desc">${escapeHtml(qy.description || "")}</p>
        ${renderDayunTable(data.dayun)}
        <div class="dayun-cards">${renderDayunCards(data.dayun)}</div>
        ${xyBlock}
      </div>
    </section>

    <section class="section-block collapsible" id="sec-ren">
      <button type="button" class="section-header" data-target="sec-ren-body">
        <h2 class="section-title">人 · 本命特质</h2><span class="section-chevron">▼</span>
      </button>
      <div class="section-body" id="sec-ren-body">
        <div class="meta-grid">
          <div class="meta-item"><p class="label">胎元</p><p class="value">${m.tai_yuan || "—"}</p></div>
          <div class="meta-item"><p class="label">命宫</p><p class="value">${m.ming_gong || "—"}</p></div>
          <div class="meta-item"><p class="label">身宫</p><p class="value">${m.shen_gong || "—"}</p></div>
        </div>
      </div>
    </section>

    <section class="section-block" id="sec-ai">
      <h2 class="section-title">问 · AI</h2>
      <p class="ai-hint">锚定本盘解读与追问，非开放闲聊。L3 每命盘每标签页最多 ${L3_MAX_ROUNDS} 轮。</p>
      <div class="ai-toolbar">
        <button type="button" class="btn btn-secondary ai-style-btn" data-style="classic" id="btn-analyze-classic">古典风格</button>
        <button type="button" class="btn btn-secondary ai-style-btn" data-style="modern" id="btn-analyze-modern">现代风格</button>
        <button type="button" class="btn btn-secondary hidden" id="btn-copy-analysis">复制解读</button>
      </div>
      <div id="ai-loading" class="ai-loading hidden"><div class="spinner"></div><p class="ai-loading-title">问元解读中</p></div>
      <div id="ai-error" class="alert alert-error hidden"></div>
      <div id="ai-empty" class="ai-empty"><p>选择风格后，AI 将按八个章节流式输出 L1 解读。</p></div>
      <div id="ai-result-wrap" class="analysis-panel hidden">
        <div class="analysis-header">
          <span id="ai-style-badge" class="analysis-style-badge style-classic">古典风格</span>
          <span id="ai-time" class="analysis-time"></span>
        </div>
        <div id="ai-result" class="analysis-content"></div>
      </div>
      <div class="l2-chips">${chips}</div>
      <div class="ask-panel">
        <div id="ask-history" class="ask-history"></div>
        <div class="ask-input-bar">
          <input type="text" id="ask-input" placeholder="就本盘提问…" maxlength="500">
          <button type="button" class="btn btn-primary" id="btn-ask">提问</button>
        </div>
        <p id="ask-rounds" class="ask-rounds"></p>
      </div>
    </section>`;
}

function renderAnalysis(text, style, streaming = false) {
  const wrap = document.getElementById("ai-result-wrap");
  const empty = document.getElementById("ai-empty");
  const badge = document.getElementById("ai-style-badge");
  const timeEl = document.getElementById("ai-time");
  const result = document.getElementById("ai-result");
  const copyBtn = document.getElementById("btn-copy-analysis");
  if (!result) return;
  const label = style === "classic" ? "古典风格" : "现代风格";
  if (badge) {
    badge.textContent = label;
    badge.className = `analysis-style-badge style-${style}`;
  }
  if (timeEl) timeEl.textContent = new Date().toLocaleString("zh-CN", { hour12: false });
  result.innerHTML = markdownToHtml(text) + (streaming ? '<span class="stream-cursor">▍</span>' : "");
  wrap?.classList.remove("hidden");
  empty?.classList.add("hidden");
  copyBtn?.classList.remove("hidden");
  document.querySelectorAll(".ai-style-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.style === style);
  });
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
  const cites = insight?.citations || [];
  if (cites.length) {
    md += `\n### 典籍参考\n\n`;
    cites.forEach((c) => { md += `- 《${c.source}》${c.text}\n`; });
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
  document.querySelectorAll(".chart-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.target;
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
      document.querySelectorAll(".chart-nav-btn").forEach((b) => b.classList.toggle("active", b === btn));
    });
  });


  document.querySelectorAll(".section-header").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.target;
      const body = document.getElementById(id);
      body?.classList.toggle("collapsed");
      btn.closest(".collapsible")?.classList.toggle("is-collapsed");
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
    const md = buildMarkdownExport(state.chart, state.chart.insight, state.analysis[state.style] || "", state.history);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `wenyuan-${state.input?.birth_date || "chart"}.md`;
    a.click();
    showToast("Markdown 已导出");
  });

  document.getElementById("btn-copy-link")?.addEventListener("click", () => {
    const modal = document.getElementById("privacy-modal");
    modal?.classList.remove("hidden");
    const confirm = () => {
      navigator.clipboard.writeText(getShareUrl(state.input)).then(() => showToast("链接已复制"));
      modal?.classList.add("hidden");
    };
    document.getElementById("modal-confirm").onclick = confirm;
    document.getElementById("modal-cancel").onclick = () => modal?.classList.add("hidden");
    modal?.querySelector(".modal-backdrop")?.addEventListener("click", () => modal?.classList.add("hidden"), { once: true });
  });

  document.getElementById("btn-copy-analysis")?.addEventListener("click", () => {
    const text = state.analysis[state.style] || "";
    if (text) navigator.clipboard.writeText(text).then(() => showToast("解读已复制"));
  });

  async function runAnalyze(style) {
    const loading = document.getElementById("ai-loading");
    const err = document.getElementById("ai-error");
    hideError(err);
    loading?.classList.remove("hidden");
    document.getElementById("ai-empty")?.classList.add("hidden");
    document.querySelectorAll(".ai-style-btn").forEach((b) => { b.disabled = true; });
    const result = document.getElementById("ai-result");
    if (result) result.innerHTML = "";
    document.getElementById("ai-result-wrap")?.classList.remove("hidden");

    try {
      const text = await API.analyze(state.chart, style, state.chart.insight, (full) => {
        renderAnalysis(full, style, true);
      });
      state.analysis[style] = text;
      renderAnalysis(text, style, false);
      saveAiCache(state.input, { analysis: state.analysis, history: state.history, style: state.style });
    } catch (e) {
      showError(err, e.message || "分析失败");
    } finally {
      loading?.classList.add("hidden");
      document.querySelectorAll(".ai-style-btn").forEach((b) => { b.disabled = false; });
    }
  }

  document.getElementById("btn-analyze-classic")?.addEventListener("click", () => runAnalyze("classic"));
  document.getElementById("btn-analyze-modern")?.addEventListener("click", () => runAnalyze("modern"));

  document.querySelectorAll(".chip-btn").forEach((btn) => {
    btn.addEventListener("click", () => runAsk(btn.dataset.q));
  });

  async function runAsk(question) {
    const rounds = state.history.filter((h) => h.role === "user").length;
    if (rounds >= L3_MAX_ROUNDS) {
      showError(document.getElementById("ai-error"), "本轮已达上限，请刷新或重新打开命盘");
      return;
    }
    const q = (question || document.getElementById("ask-input")?.value || "").trim();
    if (!q) return;
    appendAskMessage("user", q);
    document.getElementById("ask-input").value = "";
    state.history.push({ role: "user", content: q });
    updateRounds(state);

    const err = document.getElementById("ai-error");
    hideError(err);
    const placeholder = document.createElement("div");
    placeholder.className = "ask-msg ask-assistant";
    placeholder.textContent = "思考中…";
    document.getElementById("ask-history")?.appendChild(placeholder);

    try {
      let answer = "";
      answer = await API.ask(
        state.chart,
        q,
        state.style,
        state.chart.insight,
        state.analysis[state.style] || "",
        state.history.slice(0, -1),
        (full) => {
          placeholder.innerHTML = markdownToHtml(full);
        }
      );
      placeholder.innerHTML = markdownToHtml(answer);
      state.history.push({ role: "assistant", content: answer });
      saveAiCache(state.input, { analysis: state.analysis, history: state.history, style: state.style });
    } catch (e) {
      placeholder.remove();
      state.history.pop();
      showError(err, e.message || "问答失败");
    }
    updateRounds(state);
  }

  document.getElementById("btn-ask")?.addEventListener("click", () => runAsk());
  document.getElementById("ask-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runAsk();
  });
}

function updateRounds(state) {
  const n = state.history.filter((h) => h.role === "user").length;
  const el = document.getElementById("ask-rounds");
  if (el) el.textContent = `已问 ${n} / ${L3_MAX_ROUNDS} 轮`;
}

function historyLabel(chart, input) {
  const dm = chart?.meta?.day_master || "";
  const g = input?.gender === "female" ? "女" : "男";
  return `${input?.birth_date || ""} ${g} · ${dm}`;
}

async function navigateWithChart(input, chart) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chart));
  sessionStorage.setItem(INPUT_KEY, JSON.stringify(input));
  saveHistory(input, historyLabel(chart, input));
  const url = getShareUrl(input);
  location.href = url;
}

function initIndexPage() {
  const form = document.getElementById("chart-form");
  const errEl = document.getElementById("form-error");
  const btn = document.getElementById("submit-btn");
  const dateType = document.getElementById("date_type");
  const lunarHint = document.getElementById("lunar-hint");
  const leapGroup = document.getElementById("leap-month-group");

  document.getElementById("birth_date").value = "1990-05-15";
  document.getElementById("birth_time").value = "12:00";

  const renderHist = () => {
    const list = loadHistory();
    const card = document.getElementById("history-card");
    const ul = document.getElementById("history-list");
    if (!list.length || !ul) return;
    card?.classList.remove("hidden");
    ul.innerHTML = list
      .map(
        (h) =>
          `<li class="history-item"><a href="${getShareUrl(h.input)}">${escapeHtml(h.label || h.input.birth_date)}</a></li>`
      )
      .join("");
  };
  renderHist();

  dateType?.addEventListener("change", () => {
    const lunar = dateType.value === "lunar";
    lunarHint?.classList.toggle("hidden", !lunar);
    leapGroup?.classList.toggle("hidden", !lunar);
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError(errEl);
    btn.disabled = true;
    btn.textContent = "排盘中…";
    const fd = new FormData(form);
    const payload = {
      date_type: fd.get("date_type"),
      birth_date: fd.get("birth_date"),
      birth_time: fd.get("birth_time"),
      gender: fd.get("gender"),
      is_leap_month: fd.get("is_leap_month") === "on",
    };
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
      btn.disabled = false;
      btn.textContent = "开始排盘";
    }
  });
}

async function initChartPage() {
  const root = document.getElementById("chart-root");
  const loading = document.getElementById("chart-loading");
  const params = new URLSearchParams(location.search);
  const share = params.get("s");

  let input = null;
  let chart = null;

  try {
    if (share) {
      input = decodeSharePayload(share);
      loading?.classList.remove("hidden");
      const res = await API.chart(input);
      if (!res.success) throw new Error(res.error || "排盘失败");
      chart = res.data;
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
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chart));
  if (input) sessionStorage.setItem(INPUT_KEY, JSON.stringify(input));

  const cache = input ? loadAiCache(input) : null;
  const state = {
    chart,
    input: input || {},
    analysis: cache?.analysis || { classic: "", modern: "" },
    history: cache?.history || [],
    style: cache?.style || "classic",
  };

  root.innerHTML = renderChart(chart);
  wireChartInteractions(state);

  if (state.analysis.classic) renderAnalysis(state.analysis.classic, "classic");
  else if (state.analysis.modern) renderAnalysis(state.analysis.modern, "modern");

  state.history.forEach((h) => {
    appendAskMessage(h.role, h.content);
  });
  updateRounds(state);

  if (window.matchMedia("(max-width: 768px)").matches) {
    document.querySelectorAll("#sec-tian, #sec-ren").forEach((sec) => {
      sec.classList.add("is-collapsed");
      sec.querySelector(".section-body")?.classList.add("collapsed");
    });
  }
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
