# -*- coding: utf-8 -*-
"""
问元 · 读盘编排层（三阶断法）

1. 结构层：格局、旺衰、宫位、运限 — 始终完整计算
2. 断语层：各家信号合并为 claim，保留 raw
3. 呈现层：publish tier × 人生阶段 → 展示与 AI 锚定

原则：年龄只调「侧重与表述」，不删除已算出的结构信息。
"""
from __future__ import annotations

from typing import Any, Literal

from app.core.lifestage import (
    GATE_TOPIC,
    DUANSHI_TOPIC,
    build_lifestage,
    topic_priority,
)

PublishTier = Literal["assert", "hint", "structure", "withhold"]
DisplayTier = Literal["assert", "hint", "structure", "hidden"]

TIER_LABELS = {
    "assert": "直断",
    "hint": "结构提示",
    "structure": "宫位结构",
    "hidden": "",
    "withhold": "",
}

DUANSHI_TOPIC_TO_GATE = {"父母": "parents"}


def _gate_map(sanguan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {g["id"]: g for g in (sanguan.get("gates") or [])}


def publish_tier_duanshi(item: dict[str, Any], gates: dict[str, dict[str, Any]]) -> PublishTier:
    level = str(item.get("level", ""))
    if level == "强":
        return "assert"
    gate_id = DUANSHI_TOPIC_TO_GATE.get(str(item.get("topic", "")))
    if gate_id and gates.get(gate_id, {}).get("confidence") == "高":
        return "assert"
    if level == "中":
        return "hint"
    return "withhold"


def publish_tier_gate(gate: dict[str, Any]) -> PublishTier:
    conf = str(gate.get("confidence", ""))
    if conf == "高":
        return "assert"
    if conf == "中":
        return "hint"
    return "withhold"


def stage_adjust_tier(tier: PublishTier, stage_id: str, topic_id: str) -> DisplayTier:
    pri = topic_priority(stage_id, topic_id)
    if pri == "hidden":
        if tier == "assert":
            return "structure"
        if tier == "hint":
            return "structure"
        return "hidden"
    if pri == "secondary" and tier == "assert":
        return "assert"
    if tier == "withhold":
        return "hidden"
    return tier  # type: ignore[return-value]


def _structure_line_duanshi(item: dict[str, Any], liuqin: dict[str, Any]) -> str:
    topic = str(item.get("topic", ""))
    if topic == "父母":
        f = liuqin.get("father", {})
        m = liuqin.get("mother", {})
        return (
            f"父母宫：父星{f.get('star')} {','.join(f.get('locations') or []) or '不现'}；"
            f"母星{m.get('star')} {','.join(m.get('locations') or []) or '不现'}"
        )
    if topic == "婚姻":
        sp = liuqin.get("spouse", {})
        return f"婚姻宫（日支）：配偶星{sp.get('star')} {','.join(sp.get('locations') or []) or '不现'}"
    if topic == "财运":
        return "财帛：以财星、比劫与大运喜忌配合观察，不断具体应期"
    return f"{topic}宫位结构待参"


def publish_duanshi_tiered(duanshi: dict[str, Any], sanguan: dict[str, Any]) -> dict[str, Any]:
    gates = _gate_map(sanguan)
    liuqin = duanshi.get("liuqin") or {}
    items: list[dict[str, Any]] = []
    for raw in duanshi.get("items") or []:
        tier = publish_tier_duanshi(raw, gates)
        if tier == "withhold":
            continue
        item = dict(raw)
        item["publish_tier"] = tier
        item["topic_id"] = DUANSHI_TOPIC.get(str(item.get("topic", "")), "")
        if tier == "hint":
            item["display_verdict"] = f"结构倾向：{_structure_line_duanshi(item, liuqin)}"
        else:
            item["display_verdict"] = item.get("verdict", "")
        items.append(item)
    out = dict(duanshi)
    out["items"] = items
    assert_items = [i for i in items if i["publish_tier"] == "assert"]
    if assert_items:
        out["summary"] = "；".join(f"{i['topic']}:{i['display_verdict']}" for i in assert_items)
    elif items:
        out["summary"] = "；".join(f"{i['topic']}(结构)" for i in items)
    else:
        out["summary"] = ""
    out["publish_note"] = "直断=高置信断语；结构提示=中置信或宫位参考，不断具体应期"
    return out


def publish_sanguan_tiered(sanguan: dict[str, Any]) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []
    for raw in sanguan.get("gates") or []:
        tier = publish_tier_gate(raw)
        if tier == "withhold":
            continue
        g = dict(raw)
        g["publish_tier"] = tier
        g["topic_id"] = GATE_TOPIC.get(g.get("id", ""), "")
        if tier == "hint":
            g["display_verdict"] = f"结构参考：{g.get('verdict', '')}（中置信，宜结合运限）"
        else:
            g["display_verdict"] = g.get("verdict", "")
        gates.append(g)
    out = dict(sanguan)
    out["gates"] = gates
    high = [g for g in gates if g["publish_tier"] == "assert"]
    out["summary"] = (
        f"六亲印证：{len(high)}关直断"
        if high
        else (f"六亲印证：{len(gates)}关结构提示" if gates else "六亲印证：暂无显著信号")
    )
    if not high:
        out["chuan"] = out.get("chuan") or []
    out["publish_note"] = "直断=三家以上高置信；结构提示=中置信参考"
    return out


def apply_stage_presentation(insight: dict[str, Any], age: int) -> dict[str, Any]:
    """按人生阶段调整展示 tier，并重建 highlights。"""
    out = dict(insight)
    ls = build_lifestage(age)
    out["life_stage"] = ls
    out["age"] = age
    stage_id = ls["stage_id"]

    ds = dict(out.get("duanshi") or {})
    staged_items: list[dict[str, Any]] = []
    for item in ds.get("items") or []:
        topic_id = item.get("topic_id") or DUANSHI_TOPIC.get(str(item.get("topic", "")), "")
        pub_tier = item.get("publish_tier", "hint")
        display = stage_adjust_tier(pub_tier, stage_id, topic_id)
        if display == "hidden":
            continue
        staged = dict(item)
        staged["display_tier"] = display
        if display == "structure":
            liuqin = ds.get("liuqin") or {}
            staged["display_verdict"] = _structure_line_duanshi(staged, liuqin)
            staged["windows"] = []
        staged_items.append(staged)
    ds["items"] = staged_items
    if staged_items:
        ds["summary"] = "；".join(
            f"{i['topic']}:{i['display_verdict'][:24]}…"
            if len(i.get("display_verdict", "")) > 24
            else f"{i['topic']}:{i.get('display_verdict', '')}"
            for i in staged_items
        )
    else:
        ds["summary"] = ""
    out["duanshi"] = ds

    sg = dict(out.get("sanguan") or {})
    staged_gates: list[dict[str, Any]] = []
    for g in sg.get("gates") or []:
        topic_id = g.get("topic_id") or GATE_TOPIC.get(g.get("id", ""), "")
        pub_tier = g.get("publish_tier", "hint")
        display = stage_adjust_tier(pub_tier, stage_id, topic_id)
        if display == "hidden":
            continue
        staged = dict(g)
        staged["display_tier"] = display
        if display == "structure":
            staged["display_verdict"] = f"宫位结构：{g.get('name', '')}相关十神与宫位可参"
            staged["windows"] = []
        staged_gates.append(staged)
    sg["gates"] = staged_gates
    if staged_gates:
        n_assert = sum(1 for g in staged_gates if g.get("display_tier") == "assert")
        sg["summary"] = f"六亲印证：{n_assert}关直断" if n_assert else f"六亲印证：{len(staged_gates)}关结构参考"
    else:
        sg["summary"] = "六亲印证：当前阶段以结构层为主"
    out["sanguan"] = sg

    out["highlights"] = rebuild_highlights(out)
    return out


def rebuild_highlights(insight: dict[str, Any]) -> list[str]:
    """从最终呈现层重建命局要点，避免与面板矛盾。"""
    lines: list[str] = []
    gm = insight.get("guanming") or {}
    if gm.get("summary"):
        lines.append(f"【观命总观】{gm['summary']}")
    for layer in (gm.get("layers") or [])[:3]:
        if layer.get("lines"):
            lines.append(f"【{layer.get('name')}】{layer['lines'][0]}")
    dm = insight.get("day_master", "")
    wx = insight.get("day_master_wuxing", "")
    de = insight.get("de_ling") or {}
    tg = insight.get("tong_gen") or {}
    lines.append(
        f"日主{dm}（{wx}），月令{de.get('month_branch', '')}，"
        f"根气{tg.get('summary', '')}，强弱{insight.get('day_master_strength', '平衡')}。"
    )
    geju = insight.get("geju") or {}
    if geju.get("type"):
        lines.append(f"格局：{geju['type']} — {geju.get('note', '')[:50]}")
    ys = insight.get("yongshen") or {}
    if ys.get("summary"):
        lines.append(f"喜用倾向：{ys['summary']}。")
    rel = insight.get("pillars_relations") or []
    if rel:
        lines.append(f"四柱关系：{'、'.join(rel[:5])}")

    ls = insight.get("life_stage") or {}
    if ls.get("focus_summary"):
        lines.append(f"【当前关切】{ls['stage_label']} · 侧重{ls['focus_summary']}")

    for item in (insight.get("duanshi") or {}).get("items") or []:
        tier = item.get("display_tier", item.get("publish_tier", ""))
        label = TIER_LABELS.get(tier, "")
        verdict = item.get("display_verdict") or item.get("verdict", "")
        prefix = f"【{label}·{item.get('topic')}】" if label else f"【{item.get('topic')}】"
        lines.append(f"{prefix}{verdict}")
    for g in (insight.get("sanguan") or {}).get("gates") or []:
        tier = g.get("display_tier", g.get("publish_tier", ""))
        label = TIER_LABELS.get(tier, "直断")
        verdict = g.get("display_verdict") or g.get("verdict", "")
        lines.append(f"【{label}·{g.get('name')}】{verdict}")
    return lines


def ai_reading_brief(insight: dict[str, Any]) -> str:
    """供 AI 使用的读盘指引（与 UI 一致）。"""
    ls = insight.get("life_stage") or {}
    lines = [
        f"【读盘次序】先结构（观命总观、格局、旺衰、运限），再人事直断，最后结构提示。",
        f"【人生阶段】虚岁{ls.get('age', '')} · {ls.get('stage_label', '')} · 侧重{ls.get('focus_summary', '')}",
    ]
    hidden = [
        t["label"]
        for t in (ls.get("focus_areas") or [])
        if t.get("priority") == "hidden"
    ]
    for item in (insight.get("duanshi") or {}).get("items") or []:
        tier = item.get("display_tier", "")
        if tier == "assert":
            lines.append(f"可直断·{item.get('topic')}：{item.get('display_verdict')}")
        elif tier == "structure":
            lines.append(f"仅论结构·{item.get('topic')}：{item.get('display_verdict')}（不断应期吉凶）")
        elif tier == "hint":
            lines.append(f"结构提示·{item.get('topic')}：{item.get('display_verdict')}")
    for g in (insight.get("sanguan") or {}).get("gates") or []:
        tier = g.get("display_tier", "")
        if tier == "assert":
            lines.append(f"可直断·{g.get('name')}：{g.get('display_verdict')}")
        elif tier in ("structure", "hint"):
            lines.append(f"仅论结构·{g.get('name')}：{g.get('display_verdict')}")
    if ls.get("stage_id") == "child":
        lines.append("童年盘：感情、事业、子女不断具体吉凶与应期，只论将来宫位结构。")
    elif ls.get("stage_id") == "senior":
        lines.append("晚年盘：学业从略；健康、子女、心境可详论。")
    return "\n".join(lines)


def build_l1_chapters(insight: dict[str, Any]) -> list[tuple[str, str]]:
    """子平直断 L1 章节 — 与呈现层一致。"""
    ls = insight.get("life_stage") or {}
    sid = ls.get("stage_id", "prime")
    chapters: list[tuple[str, str]] = [
        ("命局总断", "据观命总观：格局、旺衰、体用、流通，三句话定调。"),
        ("性格与禀赋", "据十神、体用、滴天髓性情，论气质与行事倾向。"),
    ]

    def visible(topic_id: str) -> bool:
        return topic_priority(sid, topic_id) != "hidden"

    if visible("parents"):
        chapters.append(
            ("父母与原生家庭", "直断项据规则层展开；结构提示项只论年月宫位与十神。")
        )
    if visible("education") and sid in ("child", "teen", "youth"):
        chapters.append(("学业与成长", "结合大运论学习专注与成长方向。"))
    if visible("relationship"):
        chapters.append(
            ("感情婚姻", "有直断则展开；否则只论配偶星与婚姻宫结构；童年不断婚期。")
        )
    if visible("career_wealth"):
        chapters.append(("事业财运", "格局喜忌与大运；结构提示不断具体破财发财应期。"))
    if visible("children") or visible("siblings"):
        chapters.append(("六亲人事", "据已发布直断/结构提示论兄弟姊妹、子女等。"))
    if visible("health"):
        chapters.append(("健康身心", "五行偏枯与冲刑，非医疗诊断。"))
    chapters.append(
        ("大运应期", "逐步大运，断与当前阶段相符的 3–5 事；年份须在规则层窗口内。")
    )
    return chapters


def build_output_format(insight: dict[str, Any] | None = None) -> str:
    from app.core.ai_validate import collect_allowed_years, collect_citable_years

    ins = insight or {}
    ls = ins.get("life_stage") or {}
    age = ls.get("age", "")
    stage = ls.get("stage_label", "")
    focus = ls.get("focus_summary", "")
    geju_type = (ins.get("geju") or {}).get("type", "") or "（见规则层）"
    strength = ins.get("day_master_strength", "") or "（见规则层）"
    allowed = collect_citable_years(ins)
    if allowed:
        year_line = "、".join(str(y) for y in allowed[:12])
        if len(allowed) > 12:
            year_line += " 等"
        year_rule = (
            f"5. **开篇首段须写明格局为「{geju_type}」、日主强弱为「{strength}」**（与规则层一致，全文勿改口）。\n"
            f"6. 论具体公元年**仅限**：{year_line}（含大运所在年份）；其余运限用大运/流年干支描述，勿写其它年份。\n"
            "7. 无「直断」支撑的婚变、破财、父母凶吉、兄弟子女夭克等具体断辞勿写；结构提示只论宫位十神。\n"
            "8. 语气：现代中文，直截了当，像经验丰富的命理师当面断盘。"
        )
    else:
        year_rule = (
            f"5. **开篇首段须写明格局为「{geju_type}」、日主强弱为「{strength}」**（与规则层一致；若为「平衡/中和」则全文只用此二字，禁止出现「身强」「身弱」「偏强」「偏弱」）。\n"
            "6. 规则层无高置信应期窗口：**全文勿出现任何公元年份**；运限一律用大运/流年干支。\n"
            "7. 无「直断」支撑的婚变、破财、父母凶吉、兄弟子女夭克等具体断辞勿写。\n"
            "8. 语气：现代中文，直截了当，像经验丰富的命理师当面断盘。"
        )
    classic_extra = ""
    if ins.get("is_classical_fixture"):
        classic_extra = (
            "（本造为古籍四柱命例：宜用传统术语，"
            "父母/财禄无直断时只述宫位，不断具体吉凶件。）\n"
        )
    return f"""你是问元资深子平命理师。下方「规则层摘要」与「命盘数据」供内部分析，勿向用户提及「规则层」「直断」「结构提示」等程序术语。
{classic_extra}
【命主】虚岁 {age} 岁 · {stage}
【解读侧重】{focus or "综合命盘"}（议题须贴合当前人生阶段；与年龄无关者勿深断具体吉凶）

请输出 Markdown 解读，**建议章节顺序**（可微调标题）：
## 全盘定调 → ## 体用调候 → ## 性情结构 → ## 六亲人事 → ## 大运运限 → （仅有直断时）## 应期提示

要求：
1. 每章须有命理依据（十神、宫位、五行、刑冲合害、运限），忌空泛鸡汤。
2. 综参规则层摘要、典籍语料与相似古籍命例；相似例仅作参证，勿照抄。
3. 相似古籍与典籍引用须与当前格局/日主相关，无关勿凑数。
4. 童年盘勿断婚育子女具体件；晚年盘勿强调学业考试。
{year_rule}

文末：
> 以上由 AI 综参命盘生成，仅供参考。"""


def public_l2_questions(age: int) -> list[str]:
    """面向用户的通用追问（不引用程序断语）。"""
    from app.core.lifestage import build_lifestage, topic_priority

    ls = build_lifestage(age)
    sid = ls["stage_id"]
    qs: list[str] = []

    def add(q: str) -> None:
        if q and q not in qs:
            qs.append(q)

    add("请综合此盘，给我一份完整的命理解读。")
    if topic_priority(sid, "personality") != "hidden":
        add("我的性格禀赋与行事风格有何特点？")
    if topic_priority(sid, "education") != "hidden" and sid in ("child", "teen", "youth"):
        add("学业与成长方面有什么建议？")
    if topic_priority(sid, "career_wealth") != "hidden":
        add("事业与财运上有什么倾向？")
    if topic_priority(sid, "relationship") != "hidden":
        add("感情婚姻方面如何看？")
    if topic_priority(sid, "health") != "hidden":
        add("健康与身心需要注意什么？")
    add(f"虚岁{age}岁，当前大运阶段重点是什么？")
    return qs[:5]


def suggest_l2_questions(insight: dict[str, Any]) -> list[str]:
    ls = insight.get("life_stage") or {}
    sid = ls.get("stage_id", "prime")
    questions: list[str] = []

    def add(q: str) -> None:
        if q and q not in questions:
            questions.append(q)

    pri = {x["id"] for x in ls.get("focus_areas", []) if x.get("priority") == "primary"}

    if "personality" in pri or topic_priority(sid, "personality") != "hidden":
        gm = insight.get("guanming") or {}
        if gm.get("summary"):
            add("依观命总观，此盘性格与体用要点何在？")

    if "education" in pri:
        add("当前阶段学业与成长上宜注意什么？")

    if "parents" in pri:
        for item in (insight.get("duanshi") or {}).get("items") or []:
            if item.get("topic") == "父母" and item.get("display_tier") == "assert":
                add(f"父母宫直断「{item.get('display_verdict', '')[:20]}…」，应期在何运？")
                break
        else:
            add("原生家庭与父母关系结构上有何特点？")

    if "relationship" in pri:
        for item in (insight.get("duanshi") or {}).get("items") or []:
            if item.get("topic") == "婚姻":
                add("感情姻缘结构上有何倾向？" if item.get("display_tier") != "assert" else f"婚姻直断如何理解？")
                break

    if "career_wealth" in pri:
        geju = insight.get("geju") or {}
        if geju.get("type"):
            add(f"「{geju['type']}」对事业与财运有何倾向？")
        cd = insight.get("current_dayun") or {}
        if cd.get("ganzhi"):
            add(f"大运{cd['ganzhi']}阶段事业重点是什么？")

    if "health" in pri:
        add("五行偏枯上，健康与身心宜注意什么？")

    if "children" in pri:
        for g in (insight.get("sanguan") or {}).get("gates") or []:
            if g.get("id") == "children":
                add(f"子女方面「{g.get('display_verdict', '')[:16]}…」如何理解？")
                break

    ys = insight.get("yongshen") or {}
    if ys.get("summary") and len(questions) < 5:
        add("喜用倾向与当前大运是否相合？")

    if not questions:
        add(f"虚岁{ls.get('age', '')} · {ls.get('stage_label', '')}阶段最该关注什么？")

    return questions[:5]
