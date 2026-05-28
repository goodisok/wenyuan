# -*- coding: utf-8 -*-
"""批量测试 — 古籍四柱命例（书中八字，非现代公历反推）"""
import sys
import json
import os
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regression_ai import load_ai_suite
from scripts.regression_common import build_chart_from_gz, gender_to_code

BASE = "http://127.0.0.1:8000"

TEST_CASES = load_ai_suite()[:10]

CHECK_TERMS = {
    "ancient": ["官至", "七品", "朱门", "武职", "发用", "纳妾", "封侯", "状元", "进士"],
    "classics": ["滴天髓", "穷通宝鉴", "三命通会", "子平真诠"],
}

output_dir = f"/tmp/wenyuan_batch_{int(time.time())}"
os.makedirs(output_dir, exist_ok=True)

results = []
for i, case in enumerate(TEST_CASES):
    name = case.get("name", case.get("id", "?"))
    gz = case["gz"]
    print(f"\n[{i + 1}/{len(TEST_CASES)}] {name} ({gz})...", flush=True)
    try:
        chart = build_chart_from_gz(
            gz,
            gender_to_code(case.get("gender", "male")),
            day_master=case.get("dm"),
        )
        pillars = {p["label"]: p["ganzhi"] for p in chart["pillars"]}
        print(f"    四柱: {' '.join(pillars.values())}", flush=True)

        r2 = httpx.post(
            f"{BASE}/api/analyze",
            json={"chart": chart, "style": "classic"},
            timeout=120,
        )
        ana = r2.json().get("analysis", "")

        out_path = os.path.join(output_dir, f"{i + 1:02d}_{case.get('id', 'case')}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n四柱：{gz}\n\n{ana}\n")

        ancient_hits = [t for t in CHECK_TERMS["ancient"] if t in ana]
        classic_hits = [t for t in CHECK_TERMS["classics"] if t in ana]
        results.append(
            {
                "name": name,
                "gz": gz,
                "len": len(ana),
                "ancient_hits": ancient_hits,
                "classic_hits": classic_hits,
                "file": out_path,
            }
        )
        print(f"  ✅ {len(ana)} chars, 典籍={classic_hits}", flush=True)
    except Exception as exc:
        print(f"  ❌ {exc}", flush=True)
        results.append({"name": name, "error": str(exc)})
    time.sleep(0.5)

summary_path = os.path.join(output_dir, "summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nDone. Output: {output_dir}")
