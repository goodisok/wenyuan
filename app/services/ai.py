# -*- coding: utf-8 -*-
"""DeepSeek 命理解读服务。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

import httpx

from app.config import settings

Style = Literal["classic", "modern"]


class AIAnalysisService:
    @staticmethod
    def _format_chart_summary(chart: dict[str, Any]) -> str:
        meta = chart.get("meta", {})
        lines = [
            f"【命主】性别 {meta.get('gender_label')}，生肖 {meta.get('zodiac')}，虚岁 {meta.get('age')} 岁",
            f"【生辰】阳历 {meta.get('birth_time', {}).get('solar')} / 农历 {meta.get('birth_time', {}).get('lunar')}",
            f"【日主】{meta.get('day_master')}（{meta.get('day_master_wuxing')}）",
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
        lines.append(f"\n【五行统计】木{wx.get('木',0)} 火{wx.get('火',0)} 土{wx.get('土',0)} 金{wx.get('金',0)} 水{wx.get('水',0)}")
        dayun = chart.get("dayun", [])[:3]
        if dayun:
            lines.append("\n【大运前三步】")
            for d in dayun:
                lines.append(f"  {d.get('ganzhi')} ({d.get('start_year')}-{d.get('end_year')})")
        return "\n".join(lines)

    @classmethod
    def _build_prompt(cls, chart: dict[str, Any], style: Style) -> str:
        summary = cls._format_chart_summary(chart)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if style == "classic":
            persona = (
                "你是一位精通子平命理的学者，行文可参考《滴天髓》《子平真诠》的体系，"
                "但须用现代人能读懂的文言白话夹杂语体，条理清晰。"
            )
        else:
            persona = (
                "你是一位命理顾问，用清晰、温和的现代中文解读命盘，"
                "避免过度宿命论，侧重性格倾向与人生节奏提示。"
            )

        return f"""{persona}

请根据以下命盘信息，从格局、五行喜忌、性格特点、事业财运、感情婚姻、健康注意等维度做系统分析。
要求：
1. 分章节用小标题组织，每节 2-4 句要点
2. 结合十神、纳音、大运给出可操作建议
3. 对关键流年做简要提示
4. 不作绝对吉凶断语，注明「仅供参考」
5. 当前分析时间：{now}

命盘数据：
{summary}
"""

    @classmethod
    async def analyze(cls, chart: dict[str, Any], style: Style = "classic") -> str:
        api_key = settings.deepseek_api_key
        if not api_key:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后使用 AI 解读")

        prompt = cls._build_prompt(chart, style)
        url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.deepseek_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
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
