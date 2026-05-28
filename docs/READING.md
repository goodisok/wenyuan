# 问元 · 读盘架构（三阶断法 v1.13）

> 子平读盘：**结构全观 → 断语分级 → 阶段侧重**。  
> 实现：`app/core/reading.py` · `mingli.py` · `insight.py` · `ai.py`

---

## 1. 设计原则（命理师视角）

1. **结构不删** — 四柱、格局、旺衰、宫位、运限始终完整计算。  
2. **断语分级** — 强/高置信 → **直断**；中置信 → **结构提示**；弱 → 内部保留。  
3. **年龄调侧重，不删盘** — 童年不断婚育应期，但可示婚姻宫十神；晚年不强调学业。  
4. **单一数据源** — `highlights`、UI、AI 均从同一呈现层生成，避免矛盾。  
5. **应期可验证** — 直断才绑应期窗口；结构提示不断年份。

---

## 2. 三层架构

```
┌─────────────────────────────────────────┐
│ 结构层  ditiansui · ziping · guanming   │  始终展示
├─────────────────────────────────────────┤
│ 断语层  duanshi · sanguan (+ raw 保留)  │  全量计算
├─────────────────────────────────────────┤
│ 呈现层  publish tier × life_stage       │  UI + AI
└─────────────────────────────────────────┘
```

### 呈现 tier

| tier | 含义 | 浏览器 UI（v1.14+） | AI |
|------|------|---------------------|-----|
| **assert** | 直断 | 不展示面板，由 AI 表述 | 可断吉凶与应期 |
| **hint** | 结构提示 | 同上 | 可论十神宫位倾向 |
| **structure** | 阶段降级 | 同上 | 只论结构 |
| **hidden** | 不展示 | — | — |

### 人生阶段

虚岁分段：童年 1–12 · 少年 13–18 · 青年 19–28 · 壮年 29–45 · 中老年 46–60 · 晚年 61+  

`hidden` 议题在 UI 下降级为 `structure`，而非删除计算结果。

---

## 3. 数据流

```
BirthInput → BaziService.build_chart
          → mingli.analyze (结构 + duanshi_raw/sanguan_raw + tiered publish)
          → build_insight
          → apply_stage_presentation (life_stage + highlights 重建)
          → public_insight → 前端（仅运限 + 通用 chips）
          → ensure_ai_insight → AI（ai_reading_brief + build_output_format）
```

---

## 4. 模块职责

| 模块 | 职责 |
|------|------|
| `mingli.py` | 结构层编排，保留 raw |
| `duanshi.py` / `sanguan.py` | 断语规则（千里/盲派/子平） |
| `publish.py` | 分级发布（委托 `reading.py`） |
| `lifestage.py` | 阶段权重定义 |
| `reading.py` | **呈现编排 + highlights + AI 章节** |
| `insight.py` | 对外 insight 组装 |
| `ai_validate.py` | 直断应期与越界检测 |

---

## 5. 与旧版差异（v1.11–v1.12 → v1.13）

| 旧做法 | 问题 | v1.13 |
|--------|------|-------|
| publish 二值丢弃 |  adult 盘只剩父母一条 | 中置信 → 结构提示 |
| lifestage 硬删断语 | highlights 与面板矛盾 | 降级为 structure |
| 婚姻应期只扫年月 | windows 恒空 | 扫描日/时柱 |
| AI 八股固定章节 | 与阶段冲突 | 动态章节 + reading brief |

---

## 6. 后续演进

- Claim 对象化（id、schools、counter_evidence）  
- 学业/健康独立断事模块  
- 用户反馈校准回路  
