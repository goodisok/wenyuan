# 命理知识库说明

问元 **v1.4** 起采用**结构化语料库**（`knowledge/corpus/`），在程序规则层之上为 AI 提供可检索的古籍原文、条文与命例。

## 架构

```
排盘 → 子平综参（规则层）
     → 语料库打分检索（120 穷通 + 滴天髓/子平/渊海/三命/千里命稿）
     → 混合召回 ≤18 条（含章节、命例、按语）
     → AI 锚定（须标注书名章节）
```

## 语料规模（Phase A）

| 典籍 | 条目 | 类型 |
|------|------|------|
| 穷通宝鉴 | 120 | 调候（程序层同步生成） |
| 滴天髓 | 15 | 诗诀、旺衰、流通 |
| 子平真诠 | 11 | 格局、用神 |
| 渊海子平 | 12 | 十神、用神法 |
| 三命通会 | 12 | 格局、神煞 |
| 千里命稿 | 12 | 结构化命例 |

**合计约 182 条**（可持续扩充 JSON 语料）。

## 扩展

1. 编辑 `knowledge/corpus/data/*.json` 增加条文或命例  
2. 每条需含：`id`, `source`, `book`, `chapter`, `tags`, `text`  
3. 可选：`match`（day_stem/month_branch/geju）、`pillars`, `commentary`, `kind`（principle/case/tiao_hou/verse）

参考 [bazi-skill](https://github.com/jinchenma94/bazi-skill) MIT 整理思路。

## Phase B（未做）

向量语义检索 + embedding，适用于语料上千条后。
