# 问元 Wenyuan

探问天地人三元 — **自研**八字排盘与 AI 解读 Web 服务。

程序负责准确排盘与多层规则分析；AI 在命盘与**已发布的高置信规则层**上下文中解读与追问。支持公历/农历、PC 与手机、多用户并发，无账号注册，服务端不落库。

## 在线试用

- **站点：** [https://wenyuan.online/](https://wenyuan.online/)
- **备用：** [http://119.91.54.153/](http://119.91.54.153/)
- **当前版本：** v1.11.0（以 `/health` 为准）

配置服务端 `DEEPSEEK_API_KEY` 后可使用流式解读与就盘追问。

## 产品定位

| 是 | 不是 |
|----|------|
| 公网命盘 + 服务端统一 AI | 在线算命社区 |
| URL 分享排盘入口（编码生辰） | 云端存储用户命盘库 |
| 就盘 L1 / L2 / L3 问答 | 脱离命盘的闲聊 |
| 程序规则层锚定 AI | 纯 LLM 自由发挥 |

完整需求与验收见 **[PRODUCT.md](PRODUCT.md)**；读盘架构见 **[docs/READING.md](docs/READING.md)**；系统架构见 **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**。

## 核心能力

### 排盘（天元 · 地元 · 人元）

四柱（藏干、十神、纳音、旬空、长生）、起运、大运、流年、小运；胎元、命宫、身宫；刑冲合害。

### 规则层 · 子平综参

**先观命总观，再高置信断人事**（模棱两可项不发布到界面）。

| 模块 | 说明 |
|------|------|
| 观命总观 | 滴天髓天道/地道/人道、盲派做功、流通等 |
| 旺衰体用 | 滴天髓得令、通根、气候 |
| 调候 | 穷通宝鉴 |
| 格局 / 喜用 | 子平真诠、渊海子平 |
| 断事 | 父母 / 婚姻 / 财运等（仅高置信） |
| 六亲人事 · 多维验证 | 盲派 / 子平 / 千里交叉印证（仅高置信关） |

典籍语料在服务端注入 **AI 分析上下文**，网页不展示程序化断语面板。

### AI · 问

- **L1** AI 流式解读（按年龄与命盘智能组织章节）
- **L2** 预设追问 chips（由规则层动态生成）
- **L3** 就盘自由问答（SSE）

## 架构（简图）

```
生辰 → BaziService 排盘
     → mingli 规则层（各家模块）
     → publish 高置信过滤
     → build_insight + knowledge 检索（仅 AI）
     → public_insight → 前端展示
     → 可选 DeepSeek 流式解读 / 追问
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 技术栈

- **后端：** FastAPI · Pydantic · httpx · lunar-python
- **AI：** DeepSeek API（`AI_ENABLED` 可关）
- **前端：** Jinja2 · 原生 JS · CSS（无 React 构建链）
- **部署：** Nginx · systemd · Let's Encrypt

## 快速开始

**Windows：**

```bat
start.bat
```

**手动：**

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
copy .env.example .env         # 填入 DEEPSEEK_API_KEY
python run.py
```

- 主页：http://localhost:8000  
- API 文档：http://localhost:8000/docs  

公网部署见 **[DEPLOY.md](DEPLOY.md)**。

## 项目结构

```
wenyuan/
├── app/
│   ├── main.py           # 页面路由、健康检查
│   ├── api/routes.py     # /api/chart · analyze · ask
│   ├── core/             # 排盘、规则层、发布过滤、检索
│   └── services/ai.py    # DeepSeek 提示词与 SSE
├── knowledge/            # 典籍 JSON、bazi-wiki、BM25
├── templates/            # index · chart · privacy
├── static/               # theme.css · app.js · sw.js
├── tests/                # pytest + 黄金命例
├── docs/
│   ├── ARCHITECTURE.md   # 系统架构（当前实现）
│   └── DESIGN.md         # UI/UX 规范
├── PRODUCT.md            # 产品需求 PRD
├── DEPLOY.md             # 部署说明
└── run.py
```

## API 示例

```bash
curl -X POST http://localhost:8000/api/chart \
  -H "Content-Type: application/json" \
  -d "{\"date_type\":\"solar\",\"birth_date\":\"1990-05-15\",\"birth_time\":\"12:30\",\"gender\":\"male\",\"is_leap_month\":false}"
```

## 测试

```bash
python -m pytest tests/
node scripts/verify_birth_form.mjs   # 需 Node.js，可选
```

## 版本摘要

| 版本 | 要点 |
|------|------|
| **v1.13** | 三阶读盘：直断/结构提示分级；人生阶段降级而非删除；修复应期 |
| **v1.12** | 人生阶段关切（已并入 v1.13 呈现层） |
| v1.10 | 观命总观、发布过滤、BM25、AI 校验、黄金命例 |
| v1.9.x | 高置信发布策略、移动端优化 |
| v1.6+ | 六亲多维验证、断事层、子平综参 |

## 仓库与许可

- GitHub：[github.com/goodisok/wenyuan](https://github.com/goodisok/wenyuan)
- 许可：MIT  
- 语料说明：[knowledge/ATTRIBUTION.md](knowledge/ATTRIBUTION.md) · 更新 wiki：`python scripts/sync_wiki.py`
