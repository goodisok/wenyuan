# -*- coding: utf-8 -*-
"""Load structured entries from goodisok/bazi-wiki markdown pages."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

WIKI_ROOT = Path(__file__).resolve().parents[1] / "bazi-wiki"
WIKI_LOAD_DIRS = ("concepts", "entities", "methods")
CASE_GLOB = "cases/case-*.md"
SKIP_NAMES = {"index.md", "README.md", "SCHEMA.md", "log.md", "CLAUDE.md"}

SOURCE_BY_TAG = {
    "di-tian": "滴天髓阐微",
    "yuan-hai": "渊海子平",
    "san-ming": "三命通会",
    "qiong-tong": "穷通宝鉴",
    "zi-ping": "子平真诠",
}

WIKI_TAG_BRIDGE: dict[str, list[str]] = {
    "ge-ju": ["geju", "pattern"],
    "shi-shen": ["shishen"],
    "da-yun": ["dayun"],
    "liu-nian": ["dayun"],
    "shen-sha": ["shensha"],
    "wang-shuai": ["strength"],
    "qiong-tong": ["tiao_hou"],
    "duan-ming": ["duanshi"],
    "si-zhu": ["always"],
    "wu-xing": ["wuxing"],
    "tian-gan-di-zhi": ["always"],
    "pai-pan": ["always"],
    "jing-dian": ["always"],
}

KIND_BY_TYPE = {
    "case": "case",
    "concept": "principle",
    "entity": "principle",
    "method": "principle",
    "summary": "principle",
}

STEMS = "甲乙丙丁戊己庚辛壬癸"
SHISHEN_NAMES = (
    "比肩", "劫财", "食神", "伤官", "偏财", "正财", "偏官", "七杀", "正官", "偏印", "枭神", "正印",
)


def wiki_available() -> bool:
    return WIKI_ROOT.is_dir() and any(WIKI_ROOT.glob("concepts/*.md"))


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    block = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            meta[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
        else:
            meta[key] = val.strip("'\"")
    return meta, body


def _clean_md(text: str) -> str:
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text)
    text = re.sub(r"\^[raw/[^\]]+\]", "", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\|[-:| ]+\|", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_section(body: str, heading: str) -> str:
    pat = rf"^##\s*{re.escape(heading)}\s*$"
    m = re.search(pat, body, flags=re.M)
    if not m:
        return ""
    rest = body[m.end() :]
    nxt = re.search(r"^##\s+", rest, flags=re.M)
    chunk = rest[: nxt.start()] if nxt else rest
    return _clean_md(chunk)


def _extract_pillars(body: str) -> str:
    stems = re.search(r"\|\s*天干\s*\|(.+)\|", body)
    branches = re.search(r"\|\s*地支\s*\|(.+)\|", body)
    if not stems or not branches:
        return ""
    sg = [c.strip() for c in stems.group(1).split("|") if c.strip()]
    bg = [c.strip() for c in branches.group(1).split("|") if c.strip()]
    if len(sg) >= 4 and len(bg) >= 4:
        return " ".join(f"{sg[i]}{bg[i]}" for i in range(4))
    return ""


def _extract_day_stem(body: str) -> str:
    m = re.search(r"\*\*日主[：:]\*\*\s*([^\s（(]+)", body)
    if not m:
        return ""
    stem = m.group(1).strip()
    return stem[0] if stem and stem[0] in STEMS else ""


def _extract_geju_hints(title: str, body: str) -> list[str]:
    hints: list[str] = []
    blob = f"{title}\n{body}"
    for pat in (
        r"([\u4e00-\u9fff]{2,8}格)",
        r"(杀印相生|伤官见官|食神制杀|官杀混杂|从[杀旺革]格|化气格|羊刃格|正官格|正印格|偏财格|正财格)",
    ):
        hints.extend(re.findall(pat, blob))
    seen: set[str] = set()
    out: list[str] = []
    for h in hints:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:3]


def _extract_shishen_tags(title: str, body: str) -> list[str]:
    blob = f"{title}\n{body}"
    tags: list[str] = []
    for name in SHISHEN_NAMES:
        if name in blob:
            norm = "七杀" if name == "偏官" else ("偏印" if name == "枭神" else name)
            tag = f"ss:{norm}"
            if tag not in tags:
                tags.append(tag)
    return tags


def _wiki_tags(meta: dict[str, Any]) -> list[str]:
    raw = meta.get("tags") or []
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for t in raw:
        t = str(t).strip().strip("[]")
        if t:
            out.append(t)
    return out


def _build_tags(meta: dict[str, Any], title: str, body: str) -> list[str]:
    tags: list[str] = []
    for wt in _wiki_tags(meta):
        tags.append(wt)
        tags.extend(WIKI_TAG_BRIDGE.get(wt, []))
    tags.extend(_extract_shishen_tags(title, body))
    stem = _extract_day_stem(body)
    if stem:
        tags.append(f"stem:{stem}")
    for g in _extract_geju_hints(title, body):
        tags.append("geju")
        tags.append("pattern")
        tags.append(f"geju:{g}")
    # dedupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _source_name(meta: dict[str, Any], wiki_tags: list[str]) -> str:
    for tag in wiki_tags:
        if tag in SOURCE_BY_TAG:
            return SOURCE_BY_TAG[tag]
    return "问元知识库"


def _compose_text(meta: dict[str, Any], title: str, body: str) -> str:
    page_type = str(meta.get("type") or "")
    if page_type == "case":
        parts = []
        pillars = _extract_pillars(body)
        if pillars:
            parts.append(f"八字：{pillars}")
        review = _extract_section(body, "任铁樵原评（主旨）") or _extract_section(body, "任铁樵原评")
        if review:
            parts.append(review)
        analysis = _extract_section(body, "格局分析") or _extract_section(body, "解读")
        if analysis:
            parts.append(analysis[:600])
        yong = _extract_section(body, "用神")
        if yong:
            parts.append(yong[:400])
        text = "\n".join(parts).strip()
    else:
        overview = _extract_section(body, "概述") or _extract_section(body, "定义")
        if overview:
            text = overview
        else:
            text = _clean_md(body)
    if not text:
        text = _clean_md(body)
    title_clean = title.strip("# ").strip()
    if title_clean and title_clean not in text[:40]:
        text = f"{title_clean}。{text}"
    return text[:1400]


def _entry_from_page(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = _parse_frontmatter(raw)
    if not body.strip():
        return None
    title = str(meta.get("title") or path.stem)
    rel = path.relative_to(WIKI_ROOT).as_posix()
    wiki_tags = _wiki_tags(meta)
    tags = _build_tags(meta, title, body)
    page_type = str(meta.get("type") or "concept")
    kind = KIND_BY_TYPE.get(page_type, "principle")
    pillars = _extract_pillars(body) if page_type == "case" else ""
    geju_hints = _extract_geju_hints(title, body)
    match: dict[str, str] = {}
    stem = _extract_day_stem(body)
    if stem:
        match["day_stem"] = stem
    if geju_hints:
        match["geju"] = geju_hints[0]
    entry: dict[str, Any] = {
        "id": f"wiki_{rel.replace('/', '_').replace('.md', '')}",
        "source": _source_name(meta, wiki_tags),
        "book": "bazi-wiki",
        "chapter": title,
        "kind": kind,
        "tags": tags,
        "text": _compose_text(meta, title, body),
    }
    if match:
        entry["match"] = match
    if geju_hints:
        entry["geju"] = geju_hints[0]
    if pillars:
        entry["pillars"] = pillars
    commentary = _extract_section(body, "大运应期")
    if commentary:
        entry["commentary"] = commentary[:300]
    conf = str(meta.get("confidence") or "")
    if conf == "high":
        entry["tags"] = list(entry["tags"]) + ["always"]
    return entry


@lru_cache(maxsize=1)
def load_wiki_entries() -> list[dict[str, Any]]:
    if not wiki_available():
        return []
    paths: list[Path] = []
    for sub in WIKI_LOAD_DIRS:
        paths.extend(sorted((WIKI_ROOT / sub).glob("*.md")))
    paths.extend(sorted(WIKI_ROOT.glob(CASE_GLOB)))
    entries: list[dict[str, Any]] = []
    for path in paths:
        if path.name in SKIP_NAMES:
            continue
        item = _entry_from_page(path)
        if item and item.get("text"):
            entries.append(item)
    return entries
