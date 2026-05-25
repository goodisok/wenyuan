"""Verify live demo at http://119.91.54.153/"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://119.91.54.153"
TMP = Path(__file__).resolve().parents[1]


def fetch(url: str, *, method: str = "GET", data: bytes | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def check_html(name: str, text: str, markers: list[str], forbidden: list[str] | None = None) -> bool:
    forbidden = forbidden or []
    missing = [m for m in markers if m not in text]
    bad = [m for m in forbidden if m in text]
    ok = not missing and not bad
    status = "PASS" if ok else "FAIL"
    print(f"  {name}: {status}")
    if missing:
        print(f"    missing: {missing}")
    if bad:
        print(f"    forbidden: {bad}")
    return ok


def main() -> int:
    results: list[bool] = []

    print("== Health ==")
    code, body = fetch(f"{BASE}/health")
    health = json.loads(body)
    ok = code == 200 and health.get("status") == "ok" and health.get("version") == "1.8.3"
    print(f"  /health: {'PASS' if ok else 'FAIL'} -> {body.strip()}")
    results.append(ok)

    print("\n== Pages ==")
    pages = {
        "/": (
            TMP / "_tmp_home.html",
            ["page-home", 'class="hero"', "feature-card", "form-card", "开始排盘", "site-nav-link", "Wenyuan.initIndexPage", "birth_year", "theme.css?v=1.8.3"],
            ["btn-analyze-classic", "btn-analyze-modern", "古典解读", "现代解读"],
        ),
        "/chart": (
            TMP / "_tmp_chart.html",
            ["page-chart", "chart-skeleton", "chart-root", "Wenyuan.initChartPage", "子平直断"],
            ["btn-analyze-classic"],
        ),
        "/privacy": (
            TMP / "_tmp_privacy.html",
            ["page-legal", "隐私", "不持久化", "site-nav-link"],
            [],
        ),
    }
    for path, (file_path, markers, forbidden) in pages.items():
        code, html = fetch(f"{BASE}{path}")
        file_path.write_text(html, encoding="utf-8")
        page_ok = code == 200 and check_html(path, html, markers, forbidden)
        results.append(page_ok)

    print("\n== Static assets ==")
    for asset in ["/static/css/theme.css", "/static/js/app.js", "/static/sw.js"]:
        url = f"{BASE}{asset}"
        try:
            code, _ = fetch(url)
            asset_ok = code == 200
            print(f"  {asset}: {'PASS' if asset_ok else 'FAIL'} ({code})")
            results.append(asset_ok)
        except urllib.error.HTTPError as e:
            print(f"  {asset}: FAIL ({e.code})")
            results.append(False)

    print("\n== JS bundle markers ==")
    _, js = fetch(f"{BASE}/static/js/app.js")
    js_checks = [
        ("chart-topbar", "chart-topbar" in js),
        ("single analyze btn", "btn-analyze" in js and "btn-analyze-classic" not in js),
        ("子平直断 badge", "子平直断" in js),
        ("no motion typo", "</motion>" not in js and "<motion " not in js),
    ]
    for label, ok in js_checks:
        print(f"  {label}: {'PASS' if ok else 'FAIL'}")
        results.append(ok)

    _, sw = fetch(f"{BASE}/static/sw.js")
    sw_ok = "wenyuan-v4" in sw
    print(f"  SW cache v4: {'PASS' if sw_ok else 'FAIL'}")
    results.append(sw_ok)

    _, css = fetch(f"{BASE}/static/css/theme.css")
    css_checks = [
        ("hero styles", ".hero-title" in css),
        ("chart-topbar", ".chart-topbar" in css),
        ("section-card", ".section-card" in css),
    ]
    for label, ok in css_checks:
        print(f"  CSS {label}: {'PASS' if ok else 'FAIL'}")
        results.append(ok)

    print("\n== API /api/chart ==")
    payload = json.dumps(
        {
            "date_type": "solar",
            "birth_date": "1993-12-09",
            "birth_time": "18:00",
            "gender": "male",
            "is_leap_month": False,
        }
    ).encode("utf-8")
    code, body = fetch(f"{BASE}/api/chart", method="POST", data=payload)
    api_ok = code == 200
    if api_ok:
        data = json.loads(body)
        api_ok = data.get("success") is True
        pillars = [p["ganzhi"] for p in data["data"]["pillars"]]
        insight = data["data"].get("insight", {})
        gates = insight.get("sanguan", {}).get("gates", [])
        parent = next((g for g in gates if g.get("id") == "parents"), None)
        print(f"  status: PASS pillars={pillars}")
        if parent:
            verdict = parent.get("verdict", "")
            print(f"  parents gate: {parent.get('confidence')} — {verdict[:50]}")
            api_ok = api_ok and parent.get("confidence") == "高"
        else:
            print("  parents gate: FAIL (missing)")
            api_ok = False
        api_ok = api_ok and bool(insight.get("duanshi")) and bool(insight.get("sanguan"))
    else:
        print(f"  status: FAIL ({code})")
    results.append(api_ok)

    passed = sum(results)
    total = len(results)
    print(f"\n== Summary: {passed}/{total} checks passed ==")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
