# 问元 Wenyuan

探问天地人三元 — 八字排盘与 AI 解读 Web 服务。基于 FastAPI，在 [fate_web](https://github.com/lichengguang/fate_web) 基础上重构。

## 在线试用

**Demo：** [http://119.91.54.153/](http://119.91.54.153/)

输入公历或农历生辰即可排盘；配置 AI Key 后可使用古典 / 现代解读（当前为 v0.2.0 基线，v1.0 功能见下方路线图）。

## 产品定位

**问元**是部署于云服务器的命盘工具：程序排盘，AI 在命盘上下文中解读与答疑（非开放闲聊）。支持 PC 与手机，多用户同时使用，无账号注册。

| 是 | 不是 |
|----|------|
| 公网命盘 + 服务端 AI | 在线算命平台 |
| URL 分享命盘入口 | 云端存储用户生辰 |
| 就盘 L1/L2/L3 问答 | 脱离命盘的聊天 |

**完整需求与规划（已定稿）：** **[PRODUCT.md](PRODUCT.md)**（PRD v2.0）

## 特性

| 能力 | 说明 |
|------|------|
| 四柱八字 | 藏干、十神、纳音、旬空、刑冲合害 |
| 运势 | 起运、大运、流年、小运 |
| 规则层 | BaziInsight 摘要锚定 AI |
| AI | L1 八章解读 · L2 预设追问 · L3 就盘问答（SSE 流式） |
| 分享 | URL 编码生辰，本地最近 20 条历史 |
| API | `/api/chart` · `/api/analyze` · `/api/ask` |

## 路线图

基线 **v0.2.0** → 目标 **v1.0**（见 PRODUCT.md 验收清单）：

1. Phase 1 — URL 分享、localStorage、隐私页  
2. Phase 2 — 闰月、规则层、刑冲合害、起运等  
3. Phase 3 — 三元分区 UI（响应式）  
4. Phase 4 — L2/L3、SSE、AI 缓存  
5. Phase 5 — 公网部署、多用户验收  

## 技术栈

- **后端**: FastAPI + Pydantic + httpx  
- **历法**: lunar-python  
- **前端**: Jinja2 + 原生 JS，深色国风主题  

## 快速开始

**Windows：**

```bat
start.bat
```

**手动：**

```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
copy .env.example .env     # 配置 DEEPSEEK_API_KEY
python run.py
```

- 主页：http://localhost:8000  
- API 文档：http://localhost:8000/docs  

**公网 Demo：** [http://119.91.54.153/](http://119.91.54.153/)（腾讯云部署，v0.2.0）

部署说明见 PRODUCT.md Phase 5（`DEPLOY.md` 待编写）。

## 项目结构

```
wenyuan/
├── app/           # 后端
├── templates/     # 页面
├── static/        # 前端资源
├── tests/
├── PRODUCT.md     # 产品需求定稿（PRD v2.0）
└── run.py
```

## API 示例

```bash
curl -X POST http://localhost:8000/api/chart \
  -H "Content-Type: application/json" \
  -d '{"date_type":"solar","birth_date":"1990-05-15","birth_time":"12:30","gender":"male","is_leap_month":false}'
```

## 许可证

MIT
