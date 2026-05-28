# -*- coding: utf-8 -*-
"""Shared helpers for regression / baseline flywheel scripts."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "data" / "test_suite_v4.json"

PILLAR_KEYS = ("year", "month", "day", "hour")
POS_KEYWORDS = ("贵", "富", "寿", "功名", "封侯", "封侯", "宰辅", "昌", "吉", "福", "荣", "显", "太平", "无波")
NEG_KEYWORDS = ("凶", "夭", "刑", "破", "贫", "厄", "灾", "克", "孤", "贱", "败", "亡", "不禄", "夭折")
ANCIENT_TERMS = ["官至", "七品", "朱门", "武职", "发用", "纳妾", "封侯", "状元", "进士"]
SHENSHA_ALLOWED = {"禄神", "将星", "驿马"}

# 五行生克 → 十神（日干 vs 他干）
_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
_YANG = {"甲", "丙", "戊", "庚", "壬"}
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def app_version() -> str:
    try:
        from app import __version__

        return __version__
    except Exception:
        return "unknown"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_test_suite(path: Path | None = None) -> dict[str, Any]:
    p = path or SUITE_PATH
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def parse_gz(gz: str) -> list[str]:
    parts = re.split(r"\s+", gz.strip())
    if len(parts) != 4:
        raise ValueError(f"invalid gz: {gz!r}")
    for g in parts:
        if len(g) != 2:
            raise ValueError(f"invalid pillar: {g!r}")
    return parts


def _same_yin_yang(a: str, b: str) -> bool:
    return (a in _YANG) == (b in _YANG)


def stem_shishen(day_stem: str, other_stem: str) -> str:
    if day_stem == other_stem:
        return "日主"
    dm_wx = _WUXING[day_stem]
    ot_wx = _WUXING[other_stem]
    same_yy = _same_yin_yang(day_stem, other_stem)
    if dm_wx == ot_wx:
        return "比肩" if same_yy else "劫财"
    if _SHENG[dm_wx] == ot_wx:
        return "食神" if same_yy else "伤官"
    if _KE[dm_wx] == ot_wx:
        return "偏财" if same_yy else "正财"
    if _KE[ot_wx] == dm_wx:
        return "七杀" if same_yy else "正官"
    if _SHENG[ot_wx] == dm_wx:
        return "偏印" if same_yy else "正印"
    return ""


def build_chart_from_gz(
    gz: str,
    gender: str = "male",
    *,
    day_master: str | None = None,
) -> dict[str, Any]:
    """Build a minimal chart dict from four pillars (classical cases)."""
    from app.core.bazi import BaziService
    from app.core.changsheng import changsheng
    from app.core.relations import compute_pillar_relations

    pillars_gz = parse_gz(gz)
    dm = day_master or pillars_gz[2][0]
    if pillars_gz[2][0] != dm:
        raise ValueError(f"day_master {dm} != day pillar {pillars_gz[2][0]}")

    pillars: list[dict[str, Any]] = []
    for key, ganzhi in zip(PILLAR_KEYS, pillars_gz):
        hide_ss = []
        dz = ganzhi[1]
        for cg in BaziService._canggan_list(dz):
            hide_ss.append(stem_shishen(dm, cg["name"]))
        ss = "日主" if key == "day" else stem_shishen(dm, ganzhi[0])
        pillars.append(
            BaziService._build_pillar(key, ganzhi, ss, "", "", hide_ss)
        )
    for p in pillars:
        p["changsheng"] = changsheng(dm, p["dizhi"]["name"])

    chart: dict[str, Any] = {
        "meta": {
            "gender": gender,
            "gender_label": "男" if gender == "male" else "女",
            "date_type": "solar",
            "is_leap_month": False,
            "day_master": dm,
            "day_master_wuxing": _WUXING.get(dm, ""),
            "source": "gz_fixture",
        },
        "pillars": pillars,
        "dayun": [],
        "xiaoyun": [],
        "wuxing_stats": BaziService._wuxing_stats(pillars),
        "pillars_relations": compute_pillar_relations(pillars),
    }
    return chart


def gender_to_code(g: str) -> str:
    g = (g or "").strip()
    if g in ("male", "female"):
        return g
    if g in ("男", "M", "m"):
        return "male"
    if g in ("女", "F", "f"):
        return "female"
    return "male"


def parse_birth(birth: str) -> tuple[str, str]:
    """'1964-09-20 12:00' -> ('1964-09-20', '12:00')."""
    birth = birth.strip()
    if " " in birth:
        d, t = birth.split(" ", 1)
        return d, t[:5] if len(t) >= 5 else "12:00"
    return birth, "12:00"


def renping_polarity(text: str) -> str:
    if not text:
        return "neutral"
    pos = sum(1 for k in POS_KEYWORDS if k in text)
    neg = sum(1 for k in NEG_KEYWORDS if k in text)
    if pos > neg and pos >= 1:
        return "positive"
    if neg > pos and neg >= 1:
        return "negative"
    return "neutral"


def highlights_polarity(highlights: list[str]) -> str:
    filtered = [
        h
        for h in (highlights or [])
        if not h.startswith("【四柱关系")
        and "神煞备注" not in h
        and not h.startswith("【季节气候")
    ]
    joined = " ".join(filtered)
    return renping_polarity(joined)


def polarity_aligned(renping: str, highlights: list[str]) -> bool | None:
    rp = renping_polarity(renping)
    hp = highlights_polarity(highlights)
    if rp == "neutral" or hp == "neutral":
        return None
    return rp == hp


def geju_mentioned(text: str, geju: str) -> bool:
    if not geju:
        return True
    if geju in text:
        return True
    base = geju.replace("格", "").strip()
    if base and len(base) >= 2 and base in text:
        return True
    if "化" in geju:
        for part in (geju.replace("格", ""), geju.split("化")[-1].replace("格", "")):
            if part and len(part) >= 2 and part in text:
                return True
    return False


def _strength_consistent(text: str, strength: str) -> bool:
    if not strength:
        return True
    mentions_strong = "身强" in text or "偏强" in text or "旺" in text
    mentions_weak = "身弱" in text or "偏弱" in text
    if strength in ("偏强", "身强", "强"):
        return not (mentions_weak and not mentions_strong)
    if strength in ("偏弱", "身弱", "弱"):
        return not (mentions_strong and not mentions_weak)
    return True


def score_ai_analysis(
    text: str,
    insight: dict[str, Any] | None = None,
    *,
    style: str = "modern",
) -> tuple[float, list[str]]:
    issues: list[str] = []
    score = 10.0
    if style != "classic" and any(t in text for t in ANCIENT_TERMS):
        bad = [t for t in ANCIENT_TERMS if t in text]
        issues.append(f"古代断语: {bad}")
        score -= 2
    if insight:
        strength = str(insight.get("day_master_strength") or "")
        if not _strength_consistent(text, strength):
            issues.append(f"旺衰与规则层不一致({strength})")
            score -= 2
        geju = (insight.get("geju") or {}).get("type", "")
        if geju and not geju_mentioned(text, geju):
            issues.append(f"未提及格局类型({geju})")
            score -= 0.5
    if "身强" in text and "身弱" in text:
        strength = str((insight or {}).get("day_master_strength") or "")
        msg = (
            "平衡命却同时出现身强与身弱"
            if strength in ("平衡", "中和")
            else "同时出现身强与身弱"
        )
        if msg not in issues:
            issues.append(msg)
            score -= 2
    if len(text) < 300:
        issues.append("过短")
        score -= 1
    return max(score, 0.0), issues


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
