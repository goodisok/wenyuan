# 问元 Wenyuan

探问天地人三元 — **自研**八字排盘与 AI 解读 Web 服务。

程序负责准确排盘与多层子平规则分析；网页展示命盘结构，**AI 在服务端完整规则层与典籍检索上下文中**流式解读与就盘追问。支持公历/农历、PC 与手机、多用户并发；无账号注册，服务端不落库。

**当前版本：** v1.14.3（以 [`/health`](https://wenyuan.online/health) 为准）

## 在线试用

| 地址 | 说明 |
|------|------|
| [https://wenyuan.online/](https://wenyuan.online/) | 主域名（需 ICP 备案后国内可正常访问） |
| [http://119.91.54.153/](http://119.91.54.153/) | 备用 IP 直连 |

配置服务端 `DEEPSEEK_API_KEY` 后可使用流式解读与就盘追问；`AI_ENABLED=false` 可全站关闭 AI。

## 这是什么

| 是 | 不是 |
|----|------|
| 公网命盘 + 服务端统一 AI | 在线算命社区 |
| 程序排盘 + 规则层锚定 AI | 纯 LLM 自由发挥 |
| 就盘 L1 解读 / L2 追问 / L3 自由问答 | 脱离命盘的闲聊 |
| 无账号、无云端命盘库 | 用户自带 API Key |
| 文化参考与自我觉察 | 医疗 / 投资 / 决策依据 |

## 使用流程

1. **输入生辰** — 公历或农历（可勾选闰月），精确到分钟  
2. **浏览命盘** — 基本 · 命盘 · 细盘（四柱、五行、大运流年）  
3. **问 AI** — 流式解读 → 预设追问 chips → 就盘自由问答  
4. **导出** — 顶栏「截图」「PDF」保存当前命盘页（含完整追问记录）

分享链接 `/chart?s=…` 仅编码生辰参数（不含排盘结果）；复制前会提示隐私。本机可查看最近 20 条排盘记录（localStorage）。

## 核心能力

### 排盘（天元 · 地元 · 人元）

四柱（藏干、十神、纳音、旬空、长生）、起运、大运、流年、小运；胎元、命宫、身宫；刑冲合害；五行统计。

### 规则层 · 子平综参（服务端）

滴天髓、子平格局、穷通调候、观命总观、断事、六亲多维验证等，在服务端全量计算；**三阶读盘**（直断 / 结构提示 / 阶段侧重）由 `reading.py` 编排，高置信内容才进入 AI 上下文。

| 对用户 | 对 AI（服务端） |
|--------|-----------------|
| 命盘与运限数据 | 完整 `build_insight()` |
| 当前大运 / 流年摘要 | 观命、断事、三关、典籍 citations |
| L2 预设追问 chips | 按年龄与命盘动态生成 |

网页 **不展示** 程序化断语面板（v1.14 起）；规则层仅服务端供 AI 智能解读，避免界面与 AI 两套表述。

### AI · 问

- **L1** — `POST /api/analyze`：SSE 流式解读，章节按年龄与命盘组织  
- **L2** — 解读下方 chips → `POST /api/ask`  
- **L3** — 输入框就盘追问，可带会话 history（SSE）

## 架构概览

```
生辰 → BaziService 排盘
     → mingli / reading 规则层（全量计算 + 分级呈现）
     → build_insight + BM25 典籍检索
     → public_insight（最小字段）→ 前端
     → ensure_ai_insight（完整规则层）→ DeepSeek 流式解读 / 追问
```

- 读盘分层：[docs/READING.md](docs/READING.md)  
- 系统模块：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
- UI 规范：[docs/DESIGN.md](docs/DESIGN.md)  
- 部署运维：[DEPLOY.md](DEPLOY.md)

## 技术栈

| 层 | 选型 |
|----|------|
| 后端 | FastAPI · Pydantic · httpx · lunar-python |
| AI | DeepSeek Chat Completions（SSE） |
| 前端 | Jinja2 · 原生 JS · CSS（无 React 构建链） |
| 知识 | JSON 语料 · bazi-wiki · BM25 检索 |
| 部署 | Nginx · systemd · Let's Encrypt |

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

公网部署见 [DEPLOY.md](DEPLOY.md)。

## 项目结构

```
wenyuan/
├── app/
│   ├── main.py              # 页面路由、健康检查
│   ├── api/routes.py        # /api/chart · analyze · ask
│   ├── core/                # 排盘、规则层、读盘、发布过滤
│   └── services/ai.py       # DeepSeek 提示词与 SSE
├── knowledge/               # 典籍 JSON、bazi-wiki、BM25
├── templates/               # index · chart · privacy
├── static/                  # theme.css · app.js · 导出库
├── tests/                   # pytest + 黄金命例
├── docs/
│   ├── ARCHITECTURE.md      # 系统架构
│   ├── READING.md           # 三阶读盘
│   └── DESIGN.md            # UI/UX 规范
├── DEPLOY.md                # 部署说明
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
| **v1.14.3** | 导出截图/PDF 时完整包含追问记录 |
| **v1.14.2** | 顶栏「截图 / PDF」双按钮 |
| **v1.14** | 移除程序化断事 UI；规则层仅服务端供 AI |
| **v1.13** | 三阶读盘：直断 / 结构提示 / 人生阶段 |
| v1.10 | 观命总观、BM25、AI 校验、黄金命例 |
| v1.6+ | 六亲多维验证、断事层、子平综参 |

## 支持项目

[wenyuan.online](https://wenyuan.online/) 上的 AI 解读与追问使用作者自购的 DeepSeek Token，无广告、无付费墙。若你觉得问元有用，欢迎自愿赞赏，用于补贴 API 与服务器成本（**非必需，不影响任何功能**）。站点页脚也有 [支持作者](https://wenyuan.online/support) 入口。

<p align="center">
  <img src="docs/assets/wechat-donate.jpg" alt="微信赞赏码" width="280">
</p>

<p align="center"><sub>微信扫码 · 自愿赞赏</sub></p>

## 仓库与许可

- GitHub：[github.com/goodisok/wenyuan](https://github.com/goodisok/wenyuan)（MIT）  
- 语料说明：[knowledge/ATTRIBUTION.md](knowledge/ATTRIBUTION.md)  
- 更新 wiki 语料：`python scripts/sync_wiki.py`  
- 安装 git hook（去除 Cursor co-author）：`powershell -ExecutionPolicy Bypass -File scripts/install_git_hooks.ps1`

免责声明：输出仅供文化参考，不构成人生决策依据。详见 [隐私说明](https://wenyuan.online/privacy)。
