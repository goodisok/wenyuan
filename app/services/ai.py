# -*- coding: utf-8 -*-
"""DeepSeek 命理解读服务。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

import httpx

from app.config import settings

Style = Literal["classic", "modern"]

OUTPUT_FORMAT = """
请严格使用 Markdown 格式输出，按以下章节组织（保留 ## 标题，每节 3-5 句，要点清晰）：

## 一、三元总览
- 天（命局格局、气势）：…
- 地（五行流通、平衡）：…
- 人（性格气质、行事风格）：…

## 二、格局与十神
结合四柱十神、日主强弱，说明命局特点与潜在优势。

## 三、五行喜忌
说明五行分布、喜用神倾向，以及日常可留意之处。

## 四、性格特质
以具体场景描述性格倾向，避免空泛形容词堆砌。

## 五、事业财运
结合大运节奏，给出方向性建议（不作绝对预测）。

## 六、感情婚姻
描述相处模式与沟通倾向，语气平和务实。

## 七、健康留意
从五行对应脏腑角度给出养生提示，注明非医疗建议。

## 八、大运流年提示
结合所给大运，点出 2-3 个值得留意的阶段与应对思路。

文末单独一行引用块：
> 以上解读由问元 AI 生成，仅供文化参考，不作人生决策依据。
"""


class AIAnalysisService:
    @staticmethod
    def _format_chart_summary(chart: dict[str, Any]) -> str:
        meta = chart.get("meta", {})
        lines = [
            f"【命主】性别 {meta.get('gender_label')}，生肖 {meta.get('zodiac')}，虚岁 {meta.get('age')} 岁",
            f"【生辰】阳历 {meta.get('birth_time', {}).get('solar')} / 农历 {meta.get('birth_time', {}).get('lunar')}",
            f"【日主】{meta.get('day_master')}（{meta.get('day_master_wuxing')}） 十二长生={meta.get('day_dishi')}",
            f"【胎元】{meta.get('tai_yuan')}  【命宫】{meta.get('ming_gong')}  【身宫】{meta.get('shen_gong')}",
            "",
            "【四柱】",
        ]
        for p in chart.get("pillars", []):
            lines.append(
                f"  {p.get('label')}: {p.get('ganzhi')} "
                f"十神={p.get('shishen')} 纳音={p.get('nayin')}"
            )
        wx = chart.get("wuxing_stats", {})
        lines.append(
            f"\n【五行统计】木{wx.get('木', 0)} 火{wx.get('火', 0)} "
            f"土{wx.get('土', 0)} 金{wx.get('金', 0)} 水{wx.get('水', 0)}"
        )
        dayun = chart.get("dayun", [])[:5]
        if dayun:
            lines.append("\n【大运前五步】")
            for d in dayun:
                lines.append(
                    f"  {d.get('ganzhi')} ({d.get('start_year')}-{d.get('end_year')}) "
                    f"虚岁 {d.get('start_age')}-{d.get('end_age')}"
                )
        return "\n".join(lines)

    @classmethod
    def _system_prompt(cls, style: Style) -> str:
        if style == "classic":
            return (
                "你是「问元」平台的命理学者，精通子平命理，行文可参考《滴天髓》《子平真诠》体系。"
                "以天地人三元为纲，文白相间、典雅而不晦涩。"
                "分析须紧扣命盘数据，引用十神、纳音、大运时须与所给信息一致，不可臆造。"
            )
        return (
            "你是「问元」平台的命理顾问，以天地人三元视角解读命盘。"
            "用清晰、温和的现代中文阐述，避免宿命论与恐吓式断语，侧重性格倾向与人生节奏提示。"
            "分析须紧扣命盘数据，不可脱离所给四柱与大运信息。"
        )

    @classmethod
    def _user_prompt(cls, chart: dict[str, Any]) -> str:
        summary = cls._format_chart_summary(chart)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""请根据以下命盘做系统解读。当前分析时间：{now}

命盘数据：
{summary}

{OUTPUT_FORMAT}"""

    @classmethod
    async def analyze(cls, chart: dict[str, Any], style: Style = "classic") -> str:
        api_key = settings.deepseek_api_key
        if not api_key:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后使用 AI 解读")

        url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": cls._system_prompt(style)},
                {"role": "user", "content": cls._user_prompt(chart)},
            ],
            "temperature": 0.65,
            "max_tokens": 4096,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"AI 接口错误 {resp.status_code}: {resp.text[:200]}")
            body = resp.json()

        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError("AI 返回格式异常")
        content = choices[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("AI 返回内容为空")
        return content.strip()
