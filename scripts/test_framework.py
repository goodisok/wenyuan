# -*- coding: utf-8 -*-
"""
大规模测试框架 — wenyuan AI 命理分析质量测试
包含：
  1. 公众人物测试集（含已知人生结果）
  2. 自动评估指标
  3. 多轮迭代测试
"""
import sys, json, os, time, datetime
sys.path.insert(0, "/home/lcg/wenyuan")
import httpx

BASE_URL = "http://localhost:8000"

# ============================================================
# 测试集：公众人物（需已知八字和人生结果用于评估）
# ============================================================
# 格式: (name, year, month, day, hour, minute, gender, known_info, eval_hints)
TEST_CASES = [
    # 马云 - 1964年9月10日 时辰未知(默认午时)
    ("马云", 1964, 9, 10, 12, 0, "male", {
        "career": "阿里巴巴创始人，中国首富级企业家",
        "key_events": ["1999年创立阿里", "2014年阿里上市", "2019年退休"],
        "personality": "擅长演讲、战略眼光、敢想敢做",
        "notable": "教师出身，英语好，后转型企业家"
    }),
    # 马化腾 - 1971年10月29日
    ("马化腾", 1971, 10, 29, 12, 0, "male", {
        "career": "腾讯创始人，社交+游戏帝国",
        "key_events": ["1998年创立腾讯", "2004年上市", "2011年微信推出"],
        "personality": "低调内敛、产品思维、技术出身",
        "notable": "不同于马云的张扬，马化腾以沉稳著称"
    }),
    # 雷军 - 1969年12月16日
    ("雷军", 1969, 12, 16, 12, 0, "male", {
        "career": "小米创始人，金山软件董事长",
        "key_events": ["1992年加入金山", "2007年金山上市后离开", "2010年创立小米"],
        "personality": "勤奋、务实、技术背景、二次创业成功",
        "notable": "从程序员到企业家，两次敲钟"
    }),
    # 刘强东 - 1974年2月14日
    ("刘强东", 1974, 2, 14, 12, 0, "male", {
        "career": "京东创始人，自建物流体系",
        "key_events": ["1998年创立京东", "2014年京东上市", "2018年明尼苏达事件"],
        "personality": "强势、重控制、草根逆袭",
        "notable": "宿迁农村出身，人大毕业"
    }),
    # 张一鸣 - 1983年（具体日期有多种说法，这里用4月）
    ("张一鸣", 1983, 4, 1, 12, 0, "male", {
        "career": "字节跳动创始人，抖音/TikTok",
        "key_events": ["2012年创立字节", "2016年抖音上线"],
        "personality": "理性、算法思维、低调、持续创业者",
        "notable": "信息分发+算法推荐模式开创者"
    }),
    # 马斯克 - 1971年6月28日
    ("马斯克", 1971, 6, 28, 12, 0, "male", {
        "career": "特斯拉、SpaceX、xAI创始人",
        "key_events": ["2002年创立SpaceX", "2004年加入特斯拉", "2022年收购Twitter"],
        "personality": "冒险、偏执、多领域跨界的狂人",
        "notable": "南非出生，从PayPal到航天到电动车到AI"
    }),
    # 王兴 - 1979年2月18日
    ("王兴", 1979, 2, 18, 12, 0, "male", {
        "career": "美团创始人",
        "key_events": ["2005年校内网", "2010年创立美团"],
        "personality": "连续创业者、理性、战略清晰",
        "notable": "福建龙岩人，清华毕业，多次创业终成"
    }),
    # 黄峥 - 1980年（具体日期未公开，用近似值）
    ("黄峥", 1980, 11, 16, 12, 0, "male", {
        "career": "拼多多创始人",
        "key_events": ["2015年创立拼多多", "2020年超越阿里市值"],
        "personality": "低调、逆向思维、理性的实用主义者",
        "notable": "Google出身，懂技术和商业"
    }),
    # 董明珠 - 1954年8月10日（示例女性命例）
    ("董明珠", 1954, 8, 10, 12, 0, "female", {
        "career": "格力电器董事长",
        "key_events": ["1990年加入格力", "2012年任董事长"],
        "personality": "强势、铁娘子、实干、原则性强",
        "notable": "36岁丧夫后南下打工的传奇女企业家"
    }),
    # 曹德旺 - 1946年1月（具体日未公开）
    ("曹德旺", 1946, 1, 15, 12, 0, "male", {
        "career": "福耀玻璃创始人",
        "key_events": ["1987年创立福耀", "成为全球汽车玻璃巨头"],
        "personality": "实干、慈善家、朴实",
        "notable": "从承包乡镇小厂到全球玻璃大王"
    }),
    # 任正非 - 1944年10月25日
    ("任正非", 1944, 10, 25, 12, 0, "male", {
        "career": "华为创始人",
        "key_events": ["1987年创立华为", "成长为全球通信巨头"],
        "personality": "低调、狼性文化、危机意识强",
        "notable": "44岁被骗200万后被迫创业"
    }),
    # 李彦宏 - 1968年11月17日
    ("李彦宏", 1968, 11, 17, 12, 0, "male", {
        "career": "百度创始人",
        "key_events": ["2000年创立百度", "2005年上市"],
        "personality": "技术出身、海归、理性",
        "notable": "超链分析专利持有者"
    }),
]

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
