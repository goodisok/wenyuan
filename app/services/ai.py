# -*- coding: utf-8 -*-
"""DeepSeek 命理解读服务。"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Literal

import httpx

from app.config import settings

Style = Literal["classic", "modern"]

OUTPUT_FORMAT = """
请以子平为基础，综参滴天髓、穷通宝鉴、子平真诠、渊海子平、三命通会、千里命稿、神峰通考等典籍要义解读（不作单一派系独断）。
规则层已给出格局、喜用倾向、神煞与典籍摘要——须以之为锚，重要论断请标注出处（如「据《穷通宝鉴》……」）。
若用户消息中含「典籍参考摘要」，优先参此，勿与规则层结论矛盾。Markdown 格式，按以下章节（保留 ## 标题，每节 3-5 句）：

## 一、三元总览（天地人）
- 天：格局气势、大运节律
- 地：五行流通、刑冲合害
- 人：性情才能、行事风格

## 二、格局与体用
据规则层「格局」（子平真诠/三命通会）与「体用倾向」（滴天髓）综参，述清纯/破格倾向，勿断唯一格局。

## 三、十神性情
结合四柱十神、藏干与六亲（渊海子平），述性格倾向。

## 四、寒暖调候与喜用
综参穷通宝鉴调候与喜用倾向（扶抑/调候/通关），强调倾向参考、非唯一用神。

## 五、事业财运
结合大运与格局，述方向性节奏（不作绝对预测）。

## 六、感情婚姻
述相处模式，语气平和。

## 七、健康留意
从五行角度作养生提示，注明非医疗建议。

## 八、大运流年
结合大运流年，点出 2-3 个值得留意的阶段。

## 九、历史校准（可选）
根据大运流年组合，提出 2-3 个可能已发生的人生阶段特征（如学业、搬迁、转折），供用户对照验证；语气为「可能」「倾向」，不作断言。

文末引用块：
> 以上解读由问元 AI 综参子平诸家生成，仅供文化参考，不作人生决策依据。
"""

OFF_TOPIC_HINT = "请就当前命盘提问，问元不支持脱离命盘的闲聊。"


class AIAnalysisService:
    @staticmethod
    def ensure_available() -> None:
        if not settings.ai_enabled:
            raise ValueError("AI 解读暂时关闭，请稍后再试")
        if not settings.deepseek_api_key:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后使用 AI 解读")

    @staticmethod
    def _format_insight(insight: dict[str, Any] | None) -> str:
        if not insight:
            return ""
        lines = [
            f"【规则层·{insight.get('kernel', '子平综参')}】",
            f"参考：{', '.join(insight.get('sources') or ['子平', '滴天髓', '穷通宝鉴'])}",
            f"日主 {insight.get('day_master')}（{insight.get('day_master_wuxing')}）"
            f" 强弱={insight.get('day_master_strength')} 评分={insight.get('strength_score')}",
        ]
        for h in insight.get("highlights") or []:
            lines.append(f"· {h}")
        qt = insight.get("qiongtong") or {}
        if qt.get("hint"):
            lines.append(f"【穷通宝鉴】{qt['hint']}")
        de = insight.get("de_ling") or {}
        if de:
            lines.append(
                f"【得令】{de.get('status')} 月支{de.get('month_branch')} "
                f"本气{de.get('main_qi')} 长生{de.get('changsheng')}"
            )
        tg = insight.get("tong_gen") or {}
        if tg:
            lines.append(f"【通根】{tg.get('summary')} 得分{tg.get('score')}")
        dz = insight.get("de_zhu") or {}
        if dz:
            lines.append(f"【天干助损】{dz.get('summary')} 得助{dz.get('helps')} 受克泄{dz.get('drains')}")
        cl = insight.get("climate") or {}
        if cl:
            lines.append(f"【气候】{cl.get('season')}{cl.get('climate')} — {cl.get('note')}")
        if insight.get("tiao_hou"):
            lines.append(f"【调候综参】{insight.get('tiao_hou')}")
        ss = insight.get("shishen_summary") or {}
        if ss:
            top = list(ss.items())[:5]
            lines.append(f"【十神分布】{', '.join(f'{k}{v}' for k, v in top)}")
        geju = insight.get("geju") or {}
        if geju.get("type"):
            purity = geju.get("purity") or {}
            lines.append(
                f"【格局·{geju.get('source', '子平真诠')}】{geju['type']} "
                f"({geju.get('origin', '')}) 清纯{purity.get('level', '')} — {geju.get('note', '')}"
            )
        ys = insight.get("yongshen") or {}
        if ys.get("summary"):
            lines.append(f"【喜用倾向】{ys['summary']}（{ys.get('note', '')[:50]}）")
        sh = insight.get("shensha") or {}
        if sh.get("items"):
            names = "、".join(i["name"] for i in sh["items"])
            lines.append(f"【神煞辅助】{names} — {sh.get('note', '')[:40]}")
        pat = insight.get("pattern") or {}
        if pat:
            lines.append(f"【体用倾向】{pat.get('type')} — {pat.get('note')}")
        lines.append(f"【五行】{insight.get('wuxing_counts')} 旺{insight.get('wuxing_strongest')} 弱{insight.get('wuxing_weakest')}")
        cd = insight.get("current_dayun") or {}
        if cd:
            lines.append(f"当前大运 {cd.get('ganzhi')} ({cd.get('start_year')}-{cd.get('end_year')})")
        cy = insight.get("current_year_liunian") or {}
        if cy:
            lines.append(f"当前流年 {cy.get('ganzhi')} ({cy.get('year')})")
        rel = insight.get("pillars_relations") or []
        if rel:
            lines.append(f"刑冲合害 {', '.join(rel)}")
        cites = insight.get("citations") or []
        if cites:
            lines.append("【典籍参考摘要】")
            for c in cites:
                lines.append(f"《{c.get('source', '')}》{c.get('text', '')}")
        return "\n".join(lines)

    @classmethod
    def _format_chart_summary(cls, chart: dict[str, Any]) -> str:
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
            cg = " ".join(
                f"{c['name']}({c.get('shishen', '')})" for c in p.get("dizhi", {}).get("canggan", [])
            )
            lines.append(
                f"  {p.get('label')}: {p.get('ganzhi')} "
                f"十神={p.get('shishen')} 纳音={p.get('nayin')} 旬空={p.get('xunkong', '')} "
                f"长生={p.get('changsheng', '')} 藏干={cg}"
            )
        jieqi = meta.get("jieqi") or {}
        if jieqi:
            lines.append(
                f"\n【节令】前{jieqi.get('prev')} 后{jieqi.get('next')} "
                f"当前建{jieqi.get('current_jie')}{jieqi.get('current_qi')}"
            )
        rel = chart.get("pillars_relations") or []
        if rel:
            lines.append(f"\n【刑冲合害】{', '.join(rel)}")
        qy = chart.get("qiyun") or {}
        if qy:
            lines.append(f"\n【起运】{qy.get('description', '')}")
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
    def _system_prompt(cls, style: Style, *, for_ask: bool = False) -> str:
        base = (
            "你是「问元」平台命理顾问，具备子平、滴天髓、穷通宝鉴、子平真诠、三命通会、"
            "渊海子平、千里命稿等典籍素养。以程序规则层（格局、旺衰、调候、喜用倾向）为锚，"
            "重要论断宜标注典籍出处。借鉴诸家会通，不作单一派系独断。"
            "须严格锚定所给命盘与规则层摘要，不可臆造四柱与大运。"
            "喜用神仅作倾向参考，不得断言唯一用神。拒绝脱离命盘的闲聊。"
        )
        if for_ask:
            return base + " 回答简洁，Markdown 格式，3-8 段，须有规则层依据。"
        if style == "classic":
            return (
                base + " 行文典雅，可引经据典但须与所给数据一致，文白相间、明晰可读。"
            )
        return base + " 用清晰现代中文阐述，避免宿命论与恐吓式断语。"

    @classmethod
    def _build_messages(
        cls,
        chart: dict[str, Any],
        insight: dict[str, Any] | None,
        style: Style,
        *,
        analysis: str = "",
        question: str = "",
        history: list[dict[str, str]] | None = None,
        for_ask: bool = False,
    ) -> list[dict[str, str]]:
        summary = cls._format_chart_summary(chart)
        insight_text = cls._format_insight(insight or chart.get("insight"))
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        parts = [f"当前分析时间：{now}", insight_text, f"命盘数据：\n{summary}"]
        if analysis:
            parts.append(f"已有 L1 解读：\n{analysis}")
        if for_ask:
            user_content = f"{chr(10).join(parts)}\n\n用户问题：{question}"
            messages: list[dict[str, str]] = [
                {"role": "system", "content": cls._system_prompt(style, for_ask=True)},
            ]
            for h in (history or [])[-8:]:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": user_content})
            return messages

        user_content = f"{chr(10).join(parts)}\n\n{OUTPUT_FORMAT}"
        return [
            {"role": "system", "content": cls._system_prompt(style)},
            {"role": "user", "content": user_content},
        ]

    @classmethod
    def _headers(cls) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def _stream_completion(cls, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "temperature": 0.65,
            "max_tokens": 4096,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload, headers=cls._headers()) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise RuntimeError(f"AI 接口错误 {resp.status_code}: {body[:200]!r}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                    text = delta.get("content")
                    if text:
                        yield text

    @classmethod
    async def _complete_once(cls, messages: list[dict[str, str]]) -> str:
        url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "temperature": 0.65,
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=cls._headers())
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

    @classmethod
    async def analyze(
        cls,
        chart: dict[str, Any],
        style: Style = "classic",
        insight: dict[str, Any] | None = None,
    ) -> str:
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        return await cls._complete_once(messages)

    @classmethod
    async def analyze_stream(
        cls,
        chart: dict[str, Any],
        style: Style = "classic",
        insight: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        async for chunk in cls._stream_completion(messages):
            yield chunk

    @classmethod
    async def ask(
        cls,
        chart: dict[str, Any],
        question: str,
        style: Style = "classic",
        insight: dict[str, Any] | None = None,
        analysis: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> str:
        cls.ensure_available()
        if not chart.get("pillars"):
            raise ValueError("命盘数据无效")
        q = question.strip()
        if not q:
            raise ValueError("请输入问题")
        messages = cls._build_messages(
            chart, insight, style,
            analysis=analysis, question=q, history=history, for_ask=True,
        )
        return await cls._complete_once(messages)

    @classmethod
    async def ask_stream(
        cls,
        chart: dict[str, Any],
        question: str,
        style: Style = "classic",
        insight: dict[str, Any] | None = None,
        analysis: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        cls.ensure_available()
        if not chart.get("pillars"):
            raise ValueError("命盘数据无效")
        q = question.strip()
        if not q:
            raise ValueError("请输入问题")
        messages = cls._build_messages(
            chart, insight, style,
            analysis=analysis, question=q, history=history, for_ask=True,
        )
        async for chunk in cls._stream_completion(messages):
            yield chunk

    @staticmethod
    def sse_events(stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            full: list[str] = []
            try:
                async for text in stream:
                    full.append(text)
                    payload = json.dumps({"text": text}, ensure_ascii=False)
                    yield f"event: chunk\ndata: {payload}\n\n"
                done = json.dumps({"analysis": "".join(full)}, ensure_ascii=False)
                yield f"event: done\ndata: {done}\n\n"
            except Exception as exc:
                err = json.dumps({"error": str(exc)}, ensure_ascii=False)
                yield f"event: error\ndata: {err}\n\n"

        return _gen()

    @staticmethod
    def sse_events_ask(stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            full: list[str] = []
            try:
                async for text in stream:
                    full.append(text)
                    payload = json.dumps({"text": text}, ensure_ascii=False)
                    yield f"event: chunk\ndata: {payload}\n\n"
                done = json.dumps({"answer": "".join(full)}, ensure_ascii=False)
                yield f"event: done\ndata: {done}\n\n"
            except Exception as exc:
                err = json.dumps({"error": str(exc)}, ensure_ascii=False)
                yield f"event: error\ndata: {err}\n\n"

        return _gen()
