# 问元 Wenyuan

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.16.2-green)](app/__init__.py)

自研八字排盘与 AI 解读 Web 服务。**程序在服务端完成排盘与多层子平规则分析**；AI 在完整规则层与典籍检索上下文中流式解读，并支持就盘追问。浏览器仅展示命盘结构与 AI 输出，规则层明细不暴露给客户端。

- 在线试用：[wenyuan.online](https://wenyuan.online/) · 备用 [119.91.54.153](http://119.91.54.153/)
- 版本以 [`/health`](http://119.91.54.153/health) 返回为准

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [API](#api)
- [Development](#development)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

## Features

### Chart & rules (server-side)

- 公历 / 农历排盘，精确到分钟；四柱、藏干、十神、纳音、旬空、长生、大运、流年、小运
- 服务端多层子平规则：滴天髓、子平格局、穷通调候、观命总观、断事、六亲、三关等
- 三阶读盘（直断 / 结构提示 / 阶段侧重）；程序分级后注入 AI 上下文
- 古典案例 RAG + BM25 典籍检索（仅服务端）

### AI interpretation

- **L1** 流式命盘解读 — `POST /api/analyze`（SSE 或 JSON）
- **L2** 预设追问 chips — `POST /api/ask`
- **L3** 就盘自由问答，可带会话 history（SSE 或 JSON）
- L1/L2/L3 流式结束后：`ai_validate` 校验，必要时静默修订，`done` 事件返回最终稿

### Web & privacy

- 无账号、无服务端命盘库；分享链接仅编码生辰参数
- 当前命盘与 AI 缓存在 **sessionStorage**；最近 20 条排盘在 **localStorage**
- 命盘页截图 / PDF 导出（含完整追问记录）

## Quick Start

### Prerequisites

- Python 3.10+
- （可选）Node.js 18+ — 前端表单冒烟测试

### Install & run

**Windows：**

```bat
start.bat
```

**手动：**

```bash
git clone https://github.com/goodisok/wenyuan.git
cd wenyuan

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
copy .env.example .env         # Windows: cp .env.example .env
python run.py
```

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Web UI |
| http://localhost:8000/docs | OpenAPI |
| http://localhost:8000/health | Version check |

## Configuration

Copy `.env.example` to `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | For AI | DeepSeek API key |
| `DEEPSEEK_MODEL` | No | Default `deepseek-v4-pro` |
| `DEEPSEEK_BASE_URL` | No | Default `https://api.deepseek.com/v1` |
| `AI_ENABLED` | No | `false` → analyze/ask 返回 503 |
| `APP_HOST` / `APP_PORT` / `APP_DEBUG` | No | 见 `.env.example` |

无 `DEEPSEEK_API_KEY` 时排盘可用，AI 不可用。

## Usage

1. 输入生辰（公历/农历、可选闰月）与性别
2. 浏览 **基本 / 命盘 / 细盘** Tab
3. 在 **问 AI** 开始流式解读 → 追问 chips → 自由问答
4. 顶栏截图 / PDF 导出

```
生辰 → BaziService 排盘 → build_insight（规则层 + 检索 + RAG）
     → public_insight（运限 + 通用 chips）→ 浏览器
     → ensure_ai_insight（完整规则层）→ DeepSeek 流式 → 校验/修订
```

## API

```bash
curl -X POST http://localhost:8000/api/chart \
  -H "Content-Type: application/json" \
  -d '{"date_type":"solar","birth_date":"1990-05-15","birth_time":"12:30","gender":"male","is_leap_month":false}'
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chart` | POST | 排盘 JSON（insight 为 public 子集） |
| `/api/analyze` | POST | AI 解读（SSE 或 JSON） |
| `/api/ask` | POST | 追问（SSE 或 JSON） |
| `/health` | GET | `{"status":"ok","version":"…"}` |

请求体中的 `insight` 字段由服务端忽略，始终以服务端重算为准。

完整 schema：http://localhost:8000/docs

## Development

```bash
python -m pytest tests/ -q
npm install && npm run test:birth-form
python scripts/run_flywheel.py
python scripts/regression_rules.py
python scripts/regression_ai.py
```

Baselines：`reports/baseline_*_v*.json` · 古典 AI 套件：`data/ai_regression_suite.json`（50 例）

## Project Structure

```
wenyuan/
├── app/
│   ├── main.py, config.py, schemas.py
│   ├── api/routes.py
│   ├── core/          # 排盘、规则、读盘、校验、RAG
│   └── services/ai.py
├── knowledge/         # 语料、wiki、BM25
├── data/              # 回归套件
├── scripts/           # 部署、飞轮、回归
├── templates/ static/ tests/ docs/
└── run.py
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构与数据流 |
| [docs/READING.md](docs/READING.md) | 三阶读盘 |
| [docs/DESIGN.md](docs/DESIGN.md) | UI/UX |
| [DEPLOY.md](DEPLOY.md) | 部署运维 |
| [knowledge/ATTRIBUTION.md](knowledge/ATTRIBUTION.md) | 语料版权 |

## Deployment

```bash
python scripts/deploy_remote.py YOUR_HOST YOUR_PASSWORD
python scripts/verify_live.py
```

详见 [DEPLOY.md](DEPLOY.md)。

## Contributing

1. `python -m pytest tests/ -q`
2. `python scripts/regression_rules.py`
3. 若改 AI 提示词：`python scripts/regression_ai.py`

Issues / PR：[github.com/goodisok/wenyuan](https://github.com/goodisok/wenyuan)

## License

[MIT](LICENSE) © 2026 [goodisok](https://github.com/goodisok)

## Disclaimer

输出仅供文化参考与自我觉察，不构成医疗、投资或人生决策依据。见 [隐私说明](https://wenyuan.online/privacy)。

---

**支持：** 站点 AI 使用作者自购 Token，无广告无付费墙。自愿赞赏见 [支持页](https://wenyuan.online/support)（需将 `static/images/wechat-donate.jpg` 置于仓库方可显示二维码）。
