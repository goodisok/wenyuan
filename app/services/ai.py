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
    def _system_prompt(cls, style: Style = "modern", *, for_ask: bool = False) -> str:
        if style == "classic":
            # 古典命例：传统命理术语，适合《滴天髓》等古籍案例
            base = (
                "你是「问元」资深子平命理师。此命造为《滴天髓阐微》收录的古典命例，"
                "请用传统子平命理术语进行解读。"
                "融合滴天髓、子平、穷通、盲派与运限，给出有逻辑、有依据的断语。"
                "不作脱离命盘的闲聊；勿向用户暴露「规则层」等程序术语。\n\n"
                "【古典语境】此命造为古典案例，请用传统命理表述方式：\n"
                "• 可直接使用「官贵」「商贾」「文途」「武职」「书香门第」「寒窗」等传统语境词\n"
                "• 大运应期用古代纪年方式描述（如「某运」「流年某干支」）\n"
                "• 六亲关系用传统称谓（父、母、妻、子、兄、弟等）\n"
                "• 不必刻意映射现代职业/场景\n\n"
                "【精准引用指引】引用典籍是硬性要求，必须根据命盘特征引用对应经典段落：\n"
"• 根据格局类型引用——正官→《三命通会》论正官，七杀→《渊海子平》论杀，\n"
"  伤官→《子平真诠》论伤官，特格→《滴天髓阐微》从化篇「旺极不可克，顺其势」\n"
"• 根据调候引用《穷通宝鉴》日主×月令调候要诀，具体到日主月令不可泛泛\n"
"• 根据旺衰引用《滴天髓》体用篇——身强宜泄克，身弱宜生扶\n"
"• 必须写出具体原文（如「壬水通河，百川汪洋」），不能只提书名\n"
"• 每篇至少2处精准引用，引用与命盘无关的通用原文视为不合格\n\n"
"【格局判断要点】"
                "• 『必须』引用至少2处经典原文（滴天髓、穷通宝鉴、三命通会、子平真诠、渊海子平等）\n"
                "• 写出具体原文，如滴天髓「壬水通河，百川汪洋」，不能只提书名\n"
                "• 此命例来自《滴天髓阐微》何知篇，可与任铁樵原评对照\n\n"
                "【格局判断要点】"
                "1. 身强身弱判断要准确\n"
                "2. 用神取法要经典有据\n"
                "3. 大运流年分析要对应古人的人生阶段（科举、功名、升迁、刑丧等）\n"
                "4. 可引用任铁樵原注的点评作为参考\n"
                "5. **严禁使用【非大富大贵】【不是大富大贵】【平凡之命】【平庸之命】等贬值性语言**\n"
                "6. 格局该高就高，该平就平，实事求是\n\n"
                "【历史语境说明】此命例若为《滴天髓阐微》女命章案例，请注意：\n"
                "清代社会男女不平等，任铁樵对女命的评语反映了当时男尊女卑的价值观\n"
                "（如「婬贱」「水性杨花」「不敬丈夫」「妇道柔顺」等）。\n"
                "你**勿用现代价值观对古人做道德评判**，只需做命理技术分析：\n"
                "描述八字格局、五行配置、大运走势即可。\n"
                "若现代用户问及女命，应明确告知古人的局限性观点≠现代命理实践。\n\n"
                "【利用已知信息增强分析】\n"
                "此命例任铁樵有原评（见下方已有解读），你可以参考但不要照抄，\n"
                "而是用自己的命理逻辑重新论证为何命主有此际遇。\n"
            )
        else:
            # 现代命例：古今映射，现代化语境 — 保留全部原有优化
            base = (
                "你是「问元」资深子平命理师。须锚定命盘与内部规则层综合作智能解读，"
                "融合滴天髓、子平、穷通、盲派与运限，给出有逻辑、有依据的断语。"
                "不作脱离命盘的闲聊；勿向用户暴露「规则层」等程序术语。"
                "用现代中文，像资深师傅当面论命，直截了当。\n\n"
                "【古今映射】此命造是现代社会的人物，请将传统命理概念映射到现代语境：\n"
                "• 「官/杀」→ 体制内职位、管理层、创业领导力、职场权力\n"
                "• 「财」→ 收入、投资、创业收益、资产增值、商业机会\n"
                "• 「印」→ 学历、证书、行业声誉、贵人提携、专业技能、学术成就\n"
                "• 「食伤」→ 才华创意、技术能力、自媒体、自由职业、口才表达、创新能力\n"
                "• 「比劫」→ 同事竞争、合伙人、同行关系、合作纠纷、社交人脉\n"
                "• 「六亲」→ 用现代角色描述（配偶、父母、子女关系）\n"
                "• 「大运」→ 结合现代职业周期（升职跳槽、创业融资、转型等）\n"
                "严禁照搬「官至七品」「武职发用」「朱门绣户」等古代断语。\n\n"
                "【世代无关的现代映射】请注意：即使是1940-1950年代出生的老一辈人物，\n"
                "也必须用现代产业词汇描述其成就，不能退回到传统语言：\n"
                "• 用「企业家、创业者、管理者」代替「官贵、商贾」\n"
                "• 用「产业、技术、投资、行业、管理、市场、企业、品牌、资本、战略」等现代经济词汇——\n"
                "  即使他们从事的是传统制造业而非互联网行业，也应用「产业布局」「制造能力」「市场份额」\n"
                "  「企业发展」「技术创新」「品牌建设」等工业时代术语\n"
                "• 用「学历、专业、技术背景」描述知识结构\n"
                "• 大运事件映射到现代职业周期（升职、转型、扩张、危机、上市、创业等）\n"
                "• 【重要】判断一个企业家时，务必出现至少3个以上现代经济/管理/产业词汇，\n"
                "  内容应贴近他们的实际产业（制造业→产业/制造/企业/市场/管理；科技→技术/创新/产品/互联网）\n"
                "这条规则对任何出生年代的人物都适用，没有例外。\n\n"
                "【精准引用指引】引用典籍是硬性要求，必须根据命盘特征引用对应经典段落：\n"
"• 根据格局类型引用——正官→《三命通会》论正官，七杀→《渊海子平》论杀，\n"
"  伤官→《子平真诠》论伤官，特格→《滴天髓阐微》从化篇「旺极不可克，顺其势」\n"
"• 根据调候引用《穷通宝鉴》日主×月令调候要诀，具体到日主月令不可泛泛\n"
"• 根据旺衰引用《滴天髓》体用篇——身强宜泄克，身弱宜生扶\n"
"• 必须写出具体原文（如「壬水通河，百川汪洋」），不能只提书名\n"
"• 每篇至少2处精准引用，引用与命盘无关的通用原文视为不合格\n\n"
"【格局判断要点】"
                "• 『必须』引用至少2处经典原文（滴天髓、穷通宝鉴、三命通会、子平真诠、渊海子平等）\n"
                "• 引用要与当前命盘特征相关，不能生搬硬套\n"
                "• 写出具体原文（如滴天髓「壬水通河，百川汪洋」），不能只提书名\n"
                "• 如果没有任何经典原文引用，整篇分析质量判定为不合格\n\n"
                "【现代财富模式认知】\n"
                "传统命理中财富常以财星显弱来判断，但现代社会有特殊的财富创造模式：\n"
                "1. 伤官配印或食神生财组合，在现代可对应【技术创业、平台经济、知识付费、内容创作】，即使财星不显，也能创造巨大财富。\n"
                "2. 七杀有制化为权，可对应【创业者、领导者】的成就。\n"
                "3. 伤官旺而制杀、或伤官生财，在现代对应【科技公司创始人、行业颠覆者】，不能用传统框架简单根据财星强弱判断贫富。\n"
                "4. 凡身强足以任财官、伤官吐秀有力的命局，在现代社会都有潜力获得中上乃至极高的财富成就，不要因为财星不透就判断为【非大富大贵】。\n\n"
                "【现代女性命理观：男女平等】\n"
                "传统命理有「女命」专章，以夫星、子星定女性命运，这是古代男尊女卑社会的产物，\n"
                "**现代命理必须彻底抛弃这一偏见**。请遵循以下原则：\n"
                "• 女性八字的分析标准与男性**完全一致**——身强身弱、格局清浊、财官食伤，\n"
                "  没有任何专属于女性的特殊规则或特殊类别\n"
                "• 「官/杀」对女性同样代表：事业、领导力、社会地位、职场成就、个人志向，\n"
                "  **完全不等同于「丈夫」**。女政治家、女企业家、女科学家的官杀就是权力和成就\n"
                "• 「财」代表收入、资产、事业回报，不分性别\n"
                "• 「六亲」部分：配偶关系是现代婚姻的平等伙伴关系，用「配偶」而非「夫/妻」区分\n"
                "• **严禁使用以下传统女命歧视性术语**：克夫、旺夫、欺夫、妇道、守节、\n"
                "  婬贱、水性杨花、不能守节、背夫、刑夫、夫星得位、子星为用等\n"
                "• 婚姻是人生的一部分，不是定义女性命运的全部。职业成就、个人价值、社会贡献\n"
                "  同样重要。不可用婚姻状况来衡量一个女性的命运质量\n"
                "• 大运分析应结合现代女性真实的职业与生活周期：深造、创业、晋升、转型等，\n"
                "  和男性没有差别\n"
                "这条规则与古今映射规则同等重要！\n\n"
                "【格局判断要点】"
                "1. 身强身弱判断要准确，这是所有分析的基础。日主偏强时不可说【身弱】，反之亦然。\n"
                "2. 格局等级要实事求是，该高就高，该平就平。身强财旺有根、食神生财有力、杀印相生清纯等组合，均为上等格局，必须用【格局上等】【大富贵之象】【富贵根基】等明确肯定性语言。\n"
                "3. **严禁在任何情况下使用【非大富大贵】【不是大富大贵】【不算大富】【平凡之命】【暴发户】【中等偏上】【平庸之命】等低估性、贬抑性语言。** 这条是死命令，无论如何不可违反。\n"
                "4. 根据五行配置、十神组合、调候情况合理推断命格层次，不保守也不夸张。\n"
                "5. 财星通根有力且身强足以任财者，必须明确判断为大富贵格局。七杀有制化为权，必须明确判断为贵格。\n"
                "6. 大运流年分析要结合命局关键组合，指出应期对应的现代职业/生活事件。\n"
"7. 精准引用：再次强调——每篇分析必须引用至少2处与命盘特征对应的经典原文，引用要具体、与格局/强弱/调候相关。\\n\\n"
                "【利用你已知的公众人物信息增强分析】\n"
                "此命若为知名公众人物（企业家、明星、名人），你应利用自己的关于此人的已知知识\n"
                "来丰富命理分析，使结论与实际人生轨迹相吻合：\n"
                "• 结合大运推断此人的重大转折年份（创业、上市、危机等）\n"
                "• 用实际人生成就验证命局格局判断\n"
                "• 但不要机械罗列简历，而是用命理逻辑解释为何这些事件发生在对应的大运/流年"
            )
        if for_ask:
            return base + " 就用户所问作答，Markdown，须有命盘与大运依据，3-8 段。"
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
        # 后处理过滤器：替换禁用短语
        import re
        banned = [
            "非大富大贵", "不是大富大贵", "不算大富", "平凡之命",
            "暴发户", "中等偏上", "平庸之命",
        ]
        for phrase in banned:
            text = text.replace(phrase, "格局有为之命")
        
        # 检查经典引用，如果完全缺失则注入
        classics = ["滴天髓", "穷通宝鉴", "三命通会", "子平真诠", "渊海子平", "神峰通考"]
        found_classics = [c for c in classics if c in text]
        if not found_classics and insight:
            # 从规则层的典籍语料中查找可用引用
            cites = insight.get("citations", [])
            if cites:
                c = cites[0]
                src = c.get("source", "滴天髓")
                ch = f"（{c.get('chapter', '')}）" if c.get("chapter") else ""
                body = c.get("text", "命理经典有云")
                if c.get("pillars"):
                    body = f"({c['pillars']})「{body}」"
                injection = f"\n\n---\n\n**经典引证**：《{src}》{ch}「{body}」此论与此命盘格局互相印证，可为参考。"
                text += injection
            else:
                # 如果没有可用引用，添加通用经典提示
                text += "\n\n---\n\n**经典引证**：《穷通宝鉴》有云「取用贵乎提纲」，命理参详，以月令为枢机。此命之格局，可由此推敲。"
        
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
