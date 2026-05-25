/** 文渊 · 前端工具 */
const API = {
  async chart(payload) {
    const res = await fetch("/api/chart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  },
  async analyze(chart, style = "classic") {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chart, style }),
    });
    return res.json();
  },
};

function showError(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("hidden");
}

function hideError(el) {
  if (!el) el?.classList.add("hidden");
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
        <td>${(d.liunian || []).slice(0, 5).map((l) => `<span class="badge">${l.ganzhi}(${l.year})</span>`).join("")}${(d.liunian || []).length > 5 ? "…" : ""}</td>
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
        <div class="meta-item"><div class="label">胎元</div><div class="value">${m.tai_yuan || "—"}</div></div>
        <div class="meta-item"><div class="label">命宫</div><div class="value">${m.ming_gong || "—"}</div></div>
        <div class="meta-item"><div class="label">身宫</div><div class="value">${m.shen_gong || "—"}</div></div>
      </div>
      <p style="margin-top:1rem;font-size:0.88rem;color:var(--text-muted)">
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
          <thead><tr><th>干支</th><th>年份</th><th>年龄</th><th>流年（节选）</th></tr></thead>
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
      <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1rem">
        需配置 DeepSeek API Key。点击下方按钮开始分析，不会自动消耗额度。
      </p>
      <div class="actions">
        <button type="button" class="btn btn-secondary" id="btn-analyze-classic">古典风格解读</button>
        <button type="button" class="btn btn-secondary" id="btn-analyze-modern">现代风格解读</button>
      </div>
      <div id="ai-loading" class="loading-box hidden"><div class="spinner"></div><p>正在解读命盘…</p></div>
      <div id="ai-error" class="alert alert-error hidden"></div>
      <div id="ai-result" class="analysis-content" style="margin-top:1rem"></div>
    </div>
  `;
}

window.Wenyuan = { API, renderChart, showError, hideError };
