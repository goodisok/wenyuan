# -*- coding: utf-8 -*-
"""
大规模测试框架 — 已弃用现代名人公历测试（时辰不可靠）。

请改用：
  python scripts/regression_rules.py   # 831 条古籍规则层
  python scripts/regression_ai.py      # 20 条古籍四柱 AI 回归
"""
import sys, json, os, time, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx

BASE_URL = "http://127.0.0.1:8000"

# 现代名人用例已移除；见 data/ai_regression_suite.json（古籍四柱）
TEST_CASES: list = []

# ============================================================
# 评估指标
# ============================================================
EVAL_CRITERIA = [
    "身强身弱判断正确",
    "格局判断合理",
    "用神取法有据",
    "事业财富分析符合现实",
    "性格描述准确",
    "大运分析有据",
    "现代语境映射自然",
    "无古代断语（官至七品等）",
    "经典引用准确",
    "逻辑连贯不自相矛盾",
]

def evaluate_analysis(name, analysis, known_info):
    """
    对AI分析输出做初步评估
    返回评分 (0-10) 和发现的问题
    """
    issues = []
    score = 10
    analysis_lower = analysis.lower()

    # 1. 检查是否有古代断语
    ancient_terms = ["官至七品", "朱门绣户", "武职发用",
                     "纳妾", "三妻四妾", "封侯拜相", "状元及第",
                     "进士出身", "举人功名"]
    found_ancient = [t for t in ancient_terms if t in analysis]
    if found_ancient:
        issues.append(f"古代断语: {found_ancient}")
        score -= 2

    # 2. 检查是否引用经典
    classics = ["滴天髓", "穷通宝鉴", "三命通会", "子平真诠",
                "渊海子平", "神峰通考", "千里命稿"]
    found_classics = [c for c in classics if c in analysis]
    if not found_classics:
        issues.append("未引用任何经典")
        score -= 1

    # 3. 检查现代映射相关词汇
    modern_terms = ["创业", "投资", "管理", "技术", "互联网",
                    "学历", "专业", "行业", "职场", "团队",
                    "领导力", "竞争", "合作", "产业", "企业",
                    "市场", "战略", "资本", "品牌", "上市",
                    "创新", "制造", "服务", "发展", "布局",
                    "商业", "理财", "收益", "资产", "经济",
                    "经营", "融资", "产品", "运营", "扩张"]
    found_modern = [t for t in modern_terms if t in analysis]
    if len(found_modern) < 3:
        issues.append(f"现代词汇偏少(仅{len(found_modern)}个常见词)")
        score -= 0.5  # 列表无法穷举，适当放宽惩罚

    # 4. 检查关键事件是否被提及（如果有的话）
    for event in known_info.get("key_events", []):
        event_keywords = event.split(" ")[:2]
        for kw in event_keywords:
            if len(kw) >= 2 and kw in analysis:
                break
        else:
            issues.append(f"未涉及关键事件特征: {event[:20]}")

    # 5. 检查长度
    if len(analysis) < 300:
        issues.append("分析过短")
        score -= 1
    elif len(analysis) > 5000:
        issues.append("分析过长")
        score -= 0.5

    # 6. 检查是否有明显的逻辑矛盾
    contradictions = [
        ("身强" in analysis and "身弱" in analysis),
    ]
    if any(contradictions):
        issues.append("存在逻辑矛盾")
        score -= 2

    return max(score, 0), issues, found_modern, found_classics


def test_single(name, year, month, day, hour, minute, gender, known_info):
    """测试单个命例的完整流程"""
    # Step 1: 排盘
    birth = {"date_type": "solar", "birth_date": f"{year}-{month:02d}-{day:02d}",
             "birth_time": f"{hour:02d}:{minute:02d}", "gender": gender}
    
    r1 = httpx.post(f"{BASE_URL}/api/chart", json=birth, timeout=10)
    if r1.status_code != 200 or not r1.json().get("success"):
        return {"name": name, "error": f"排盘失败: {r1.text[:200]}", "chart": None, "analysis": None}

    chart = r1.json()["data"]
    
    # Extract pillar info
    pillars = {p["label"]: p["ganzhi"] for p in chart["pillars"]}
    wx = chart.get("wuxing_stats", {})
    meta = chart.get("meta", {})
    day_master = meta.get("day_master", "?")
    
    # Step 2: AI分析
    r2 = httpx.post(f"{BASE_URL}/api/analyze",
                    json={"chart": chart, "style": "modern"}, timeout=120)
    if r2.status_code != 200:
        return {"name": name, "error": f"AI分析失败: {r2.text[:200]}", "chart": pillars, "analysis": None}
    
    result = r2.json()
    if not result.get("success"):
        return {"name": name, "error": f"AI分析错误: {result.get('error', 'unknown')}", "chart": pillars, "analysis": None}
    
    analysis = result.get("analysis", "")
    
    # Evaluate
    score, issues, modern_terms, classics = evaluate_analysis(name, analysis, known_info)
    
    return {
        "name": name,
        "pillars": f"{pillars.get('年柱','')} {pillars.get('月柱','')} {pillars.get('日柱','')} {pillars.get('时柱','')}",
        "day_master": day_master,
        "wuxing": f"木{wx.get('木',0)} 火{wx.get('火',0)} 土{wx.get('土',0)} 金{wx.get('金',0)} 水{wx.get('水',0)}",
        "analysis_len": len(analysis),
        "score": score,
        "issues": issues,
        "modern_terms": modern_terms,
        "classics": classics,
        "analysis_preview": analysis[:200],
        "has_analysis": True,
    }


def run_batch(cases_subset=None):
    """运行一批测试"""
    targets = TEST_CASES if cases_subset is None else [TEST_CASES[i] for i in cases_subset]
    results = []
    
    print(f"\n{'='*70}")
    print(f"  测试批次: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  测试数量: {len(targets)} 人")
    print(f"{'='*70}")
    
    for i, (name, y, m, d, h, mi, g, info) in enumerate(targets):
        print(f"\n[{i+1}/{len(targets)}] {name} ({y}-{m:02d}-{d:02d})...", end=" ", flush=True)
        try:
            result = test_single(name, y, m, d, h, mi, g, info)
            results.append(result)
            if result.get("error"):
                print(f"❌ {result['error'][:50]}")
            else:
                score = result["score"]
                marks = "⭐" * (score // 2) + "✨" * (score % 2)
                print(f"评分: {score}/10 {marks}")
                if result["issues"]:
                    print(f"  问题: {'; '.join(result['issues'][:3])}")
                if result.get("modern_terms"):
                    print(f"  现代词汇: {result['modern_terms'][:5]}")
                if result.get("classics"):
                    print(f"  经典引用: {result['classics']}")
        except Exception as e:
            results.append({"name": name, "error": str(e)})
            print(f"❌ Exception: {e}")
        
        # 请求间隔避免限流
        time.sleep(0.5)
    
    # 统计
    scores = [r["score"] for r in results if "score" in r]
    avg = sum(scores) / len(scores) if scores else 0
    issues_list = []
    for r in results:
        for issue in r.get("issues", []):
            issues_list.append(issue)
    
    print(f"\n\n{'='*70}")
    print(f"  批次统计")
    print(f"{'='*70}")
    print(f"  平均分: {avg:.1f}/10")
    print(f"  最高分: {max(scores) if scores else 0}")
    print(f"  最低分: {min(scores) if scores else 0}")
    if issues_list:
        from collections import Counter
        top_issues = Counter(issues_list).most_common(5)
        print(f"  常见问题:")
        for issue, count in top_issues:
            print(f"    - {issue} ({count}次)")
    
    return results, avg


if __name__ == "__main__":
    if not TEST_CASES:
        print("现代名人测试集已移除。请运行: python scripts/regression_ai.py")
        raise SystemExit(0)
    results, avg = run_batch()
    
    # 保存结果
    output = {
        "timestamp": datetime.datetime.now().isoformat(),
        "avg_score": avg,
        "results": [{k: v for k, v in r.items() if k != "analysis"} for r in results],
        "total": len(results),
    }
    
    # Also save analysis texts separately for review
    analysis_dir = f"/tmp/wenyuan_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(analysis_dir, exist_ok=True)
    
    with open(f"{analysis_dir}/summary.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    for r in results:
        if r.get("has_analysis"):
            with open(f"{analysis_dir}/{r['name']}.md", "w", encoding="utf-8") as f:
                f.write(r.get("analysis", "N/A"))
    
    print(f"\n\n✅ 结果保存到: {analysis_dir}/")
    print(f"   分析文本保存到: {analysis_dir}/[name].md")
