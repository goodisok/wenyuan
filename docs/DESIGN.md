# 问元 · 设计规范（DESIGN v2）

> 与 **v1.11** 实现对齐。实现文件：`static/css/theme.css`、`templates/`、`static/js/app.js`。

---

## 1. 品牌与气质

| 项 | 说明 |
|----|------|
| **名称** | 问元 Wenyuan |
| **主张** | 探问天地人三元 — 自研子平综参，先观全盘再高置信断人事 |
| **气质** | 深色纸墨、金色点睛、克制国风（避免炫彩玄学风） |

---

## 2. 设计 Token（`:root`）

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#0f0e0c` | 页面底 |
| `--bg-card` | `#1a1814` | 卡片 |
| `--bg-elevated` | `#242019` | 输入框、抬升区 |
| `--border` | `#3d3528` | 边框 |
| `--text` | `#e8e0d4` | 正文 |
| `--text-muted` | `#9a8f7a` | 次要说明 |
| `--accent` | `#c9a227` | 主强调、标题、链接 |
| `--accent-dim` | `#8a7020` | 弱强调 |
| `--accent-warm` | `#e8a87c` | 观命、断事暖色 |
| `--accent-cool` | `#7eb8da` | 六亲印证信息色 |
| `--shadow-sm` | 见 theme.css | 分段控件选中、sticky 条 |
| `--nav-offset` | `3.5rem` | 顶栏 + sticky 导航偏移 |
| 五行色 | wood/fire/earth/metal/water | 柱、五行条 |

`body` 背景：顶部淡金 radial + 右下淡蓝 radial。

---

## 3. 字体与排版

- **Sans（Noto Sans SC）：** 正文、表单、按钮、说明  
- **Serif（Noto Serif SC）：** Logo、章节标题、四柱大字、出生摘要  

移动端表单控件 `font-size: 16px`，避免 iOS 缩放。

---

## 4. 布局

- 内容最大宽度：**960px**（`.container`）  
- 基础间距单位：**4px**  
- 卡片圆角：`--radius: 12px`；按钮/输入 `8px`  
- `html { scroll-padding-top }`：锚点滚动不被 sticky 导航遮挡  

---

## 5. 组件规范

### 5.1 按钮

| 类名 | 用途 |
|------|------|
| `.btn-primary` | 主 CTA（排盘、开始解读）；金色渐变 |
| `.btn-secondary` | 分享、导出、次要操作 |
| `.btn-sm` | 命盘顶栏 |
| `.is-loading` | 提交/解读中；`.btn-label` 可换文案 |

### 5.2 分段控件（历法 / 性别）

类名：`.segmented` · `.segmented-item` · `input` + `span`

- 参考 shadcn Toggle Group：选中态金底描边  
- 必须保留 `focus-visible` 环  
- 隐藏原生 radio，点击整块区域  

### 5.3 表单

- `fieldset` + `legend` 分组：历法、出生日期、出生时间、性别  
- 年月日时分为 **select**（非原生 datetime，便于农历/闰月）  
- `.birth-summary`：实时显示当前选择（`aria-live="polite"`）  
- `.form-tips`：简短提示 chips  

### 5.4 面板（规则层）

```
.insight-stack
  .panel-card.guanming-panel     ← 观命总观
  .panel-card.highlights-panel   ← 命局要点
  .panel-card.duanshi-panel      ← 断事
  .panel-card.sanguan-panel       ← 六亲人事 · 多维验证
```

v2 面板样式：**减少嵌套卡片**，以顶部分隔线区分（避免 card-in-card）。

### 5.5 命盘页

```
.chart-page
  .chart-topbar              ← 返回 + 分享/导出
  .chart-nav                 ← Tab（sticky，支持方向键）
  .chart-sticky-summary      ← 四柱 + 日主 + 生辰
  #sec-meta                  ← 基本
  #sec-di                    ← 基本命盘（表格式）
  #sec-tian                  ← 细盘 / 大运
  #sec-ai                    ← 问 AI
```

**基本命盘表（`.bazi-grid`）：**

- 行：十神、天干、地支、藏干、纳音、空亡、星运  
- **无** 神煞行  
- 十神、纳音为**纯文本**（无悬浮 tooltip）  

### 5.6 AI 区

| 元素 | 类名 / 说明 |
|------|-------------|
| 空状态 | `#ai-empty` |
| 加载 | `#ai-loading` + `.spinner` |
| 结果 | `#ai-result-wrap` + `.analysis-content` |
| L2 | `.l2-chip` |
| 追问 | `.ask-input-bar`（移动端 sticky 底栏） |
| 流式光标 | `.stream-cursor` |

**不做：** 参与式核对面板、典籍语料列表。

### 5.7 状态与反馈

| 状态 | 实现 |
|------|------|
| 页内加载 | `.chart-skeleton` |
| 错误 | `.alert.alert-error` |
| Toast | `.copy-toast` |
| 弹窗 | `#privacy-modal`（分享确认） |

---

## 6. 页面线框

### 6.1 首页 `/`

```
[Header: Logo + 排盘 | 隐私]
[Hero:  eyebrow + 标题 + 三步]
[Card:  历法分段 | 年月日 | 时分 | 闰月 | 性别 | 出生摘要 | 开始排盘]
[Features: 规则层 | 观命断事 | 问 AI]
[Card:  最近排盘（可选）]
[Footer]
```

### 6.2 命盘 `/chart`

```
[Topbar]
[Tab: 基本 | 命盘 | 细盘 | 问 AI]
[Sticky: 四柱串 + 日主 + 阳历]
[sec-meta: 基本信息 + 观命 + 要点 + 断事 + 六亲]
[sec-di: 四柱表 + 可选卡片视图]
[sec-tian: 大运流年]
[sec-ai: 解读 + chips + 追问]
```

---

## 7. AI 交互（产品层）

| 层级 | 触发 | 说明 |
|------|------|------|
| **L1** | 「开始解读」 | SSE 六章 Markdown；badge「子平直断」 |
| **L2** | `.l2-chip` | 单次 `POST /api/ask` |
| **L3** | 输入框 Enter 发送 | 可带 history；Shift+Enter 换行 |

API 字段 `style` 保留兼容，提示词已统一。

---

## 8. 无障碍与动效

- Skip link：`.skip-link`  
- Tab 导航：`role="tablist"`，`aria-selected`，键盘 ←→  
- `prefers-reduced-motion: reduce`：缩短动画  
- 命盘加载：`.chart-page.is-ready` 淡入  

---

## 9. 扩展约定

1. 新样式优先扩展现有 class，避免平行命名体系  
2. 新 token 写入 `:root` 并更新本文档  
3. 改动后跑 `pytest` + 移动端抽查（640px 断点）  
4. Cursor 规则：`.cursor/rules/wenyuan-ui.mdc`（若存在）

---

## 10. 与 v1 差异摘要

| 项 | v1 | v2（当前） |
|----|-----|------------|
| 历法/性别 | select / radio 横排 | 分段控件 |
| 命盘 Tab 文案 | 概览/四柱/… | 基本/命盘/细盘/问 AI |
| 三关展示名 | 过三关 | 六亲人事 · 多维验证 |
| 典籍/校准 | 前端展示 | 已移除 |
| 十神纳音 | tooltip | 纯文本 |
| 神煞 | 命盘表一行 | 不展示 |
| AI 章数 | 八/九章含校准 | 六章 |
