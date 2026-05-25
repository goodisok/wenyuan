# 八字命理知识库

中国传统八字命理学（子平法）知识体系。

## 目录结构

```
bazi/
├── manifest.json        # 机器可读的内容清单（JSON + YAML）
├── CLAUDE.md            # AI 使用说明（本文件）
├── README.md            # 项目简介
├── SCHEMA.md            # 领域约定与标签分类
├── index.md             # 人工阅读的内容目录
├── concepts/            # 核心概念（14页）
│   ├── tian-gan-di-zhi.md    # 天干地支
│   ├── wu-xing.md            # 五行
│   ├── si-zhu.md             # 四柱结构
│   ├── shi-shen.md           # 十神
│   ├── da-yun-liu-nian.md    # 大运流年
│   └── yuan-hai-zi-ping.md  等9本经典解析
├── entities/            # 实体参考（3页）
├── methods/             # 方法论（1页）
├── cases/               # 实战命例（16个覆盖全部格局）
└── raw/classics/        # 原典全文（4部约45万字）
```

## 查询指引

- **快速查找概念**：查阅 `concepts/` 下对应文件
- **查找格局断法**：查阅 `entities/ge-ju.md` 和 `cases/` 对应命例
- **原文对照**：查阅 `raw/classics/` 下原典
- **机器检索**：先读 `manifest.json` 获取完整内容清单，再按需读取具体页面

## 内容使用说明

- 每页含 YAML frontmatter（title, type, tags, confidence）
- `confidence: high` = 经典定论；`medium` = 需交叉验证；`low` = 存疑待考
- 原典全文在 `raw/classics/`，未经修改
- 命例来自《滴天髓阐微》（任铁樵注），含八字排盘、原评、白话解读

## 标签体系

- **基础架构**：tian-gan-di-zhi, wu-xing, yin-yang
- **核心命理**：si-zhu, shi-shen, ge-ju, da-yun, shen-sha, wang-shuai
- **方法**：pai-pan, duan-ming, liu-nian
- **古籍**：jing-dian, yuan-hai, san-ming, di-tian, qiong-tong
