# 问元 Wenyuan

探问天地人三元 — **自研**八字排盘与 AI 解读 Web 服务。

程序负责准确排盘与多层规则断事，AI 在命盘上下文中解读与答疑。支持公历/农历、PC 与手机、多用户并发，无账号注册，服务端不落库。

## 在线试用

**Demo：** [http://119.91.54.153/](http://119.91.54.153/)（v1.8.3）

输入生辰即可排盘；配置 DeepSeek API Key 后可使用 L1 解读、L2 追问、L3 就盘问答。

## 产品定位

| 是 | 不是 |
|----|------|
| 公网命盘 + 服务端 AI | 在线算命平台 / 社区 |
| URL 分享命盘入口 | 云端存储用户生辰 |
| 就盘 L1/L2/L3 问答 | 脱离命盘的 AI 闲聊 |
| 程序规则层 + 典籍语料锚定 | 纯 LLM 自由发挥 |

完整需求见 **[PRODUCT.md](PRODUCT.md)**（PRD v2.0）。

## 核心能力

### 排盘 · 天元地元人元

四柱八字（藏干、十神、纳音、旬空）、起运、大运、流年、小运；胎元、命宫、身宫；刑冲合害破穿。

### 规则层 · 子平综参

综参子平诸家，非独尊一家：

| 模块 | 典籍 / 方法 | 作用 |
|------|-------------|------|
| 旺衰体用 | 滴天髓 | 得令、通根、气候 |
| 调候 | 穷通宝鉴（120 组） | 寒暖燥湿 |
| 格局 | 子平真诠、三命通会 | 格局清纯 |
| 喜用 | 渊海子平 | 喜忌倾向 |
| 神煞 | 三命通会 | 辅助参考 |
| **断事层** | 子平六亲 + 千里应期 | 父母 / 婚姻 / 财运直断 |
| **过三关** | 盲派穿 + 子平 + 千里 | 父母 / 兄弟 / 子女多维交叉验证 |

### 知识库 · 典籍语料

182+ 条结构化语料（穷通 120 + 滴天髓 / 子平真诠 / 渊海子平 / 三命通会 / 千里命稿），打分检索后注入 AI，要求标注出处。见 `knowledge/corpus/`。

### AI · 问

- **L1** 九章解读（含历史校准），SSE 流式
- **L2** 预设追问（含断事 / 过三关动态生成）
- **L3** 就盘自定义问答

## 架构

```
生辰输入 → BaziService 排盘
         → mingli 规则层（ziping / ditiansui / qiongtong / yongshen / shensha）
         → duanshi 断事层 + sanguan 过三关多维验证
         → knowledge 语料检索（≤18 条）
         → insight 摘要 → AI（DeepSeek）流式解读
         → 前端展示（命盘 + 要点 + 断事 + 三关 + 典籍引用）
```

## 版本

当前 **v1.8.3**

| 版本 | 要点 |
|------|------|
| v1.8.3 | 年月日时分离输入、四柱表格神煞、大运横滑与词条 tooltip |
| v1.8 | 产品化 UI（Hero、能力卡、命盘顶栏）+ 设计规范 + 样式/缓存修复 |
| v1.7 | 前端 v2.0 全面升级；统一「子平直断」单一解读 |
| v1.6 | 过三关·多维验证（盲派穿 + 子平六亲 + 千里应期交叉印证） |
| v1.5 | 断事层（父母 / 婚姻 / 财运 + 大运应期） |
| v1.4 | 结构化典籍语料库、混合检索 |
| v1.3 | 子平综参规则层、轻量知识库 |
| v1.2 | 多学派内核、UX 升级 |
| v1.1 | 滴天髓阐微旺衰体用 |
| v1.0 | 天地人三元排盘、L1/L2/L3、URL 分享 |

## 技术栈

- **后端**：FastAPI · Pydantic · httpx
- **历法**：lunar-python
- **AI**：DeepSeek API（可配置开关）
- **前端**：Jinja2 · 原生 JS · 深色国风主题
- **部署**：Nginx · systemd · 腾讯云

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
│   ├── core/          # 排盘、规则层（mingli / duanshi / sanguan / ziping …）
│   ├── services/      # AI 解读
│   └── routes/        # API 路由
├── knowledge/
│   ├── corpus/data/   # 结构化典籍 JSON
│   └── snippets.py    # 轻量条文
├── templates/         # 页面模板
├── static/            # 前端资源
├── tests/             # pytest
├── docs/DESIGN.md     # 前端设计规范
├── .cursor/rules/     # Cursor UI 规则（wenyuan-ui.mdc）
├── PRODUCT.md         # 产品需求（PRD）
├── DEPLOY.md          # 部署说明
└── run.py
```

## API 示例

```bash
curl -X POST http://localhost:8000/api/chart \
  -H "Content-Type: application/json" \
  -d '{"date_type":"solar","birth_date":"1990-05-15","birth_time":"12:30","gender":"male","is_leap_month":false}'
```

## 仓库

GitHub：[github.com/goodisok/wenyuan](https://github.com/goodisok/wenyuan)

## 许可证

MIT

知识库语料部分参考 [bazi-skill](https://github.com/jinchenma94/bazi-skill)，详见 [knowledge/ATTRIBUTION.md](knowledge/ATTRIBUTION.md)。
