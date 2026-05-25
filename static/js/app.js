/** 问元 · 前端工具 */
const STORAGE_KEY = "wenyuan_chart";

async function parseJsonResponse(res) {
  const body = await res.json();
  if (!res.ok) {
    const detail = body.detail;
    if (Array.isArray(detail)) {
      const msg = detail.map((d) => d.msg || d.message || String(d)).join("；");
      throw new Error(msg || `请求失败 (${res.status})`);
    }
    throw new Error(body.error || body.message || `请求失败 (${res.status})`);
  }
  return body;
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
  async analyze(chart, style = "classic") {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chart, style }),
    });
    return parseJsonResponse(res);
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

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
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
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

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

  const blocks = escaped.split(/\n(?=## )/);
  return blocks
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

function renderAnalysis(text, style) {
  const wrap = document.getElementById("ai-result-wrap");
  const empty = document.getElementById("ai-empty");
  const badge = document.getElementById("ai-style-badge");
  const timeEl = document.getElementById("ai-time");
  const result = document.getElementById("ai-result");

  if (!result) return;

  const label = style === "classic" ? "古典风格" : "现代风格";
  if (badge) {
    badge.textContent = label;
    badge.className = `analysis-style-badge style-${style}`;
  }
  if (timeEl) {
    timeEl.textContent = new Date().toLocaleString("zh-CN", { hour12: false });
  }

  result.innerHTML = markdownToHtml(text);
  wrap?.classList.remove("hidden");
  empty?.classList.add("hidden");

  document.querySelectorAll(".ai-style-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.style === style);
  });

  wrap?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function wuxingClass(color) {
  return color ? `wuxing-${color}` : "";
}

function renderPillar(p) {
  const cg = (p.dizhi.canggan || [])
    .map((c) => `<span class="canggan-tag ${wuxingClass(c.color)}">${c.name}</span>`)
    .join("");
  return `
    <div class="pillar">
      <div class="pillar-label">${p.label}</div>
      <div class="pillar-ganzhi">${p.ganzhi}</div>
      <div class="stem ${wuxingClass(p.tiangan.color)}">${p.tiangan.name} · ${p.tiangan.wuxing}</div>
      <div class="branch ${wuxingClass(p.dizhi.color)}">${p.dizhi.name} · ${p.dizhi.wuxing}</div>
      <div class="canggan-list">${cg}</div>
      <div class="pillar-meta">${p.shishen}<br>${p.nayin}</div>
    </div>`;
}

function renderChart(data) {
  const m = data.meta;
  const wx = data.wuxing_stats || {};
  const wxMap = { 木: "wood", 火: "fire", 土: "earth", 金: "metal", 水: "water" };
  const wxChips = Object.entries(wx)
    .map(([k, v]) => `<span class="wuxing-chip wuxing-${wxMap[k] || ""}">${k} ${v}</span>`)
    .join("");

  const dayunRows = (data.dayun || [])
    .map(
      (d) => `
      <tr>
        <td><strong>${d.ganzhi}</strong></td>
        <td>${d.start_year} — ${d.end_year}</td>
        <td>${d.start_age} — ${d.end_age} 岁</td>
        <td class="liunian-cell">${(d.liunian || []).map((l) => `<span class="badge">${l.ganzhi}(${l.year})</span>`).join("")}</td>
      </tr>`
    )
    .join("");

  const xyRows = (data.xiaoyun || [])
    .slice(0, 12)
    .map(
      (x) => `
      <tr>
        <td>${x.year}</td>
        <td>${x.ganzhi}</td>
        <td>${x.age} 岁</td>
        <td>${x.liunian?.ganzhi || ""} (${x.liunian?.year || ""})</td>
      </tr>`
    )
    .join("");

  return `
    <div class="card">
      <h2 class="card-title">命主信息</h2>
      <div class="meta-grid">
        <div class="meta-item"><div class="label">性别</div><div class="value">${m.gender_label}</div></div>
        <div class="meta-item"><div class="label">生肖</div><div class="value">${m.zodiac}</div></div>
        <div class="meta-item"><div class="label">虚岁</div><div class="value">${m.age} 岁</div></div>
        <div class="meta-item"><div class="label">日主</div><div class="value">${m.day_master}（${m.day_master_wuxing}）</div></div>
        <div class="meta-item"><div class="label">十二长生</div><div class="value">${m.day_dishi || "—"}</div></div>
        <div class="meta-item"><div class="label">胎元</div><div class="value">${m.tai_yuan || "—"}</div></div>
        <div class="meta-item"><div class="label">命宫</div><div class="value">${m.ming_gong || "—"}</div></div>
        <div class="meta-item"><div class="label">身宫</div><div class="value">${m.shen_gong || "—"}</div></div>
      </div>
      <p class="birth-time-note">
        阳历 ${m.birth_time?.solar || ""}<br>
        农历 ${m.birth_time?.lunar || ""}
      </p>
      <div class="wuxing-bar">${wxChips}</div>
    </div>

    <div class="card">
      <h2 class="card-title">四柱八字</h2>
      <div class="bazi-board">${data.pillars.map(renderPillar).join("")}</div>
    </div>

    <div class="card">
      <h2 class="card-title">大运</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>干支</th><th>年份</th><th>年龄</th><th>流年</th></tr></thead>
          <tbody>${dayunRows || "<tr><td colspan='4'>暂无</td></tr>"}</tbody>
        </table>
      </div>
    </div>

    ${
      data.xiaoyun?.length
        ? `<div class="card">
      <h2 class="card-title">小运</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>年份</th><th>小运</th><th>年龄</th><th>流年</th></tr></thead>
          <tbody>${xyRows}</tbody>
        </table>
      </div>
    </div>`
        : ""
    }
    <div class="card" id="ai-section">
      <h2 class="card-title">AI 命理解读</h2>
      <p class="ai-hint">
        以 DeepSeek 结合本盘四柱、十神与大运生成解读。手动触发，不自动消耗额度。
      </p>
      <div class="ai-toolbar">
        <button type="button" class="btn btn-secondary ai-style-btn" data-style="classic" id="btn-analyze-classic">古典风格</button>
        <button type="button" class="btn btn-secondary ai-style-btn" data-style="modern" id="btn-analyze-modern">现代风格</button>
      </div>
      <div id="ai-loading" class="ai-loading hidden">
        <div class="spinner"></div>
        <p class="ai-loading-title">问元解读中</p>
        <p class="ai-loading-desc">正在结合天地人三元梳理命盘…</p>
      </div>
      <div id="ai-error" class="alert alert-error hidden"></div>
      <div id="ai-empty" class="ai-empty">
        <p>选择解读风格后，AI 将按八个章节输出结构化分析。</p>
      </div>
      <div id="ai-result-wrap" class="analysis-panel hidden">
        <div class="analysis-header">
          <span id="ai-style-badge" class="analysis-style-badge style-classic">古典风格</span>
          <span id="ai-time" class="analysis-time"></span>
        </div>
        <div id="ai-result" class="analysis-content"></div>
      </div>
    </div>
  `;
}

window.Wenyuan = { API, renderChart, renderAnalysis, showError, hideError, STORAGE_KEY };
