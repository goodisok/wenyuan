# -*- coding: utf-8 -*-
"""DeepSeek 命理解读服务。"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Literal

import httpx

from app.config import settings
from app.core.ai_validate import validate_analysis

Style = Literal["classic", "modern"]  # 保留 API 兼容，提示词已统一

AI_STYLE_LABEL = "子平直断"

OUTPUT_FORMAT = """
你是专业子平命理师，以断事为要。综参滴天髓、穷通宝鉴、子平真诠、渊海子平、三命通会、千里命稿及问元知识库（bazi-wiki 概念与命例），
结合规则层（观命总观、格局、断事、六亲人事多维验证、大运应期、语料）直断，不必过度委婉，不必作道德说教。
须先依【观命总观】展开天道/地道/人道/体用/调候/流通，再论具体人事。
规则层已过滤：仅含高置信断事与六亲高置信印证；模棱两可、单源低置信不在规则层，勿臆造。
规则层「断事」「六亲印证」须展开；高置信须写明盲派/子平/千里各家信号。应期年份须在规则层窗口内。重要论断标注出处。Markdown 格式，按以下章节（保留 ## 标题）：

## 一、命局总断
据观命总观：格局、旺衰、体用、流通，三句话定调。

## 二、父母与原生家庭
若规则层有父母断语或过三关第一关，据其展开；否则只论年月宫位与结构，不断具体分离离异。

## 三、婚姻感情
若规则层有婚姻断语则直断；若无，只论妻宫/夫星、桃花、冲刑结构，不断婚变吉凶。

## 四、事业财运
格局喜忌与大运，断职业方向与财禄起伏（规则层无财运断语时只论结构）。

## 五、健康灾厄
五行偏枯与冲刑，断易伤之处（非医疗诊断）。

## 六、大运应期
逐步大运，断 3-5 个已应或将应之事（学业、搬迁、婚恋、家庭变故、破财升官等），给出年份；须与规则层应期窗口一致或在其范围内。

## 七、历史校准
据大运流年，断 3-5 件可能已发生之具体事件（含父母离异、分居等若规则层有象），供命主核对。

文末：
> 问元 AI 子平断事，以所给命盘与规则层为准。
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
        gm = insight.get("guanming") or {}
        if gm.get("summary"):
            lines.append(f"【观命总观·滴天髓】{gm['summary']}（{gm.get('method', '')}）")
        if gm.get("verse"):
            lines.append(f"【滴天髓歌诀】{gm['verse']}")
        for layer in gm.get("layers") or []:
            layer_lines = layer.get("lines") or []
            if layer_lines:
                lines.append(
                    f"【{layer.get('name')}·{layer.get('subtitle', '')}】"
                    + "；".join(layer_lines[:3])
                )
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
        ds = insight.get("duanshi") or {}
        if ds.get("summary"):
            lines.append(f"【断事总论】{ds['summary']}")
        for item in ds.get("items") or []:
            lines.append(
                f"【断·{item.get('topic')}】{item.get('verdict')}（力度{item.get('level')}）"
            )
            for r in item.get("reasons") or []:
                lines.append(f"  因：{r}")
            for w in item.get("windows") or []:
                lines.append(f"  应期：大运{w.get('dayun')} {w.get('years')} {w.get('note')}")
        lq = ds.get("liuqin") or {}
        if lq and ds.get("items"):
            lines.append(
                f"【六亲】父{lq.get('father', {}).get('star')}@{lq.get('father', {}).get('locations')} "
                f"母{lq.get('mother', {}).get('star')}@{lq.get('mother', {}).get('locations')}"
            )
        sg = insight.get("sanguan") or {}
        if sg.get("summary"):
            lines.append(f"【六亲人事·多维验证】{sg['summary']}（{sg.get('method', '')}）")
        if sg.get("chuan"):
            lines.append(f"【盲派穿象】{'、'.join(sg['chuan'][:6])}")
        for g in sg.get("gates") or []:
            lines.append(
                f"【{g.get('name')}】{g.get('verdict')} "
                f"（置信{g.get('confidence')}，{g.get('schools_agree')}家印证）"
            )
            for s in g.get("signals") or []:
                lines.append(f"  · [{s.get('school')}] {s.get('text')}")
            for w in g.get("windows") or []:
                lines.append(f"  应期：大运{w.get('dayun')} {w.get('years')} {w.get('note')}")
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
            lines.append("【典籍语料】")
            for c in cites:
                ch = f"（{c.get('chapter')}）" if c.get("chapter") else ""
                prefix = f"《{c.get('source', '')}》{ch}"
                body = c.get("text", "")
                if c.get("pillars"):
                    body = f"例{c['pillars']}：{body}"
                if c.get("commentary"):
                    body += f" 按：{c['commentary']}"
                lines.append(f"{prefix}{body}")
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
    def _system_prompt(cls, *, for_ask: bool = False) -> str:
        base = (
            "你是「问元」专业命理师，以子平断事为本。须锚定命盘与规则层（含断事、过三关多维验证、大运应期），"
            "直断父母、婚姻、财运、灾厄等具体人事，给出应期年份。可引典籍出处。"
            "规则层已过滤：仅含高置信断事与过三关高置信项；模棱两可、单源低置信的内容不会出现在规则层，切勿臆造。"
            "某类人事若规则层未列，对应章节从略或只论结构，不断具体吉凶。"
            "不作脱离命盘的闲聊；不回避离异、破财、灾厄等已高置信断语。"
            "用现代中文直断，干脆明确，不断事、不空泛。"
        )
        if for_ask:
            return base + " 就用户所问直断，Markdown，须有规则层与大运依据，3-8 段。"
        return base

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
                {"role": "system", "content": cls._system_prompt(for_ask=True)},
            ]
            for h in (history or [])[-100:]:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": user_content})
            return messages

        user_content = f"{chr(10).join(parts)}\n\n{OUTPUT_FORMAT}"
        return [
            {"role": "system", "content": cls._system_prompt()},
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
    @classmethod
    def _append_validation_note(cls, text: str, insight: dict[str, Any] | None) -> str:
        vr = validate_analysis(text, insight)
        if not vr.get("warnings"):
            return text
        note = "；".join(vr["warnings"])
        return f"{text}\n\n---\n> 规则层校对：{note}\n"

    @classmethod
    async def analyze(
        cls,
        chart: dict[str, Any],
        style: Style = "classic",
        insight: dict[str, Any] | None = None,
    ) -> str:
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        ins = insight or chart.get("insight")
        text = await cls._complete_once(messages)
        return cls._append_validation_note(text, ins)

    @classmethod
    async def analyze_stream(
        cls,
        chart: dict[str, Any],
        style: Style = "classic",
        insight: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        ins = insight or chart.get("insight")
        buf: list[str] = []
        async for chunk in cls._stream_completion(messages):
            buf.append(chunk)
            yield chunk
        full = "".join(buf)
        noted = cls._append_validation_note(full, ins)
        if noted != full:
            yield noted[len(full) :]

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
