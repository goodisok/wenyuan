# Wiki Schema — 八字命理知识库

## Domain
中国传统八字命理学（四柱预测）。涵盖天干地支、五行生克、十神、格局、大运流年、神煞等核心概念。以子平法为主流框架。

## Conventions
- 文件名：中文 + 小写字母、hyphen 连接，不用空格（如 `shi-shen.md`、`tian-gan-di-zhi.md`）
- 每个 Wiki 页以 YAML frontmatter 开头
- 使用 `[[wikilinks]]` 交叉引用（每页至少 2 个出链）
- 更新页面时务必 bump `updated` 日期
- 每新建一页必须在 `index.md` 对应分区添加条目
- 每个操作必须追加到 `log.md`
- 来源标注：由 3+ 来源综合而成的页面，在段落末尾追加 `^[raw/.../source.md]` 标记

## Frontmatter
```yaml
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept | entity | method | query | summary
tags: [来自下方分类]
sources: [raw/.../source.md]
confidence: high | medium | low
contested: true      # 当页面存在未解决矛盾时设置
---
```

## Tag Taxonomy

### 基础架构
- tian-gan-di-zhi: 天干地支
- wu-xing: 五行
- yin-yang: 阴阳

### 核心命理
- si-zhu: 四柱
- shi-shen: 十神
- ge-ju: 格局
- da-yun: 大运流年
- shen-sha: 神煞
- wang-shuai: 旺衰

### 方法
- pai-pan: 排盘
- duan-ming: 断命
- liu-nian: 流年
- he-hun: 合婚

### 古籍
- jing-dian: 经典
- yuan-hai: 渊海子平
- san-ming: 三命通会
- di-tian: 滴天髓
- qiong-tong: 穷通宝鉴

### 元
- reference: 参考资料
- tool: 工具
- comparison: 对比

**规则：** 每个 tag 必须先添加到此分类再使用。防止标签膨胀。

## Page Thresholds
- **创建页面：** 当概念/实体在 2+ 来源中出现，或作为 1 个来源的核心主题
- **追加到已有页面：** 当来源提及已有内容
- **不要创建：** 泛泛提及、背景常识（如"什么是五行"属于基础概念仍要创建，但无需过度细碎拆分）
- **拆分页面：** 超过 ~200 行时，拆分子主题并交叉引用
- **归档：** 内容被完全取代时，移至 `_archive/`，从 index 移除

## Entity Pages
每实体的单页。包含：概述、核心事实、与其它实体的 `[[wikilinks]]`、来源引用。

## Concept Pages
每概念的单页。包含：定义/解释、当前认知状态、开放问题或争议、相关概念。

## Method Pages
方法论页面。包含：步骤、原理、适用场景、常见误区和争议。

## Update Policy
当新信息与已有内容冲突时：
1. 检查时间——新来源通常取代旧来源
2. 如果确实矛盾，标注双方观点及时间来源
3. 在 frontmatter 标记：`contradictions: [page-name]`
4. 在 lint 报告中标记供用户审查
