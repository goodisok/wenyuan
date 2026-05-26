# -*- coding: utf-8 -*-
"""
子平综参 · 命理规则层

综合子平排盘、滴天髓体用、穷通宝鉴调候、子平真诠格局、
三命通会神煞、渊海子平喜用倾向等各家要义。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.ditiansui import analyze as ditiansui_analyze
from app.core.guanming import build_guanming
from app.core.duanshi import analyze as duanshi_analyze
from app.core.publish import publish_duanshi, publish_sanguan
from app.core.sanguan import analyze as sanguan_analyze
from app.core.qiongtong import lookup as qiongtong_lookup
from app.core.shensha import analyze as shensha_analyze
from app.core.yongshen import analyze as yongshen_analyze
from app.core.ziping import analyze as ziping_analyze

KERNEL = "子平综参"
METHOD_NOTE = "先观命盘全息（滴天髓天道地道人道），再断高置信人事；模棱两可者不上断"
SOURCES = [
    "子平", "滴天髓", "穷通宝鉴", "子平真诠", "渊海子平",
    "三命通会", "千里命稿", "神峰通考", "协纪辨方书",
]


def _shishen_summary(pillars: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in pillars:
        ss = p.get("shishen", "")
        if ss and ss != "日主":
            counts[ss] = counts.get(ss, 0) + 1
        for cg in p.get("dizhi", {}).get("canggan", []):
            css = cg.get("shishen", "")
            if css:
                counts[css] = counts.get(css, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _current_dayun(dayun: list[dict[str, Any]]) -> dict[str, Any] | None:
    year = datetime.now().year
    for d in dayun:
        if d.get("start_year", 0) <= year <= d.get("end_year", 0):
            return {
                "ganzhi": d.get("ganzhi"),
                "start_year": d.get("start_year"),
                "end_year": d.get("end_year"),
            }
    return dayun[0] if dayun else None


def _current_liunian(dayun: list[dict[str, Any]]) -> dict[str, Any] | None:
    year = datetime.now().year
    for d in dayun:
        for ln in d.get("liunian", []):
            if ln.get("year") == year:
                return {"ganzhi": ln.get("ganzhi"), "year": ln.get("year")}
    return None


def _plain_highlights(
    meta: dict[str, Any],
    guanming: dict[str, Any],
    dts: dict[str, Any],
    qt: dict[str, str],
    geju: dict[str, Any],
    yongshen: dict[str, Any],
    shensha: dict[str, Any],
    duanshi: dict[str, Any],
    sanguan: dict[str, Any],
    relations: list[str],
) -> list[str]:
    lines: list[str] = []
    if guanming.get("summary"):
        lines.append(f"【观命总观】{guanming['summary']}")
    for layer in guanming.get("layers") or []:
        if layer.get("lines"):
            lines.append(f"【{layer.get('name')}】{layer['lines'][0]}")
    dm = meta.get("day_master", "")
    wx = meta.get("day_master_wuxing", "")
    de = dts.get("de_ling", {})
    tg = dts.get("tong_gen", {})
    cl = dts.get("climate", {})
    body_pat = dts.get("pattern", {})

    lines.append(
        f"日主{dm}（{wx}），月令{de.get('month_branch', '')}，"
        f"时令{de.get('status', '')}，根气{tg.get('summary', '')}，"
        f"强弱{dts.get('day_master_strength', '平衡')}。"
    )
    if geju.get("type"):
        purity = geju.get("purity", {})
        lines.append(
            f"格局：{geju['type']}（{geju.get('origin', '')}），"
            f"清纯度{purity.get('level', '平')} — {geju.get('note', '')[:60]}"
        )
    if yongshen.get("summary"):
        lines.append(f"喜用倾向：{yongshen['summary']}。")
    if qt.get("hint"):
        lines.append(f"穷通宝鉴：{qt['hint']}。")
    if cl.get("note"):
        lines.append(f"季节气候：{cl.get('season', '')}{cl.get('climate', '')}，{cl.get('note')}。")
    if body_pat.get("type") and body_pat["type"] != "正格":
        lines.append(f"体用倾向：{body_pat['type']} — {body_pat.get('note', '')}")
    if shensha.get("items"):
        names = "、".join(i["name"] for i in shensha["items"][:4])
        lines.append(f"神煞辅助：{names}（须合格局参看）。")
    if relations:
        lines.append(f"四柱关系：{'、'.join(relations[:5])}" + ("…" if len(relations) > 5 else ""))
    for item in duanshi.get("items") or []:
        lines.append(f"【断{item.get('topic')}】{item.get('verdict')}（{item.get('source')}）")
    for g in sanguan.get("gates") or []:
        lines.append(
            f"【{g.get('name')}·{g.get('confidence')}置信】{g.get('verdict')} "
            f"（{g.get('schools_agree')}家印证）"
        )
    if sanguan.get("chuan"):
        lines.append(f"【盲派穿】{'、'.join(sanguan['chuan'][:4])}")
    return lines


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_stem = meta.get("day_master", "")
    month_branch = pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""

    dts = ditiansui_analyze(chart)
    qt = qiongtong_lookup(day_stem, month_branch)
    geju = ziping_analyze(chart)
    shensha = shensha_analyze(chart)
    duanshi_raw = duanshi_analyze(chart)
    sanguan_raw = sanguan_analyze(chart)
    duanshi = publish_duanshi(duanshi_raw, sanguan_raw)
    sanguan = publish_sanguan(sanguan_raw)
    yongshen = yongshen_analyze(
        chart,
        strength=dts.get("day_master_strength", "平衡"),
        tiao_hou=qt.get("hint", ""),
        geju=geju,
    )
    relations = chart.get("pillars_relations") or []
    shishen = _shishen_summary(pillars)

    tiao_hou = qt["hint"]
    dts_tiao = dts.get("tiao_hou", "")
    if dts_tiao and dts_tiao != tiao_hou:
        tiao_hou = f"{tiao_hou}；滴天髓：{dts_tiao}"

    guanming = build_guanming(
        chart,
        dts=dts,
        geju=geju,
        yongshen=yongshen,
        shensha=shensha,
        shishen_summary=shishen,
        tiao_hou=tiao_hou,
        relations=relations,
        chuan_list=sanguan_raw.get("chuan") or [],
        current_dayun=_current_dayun(chart.get("dayun", [])),
        current_liunian=_current_liunian(chart.get("dayun", [])),
    )

    highlights = _plain_highlights(
        meta, guanming, dts, qt, geju, yongshen, shensha, duanshi, sanguan, relations
    )

    return {
        "kernel": KERNEL,
        "method_note": METHOD_NOTE,
        "guanming": guanming,
        "day_master_strength": dts.get("day_master_strength", "平衡"),
        "strength_score": dts.get("strength_score"),
        "stem_nature": dts.get("stem_nature"),
        "de_ling": dts.get("de_ling"),
        "tong_gen": dts.get("tong_gen"),
        "de_zhu": dts.get("de_zhu"),
        "climate": dts.get("climate"),
        "tiao_hou": tiao_hou,
        "qiongtong": qt,
        "ditiansui": dts,
        "geju": geju,
        "yongshen": yongshen,
        "shensha": shensha,
        "duanshi": duanshi,
        "sanguan": sanguan,
        "shishen_summary": shishen,
        "pattern": dts.get("pattern"),
        "changsheng_map": dts.get("changsheng_map"),
        "highlights": highlights,
        "sources": list(SOURCES),
    }
