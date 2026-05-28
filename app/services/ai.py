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
from app.core.reading import build_output_format

Style = Literal["classic", "modern"]  # classic=古典命例(传统术语), modern=现代人物(古今映射)

AI_STYLE_LABEL = "子平直断"

OUTPUT_FORMAT = build_output_format(None)

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
            lines.append("【传统备注·不作分析依据】神煞仅供参考，应以五行生克制化、格局旺衰为根本判断：")
            for i in sh["items"]:
                m = i.get("modern", "")
                lines.append(f"  · {i['name']}（{i.get('position','')}）— {i.get('note','')} {'→'+m if m else ''}")
        ds = insight.get("duanshi") or {}
        if ds.get("summary"):
            lines.append(f"【断事总论】{ds['summary']}")
        for item in ds.get("items") or []:
            verdict = item.get("display_verdict") or item.get("verdict", "")
            tier = item.get("display_tier") or item.get("publish_tier", "")
            tier_tag = {"assert": "直断", "hint": "结构提示", "structure": "宫位"}.get(tier, "")
            lines.append(
                f"【断·{item.get('topic')}·{tier_tag}】{verdict}（力度{item.get('level')}）"
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
            tier = g.get("display_tier") or g.get("publish_tier", "")
            tier_tag = {"assert": "直断", "hint": "结构提示", "structure": "宫位"}.get(tier, "")
            verdict = g.get("display_verdict") or g.get("verdict", "")
            lines.append(
                f"【{g.get('name')}·{tier_tag}】{verdict} "
                f"（{g.get('schools_agree')}家印证）"
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
        dd = insight.get("dayun_detail") or {}
        if dd.get("current_year_detail"):
            y = dd["current_year_detail"]
            triggers = y.get("triggers", [])
            if triggers:
                lines.append(f"【流年触发】{y.get('liunian_ganzhi')}年：{'；'.join(t['detail'] for t in triggers[:5])}")
            key_ms = y.get("key_months", [])
            if key_ms:
                m_lines = []
                for m in key_ms[:4]:
                    m_trig = "、".join(t["relation"]+t["target"] for t in m.get("triggers", []))
                    m_lines.append(f"{m['month_name']}({m['ganzhi']})→{m_trig}")
                lines.append(f"【流月应期】关键月份：{'；'.join(m_lines)}")
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
        from app.core.classical_ref import format_for_ai

        cref = format_for_ai(insight.get("classical_refs") or [])
        if cref:
            lines.append(cref)
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
    def _accuracy_rules(cls) -> str:
        return (
            "【断语原则】\n"
            "1. 以命盘与下方规则层摘要为唯一依据，该高则高、该平则平、该凶则凶，不讨好、不粉饰。\n"
            "2. 开篇须点明规则层格局全称与日主强弱标签；全文强弱表述须统一，"
            "规则层为「平衡/中和」时只用这两字，禁止再写「身强」「身弱」「偏强」「偏弱」。\n"
            "3. 「直断」项可断具体吉凶与应期；「结构提示」可论十神宫位倾向（财星透藏、父星位置、配偶星等），"
            "但勿断言具体事件（如必离婚、必破财、父母早亡）。\n"
            "4. 具体事件应期：仅可引用「直断应期年份」列表内的公元年；无列表则运限用大运/流年干支描述。\n"
            "5. 无直断支撑时，禁止写「必破财、必暴富、必离婚、克妻、父母早亡」等断言；"
            "可写结构倾向（如财路宽窄、感情波折风险、父母缘厚薄）。\n"
            "6. 格局清纯、偏枯、中和、从格、假格等如实表述，可谈局限、波折、晚成、起伏。\n"
            "7. 引用典籍须与当前格局/日主/调候相关；不作脱离命盘的闲聊。\n"
        )

    @classmethod
    def _citation_guide(cls) -> str:
        return (
            "【典籍引用】按格局与调候择典：正官→三命通会，七杀→渊海子平，伤官→子平真诠，"
            "特格→滴天髓从化篇，调候→穷通宝鉴日主×月令，旺衰→滴天髓体用篇。"
            "写出与命盘相关的原文或精要，勿空提书名。\n"
        )

    @classmethod
    def _system_prompt(cls, style: Style = "modern", *, for_ask: bool = False) -> str:
        accuracy = cls._accuracy_rules()
        cite = cls._citation_guide()
        if style == "classic":
            base = (
                "你是「问元」资深子平命理师。此命造多为古籍命例，请用传统子平术语解读。\n"
                f"{accuracy}"
                f"{cite}"
                "【古典语境】可用官贵、商贾、文途、武职等传统表述；大运用干支与运限描述。\n"
                "可与任铁樵等原评对照，但须用自身逻辑论证，勿照抄。\n"
                "论父母、兄弟、子女、财运：无「直断」时可论十神宫位结构倾向，"
                "勿写父母必克、早亡、必破财、必大发等断言。\n"
            )
        else:
            base = (
                "你是「问元」资深子平命理师。须锚定命盘与规则层综合作智能解读。\n"
                f"{accuracy}"
                f"{cite}"
                "【现代语境】十神映射现代生活：官杀→职位权力与竞争，财→收入资产，"
                "印→学历资质与背书，食伤→技能表达与创造，比劫→合作竞争与人际。\n"
                "用现代中文直断，避免「官至七品」「武职发用」等古代官制断语。\n"
                "男女命同一套旺衰格局体系；配偶、事业、财运均按盘中十神与运限论，不作道德评判。\n"
            )
        if for_ask:
            return base + "就用户所问作答，Markdown，须有命盘与大运依据，3-8 段。"
        return base

    @classmethod
    def _output_format(cls, insight: dict[str, Any] | None) -> str:
        return build_output_format(insight)

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
        ins = insight or chart.get("insight") or {}
        if not ins.get("duanshi"):
            from app.core.insight import build_insight

            ins = build_insight(chart)
        insight_text = cls._format_insight(ins)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        parts = [f"当前分析时间：{now}", insight_text, f"命盘数据：\n{summary}"]
        if analysis:
            parts.append(f"已有 L1 解读：\n{analysis}")
        if for_ask:
            user_content = f"{chr(10).join(parts)}\n\n用户问题：{question}"
            messages: list[dict[str, str]] = [
                {"role": "system", "content": cls._system_prompt(style, for_ask=True)},
            ]
            for h in (history or [])[-100:]:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": user_content})
            return messages

        user_content = f"{chr(10).join(parts)}\n\n{cls._output_format(ins)}"
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
            "temperature": 0.54,
            "max_tokens": 4096,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
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
    async def _complete_once(
        cls,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.45,
    ) -> str:
        url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
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
    def _revision_prompt(cls, warnings: list[str]) -> str:
        return (
            "请修订上一稿，消除以下问题，保留正确的格局、旺衰与运限分析：\n"
            + "\n".join(f"- {w}" for w in warnings)
            + "\n平衡/中和命统一用规则层标签，勿混用身强与身弱。"
            "结构提示可保留十神宫位倾向，勿添加无直断支撑的具体事件断言或列表外年份。"
        )

    @classmethod
    async def _finalize_analysis(
        cls,
        messages: list[dict[str, str]],
        text: str,
        insight: dict[str, Any] | None,
    ) -> str:
        vr = validate_analysis(text, insight)
        warnings = list(vr.get("warnings") or [])
        if not warnings:
            return text
        revised_messages = messages + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": cls._revision_prompt(warnings)},
        ]
        return await cls._complete_once(revised_messages, temperature=0.45)

    @classmethod
    async def _complete_with_revision(
        cls,
        messages: list[dict[str, str]],
        insight: dict[str, Any] | None,
    ) -> str:
        text = await cls._complete_once(messages, temperature=0.54)
        return await cls._finalize_analysis(messages, text, insight)

    @classmethod
    async def analyze(
        cls,
        chart: dict[str, Any],
        style: Style = "modern",
        insight: dict[str, Any] | None = None,
    ) -> str:
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        ins = insight or chart.get("insight")
        return await cls._complete_with_revision(messages, ins)

    @classmethod
    async def analyze_stream(
        cls,
        chart: dict[str, Any],
        style: Style = "modern",
        insight: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        ins = insight or chart.get("insight")
        async for chunk in cls._stream_completion(messages):
            yield chunk

    @classmethod
    def analyze_sse(
        cls,
        chart: dict[str, Any],
        style: Style = "modern",
        insight: dict[str, Any] | None = None,
    ):
        cls.ensure_available()
        messages = cls._build_messages(chart, insight, style)
        ins = insight or chart.get("insight")

        async def finalize(text: str) -> str:
            return await cls._finalize_analysis(messages, text, ins)

        async def stream() -> AsyncIterator[str]:
            async for chunk in cls._stream_completion(messages):
                yield chunk

        return cls.sse_events(stream(), finalize=finalize)

    @classmethod
    async def ask(
        cls,
        chart: dict[str, Any],
        question: str,
        style: Style = "modern",
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
        style: Style = "modern",
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
    def sse_events(
        stream: AsyncIterator[str],
        *,
        finalize=None,
    ) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            full: list[str] = []
            try:
                async for text in stream:
                    full.append(text)
                    payload = json.dumps({"text": text}, ensure_ascii=False)
                    yield f"event: chunk\ndata: {payload}\n\n"
                text = "".join(full)
                if finalize is not None:
                    text = await finalize(text)
                done = json.dumps({"analysis": text}, ensure_ascii=False)
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
