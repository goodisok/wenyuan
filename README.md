# 问元 Wenyuan

探问天地人三元 — 基于 FastAPI 的八字排盘系统，在 [fate_web](https://github.com/lichengguang/fate_web) 基础上重构，提供更清晰的架构、更完整的命盘信息与更现代的交互体验。

## 特性

| 能力 | 说明 |
|------|------|
| 四柱八字 | 年月日时，含藏干、五行着色 |
| 十神 | 年、月、时柱十神，日柱标注日主 |
| 纳音 | 四柱纳音五行 |
| 胎元 / 命宫 / 身宫 | 来自 `lunar-python` EightChar |
| 大运 · 流年 | 起止年份、年龄、流年列表 |
| 小运 | 起运前小运与对应流年 |
| 五行统计 | 四柱五行分布概览 |
| AI 解读 | DeepSeek（可选，手动触发，不依赖 Session） |
| REST API | `POST /api/chart`、`POST /api/analyze` |

## 技术栈

- **后端**: FastAPI + Pydantic + httpx
- **历法**: lunar-python
- **前端**: Jinja2 + 原生 JS，深色国风主题

## 快速开始

```bash
cd wenyuan
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY（AI 功能可选）
python run.py
```

浏览器打开 [http://localhost:8000](http://localhost:8000)

API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

## 项目结构

```
wenyuan/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 环境配置
│   ├── schemas.py       # 请求/响应模型
│   ├── api/routes.py    # REST 路由
│   ├── core/bazi.py     # 排盘核心
│   └── services/ai.py   # AI 解读
├── templates/           # 页面模板
├── static/              # CSS / JS
├── tests/
└── run.py
```

## API 示例

```bash
curl -X POST http://localhost:8000/api/chart \
  -H "Content-Type: application/json" \
  -d '{"date_type":"solar","birth_date":"1990-05-15","birth_time":"12:30","gender":"male"}'
```

## 与 fate_web 的主要改进

1. **架构**: 分层（core / api / services），类型校验，可独立调用 API
2. **命盘信息**: 十神、纳音、胎元命宫身宫、五行统计
3. **AI**: 无 Session 依赖，用户主动触发；支持古典 / 现代两种风格
4. **体验**: 统一深色主题、响应式四柱展示、OpenAPI 文档
5. **测试**: pytest 覆盖核心排盘逻辑

## 许可证

MIT
