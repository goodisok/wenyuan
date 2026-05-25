# 问元 Wenyuan



探问天地人三元 — 八字排盘与 AI 解读 Web 服务。基于 FastAPI，在 [fate_web](https://github.com/lichengguang/fate_web) 基础上重构。



## 在线试用



**Demo：** [http://119.91.54.153/](http://119.91.54.153/)



输入公历或农历生辰即可排盘；程序综参子平诸家，AI 在命盘上下文中解读（**v1.4**）。



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

| 规则层 | **子平综参**：格局（子平真诠/三命通会）、旺衰体用（滴天髓）、调候（穷通 120 组）、喜用倾向、神煞辅助 |

| 知识库 | 182+ 条结构化语料（穷通120 + 滴天髓/子平/渊海/三命/千里命稿），打分检索锚定 AI |

| AI | L1 九章解读（含历史校准）· L2 预设追问 · L3 就盘问答（SSE 流式） |

| 分享 | URL 编码生辰，本地最近 20 条历史 |

| API | `/api/chart` · `/api/analyze` · `/api/ask` |



## 版本



当前 **v1.4.0** — 结构化典籍语料库（原文/条文/命例）、混合检索、AI 章节引用。



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



**公网 Demo：** [http://119.91.54.153/](http://119.91.54.153/)（v1.4.0，部署后更新）



部署说明见 **[DEPLOY.md](DEPLOY.md)**。



## 项目结构



```

wenyuan/

├── app/           # 后端（mingli / ziping / shensha / yongshen / knowledge）

├── knowledge/     # 语料库 corpus/data/*.json + snippets

├── templates/     # 页面

├── static/        # 前端资源

├── tests/

├── PRODUCT.md     # 产品需求定稿（PRD v2.0）

├── DEPLOY.md      # 云服务器部署

└── run.py

```



## API 示例



```bash

curl -X POST http://localhost:8000/api/chart \

  -H "Content-Type: application/json" \

  -d '{"date_type":"solar","birth_date":"1990-05-15","birth_time":"12:30","gender":"male","is_leap_month":false}'

```



## 许可证



MIT（知识库部分参考 [bazi-skill](https://github.com/jinchenma94/bazi-skill)，见 `knowledge/ATTRIBUTION.md`）

