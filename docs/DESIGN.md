# 问元 · 设计规范（DESIGN v1）

> 供前端开发与 Cursor AI 统一视觉与 IA。实现文件：`static/css/theme.css`、`templates/`、`static/js/app.js`。

## 品牌

- **名称**：问元 Wenyuan
- **主张**：探问天地人三元 — 自研子平综参排盘，规则层直断 + AI 锚定解读
- **气质**：深色纸墨、金色点睛、克制国风（非炫彩玄学风）

## 色彩

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#0f0e0c` | 页面底 |
| `--bg-card` | `#1a1814` | 卡片 |
| `--bg-elevated` | `#242019` | 抬升面板、输入框 |
| `--border` | `#3d3528` | 边框 |
| `--text` | `#e8e0d4` | 正文 |
| `--text-muted` | `#9a8f7a` | 次要说明 |
| `--accent` | `#c9a227` | 主强调、链接、标题 |
| `--accent-dim` | `#8a7020` | 弱强调 |
| `--accent-cool` | `#7eb8da` | 过三关、信息 |
| `--accent-warm` | `#e8a87c` | 断事强信号 |
| 五行 | wood/fire/earth/metal/water | 柱、五行条 |

背景渐变：顶部淡金 radial + 右下淡蓝 radial（已写在 `body`）。

## 字体

- **Sans**：Noto Sans SC — 正文、表单、按钮
- **Serif**：Noto Serif SC — Logo、章节标题、四柱大字

## 间距与圆角

- 基础单位：**4px**
- 卡片内边距：`1.75rem`（`.card`）/ `0.85–0.95rem`（`.panel-card-body`）
- 圆角：`--radius: 12px`；按钮/输入 `8px`；chip/badge `999px`
- 内容最大宽度：**960px**（`.container`）

## 组件

### 按钮

- `.btn-primary`：金色渐变，表单主 CTA 全宽
- `.btn-secondary`：描边，工具栏/次要操作
- `.is-loading`：提交/解读 loading（旋转指示）

### 面板

```
.panel-card
  .panel-card-header  → .panel-card-title
  .panel-card-body
```

用于：命局要点、断事、过三关。

### 命盘布局

```
.chart-page
  .chart-topbar        → 返回 + 分享/导出
  .chart-nav           → 分区 Tab（sticky）
  .chart-sticky-summary → 四柱 + 日主
  .section-block       → 各分区内容
```

### 状态

- 加载：`.chart-skeleton` / `.spinner` / `.is-pending`
- 空：`.ai-empty`
- 错：`.alert.alert-error`
- Toast：`.copy-toast`

## 页面线框

### 首页

```
[Header: Logo + 导航]
[Hero:  eyebrow + 标题 + 副文 + 3 步]
[Card:  排盘表单]
[Features: 3 列能力卡]
[Card:  最近排盘（可选）]
[Footer]
```

### 命盘

```
[Topbar: ← 重新排盘 | 分享 导出]
[Tab: 概览 | 四柱 | 运势 | 本命 | 问 AI]
[Summary bar: 癸酉 甲子 … | 日主癸 …]
[Sections…]
[AI: 开始解读 → 流式八章 → L2 chips → L3 输入]
```

## AI 交互

- **单一解读**：按钮「开始解读」，badge「子平直断」
- API `style` 字段保留兼容，提示词已统一
- L2 预设 chip + L3 自由问，每盘最多 8 轮

## 扩展约定

新增 UI 时：

1. 优先扩展现有 class，不新建平行命名
2. 新 token 追加到 `:root`，并更新本文档
3. 带 `[cursor/rules/wenyuan-ui.mdc]` 约束的改动需跑 `pytest` 与手动看移动端
