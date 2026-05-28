# 命理知识库说明

问元采用**双层知识架构**：程序规则层 + 结构化语料检索，为 AI 提供可锚定的典籍原文、概念页与命例。

## 架构

```
排盘 → 子平综参（规则层）
     → 语料库混合检索
         · JSON 典籍条文（滴天髓 / 子平 / 渊海 / 三命 / 千里）
         · 穷通宝鉴 120 组（程序同步）
         · bazi-wiki 概念 / 实体 / 方法 / 命例页
     → 混合召回 ≤18 条（含章节、命例、按语）
     → AI 锚定（须标注书名章节）
```

## 语料来源

| 来源 | 条目 | 说明 |
|------|------|------|
| 穷通宝鉴 | 120 | 调候（`app/core/qiongtong.py` 同步） |
| JSON 语料 | ~62 | `knowledge/corpus/data/*.json` |
| **[bazi-wiki](https://github.com/goodisok/bazi-wiki)** | ~40 | 概念、实体、方法、滴天髓命例（Markdown，子集入 BM25） |

**bazi-wiki** 替代原 [bazi-skill](https://github.com/jinchenma94/bazi-skill) 的外部参考思路，作为问元自维护知识库，与产品同演进。

同步命令：

```bash
python scripts/sync_wiki.py          # 拉取 wiki，运行时不含 raw 原典全文
python scripts/sync_wiki.py --keep-raw   # 保留 raw/classics 供本地研读
```

## bazi-wiki 页面映射

| Wiki | 语料 kind | 检索标签 |
|------|-----------|----------|
| concepts/ | principle | 十神、五行、格局概念等 |
| entities/ | principle | 格局、长生、生肖实体 |
| methods/ | principle | 排盘步骤等方法论 |
| cases/case-*.md | case | 滴天髓阐微命例，含八字、任评、用神 |

Wiki 标签（`ge-ju`, `shi-shen` 等）在检索时与问元标签（`geju`, `ss:正官` 等）自动桥接。

## JSON 语料扩展

1. 编辑 `knowledge/corpus/data/*.json`
2. 每条需含：`id`, `source`, `book`, `chapter`, `tags`, `text`
3. 可选：`match`, `pillars`, `commentary`, `kind`

## Phase B（未做）

向量语义检索 + embedding，适用于语料上千条后。
