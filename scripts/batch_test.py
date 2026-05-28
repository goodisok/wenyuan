# -*- coding: utf-8 -*-
"""批量测试 - 分人执行，结果写文件"""
import sys, json, os, time, httpx
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = "http://127.0.0.1:8000"

TEST_CASES = [
    ("马云", 1964, 9, 10, "male", "阿里创始人，首富级"),
    ("马化腾", 1971, 10, 29, "male", "腾讯创始人，社交+游戏"),
    ("雷军", 1969, 12, 16, "male", "小米创始人，金山董事长"),
    ("刘强东", 1974, 2, 14, "male", "京东创始人"),
    ("马斯克", 1971, 6, 28, "male", "特斯拉/SpaceX创始人"),
    ("王兴", 1979, 2, 18, "male", "美团创始人"),
    ("董明珠", 1954, 8, 10, "female", "格力董事长"),
    ("曹德旺", 1946, 1, 15, "male", "福耀玻璃创始人"),
    ("任正非", 1944, 10, 25, "male", "华为创始人"),
    ("李彦宏", 1968, 11, 17, "male", "百度创始人"),
]

CHECK_TERMS = {
    "ancient": ["官至", "七品", "朱门", "武职", "发用", "纳妾", "封侯", "状元", "进士"],
    "classics": ["滴天髓", "穷通宝鉴", "三命通会", "子平真诠"],
}

output_dir = f"/tmp/wenyuan_batch_{int(time.time())}"
os.makedirs(output_dir, exist_ok=True)

results = []
for i, (name, y, m, d, g, info) in enumerate(TEST_CASES):
    print(f"\n[{i+1}/{len(TEST_CASES)}] {name} ({y}-{m:02d}-{d:02d})...", flush=True)
    try:
        r1 = httpx.post(f'{BASE}/api/chart', json={
            'date_type': 'solar', 'birth_date': f'{y}-{m:02d}-{d:02d}',
            'birth_time': '12:00', 'gender': g
        }, timeout=10)
        if not r1.json().get('success'):
            print(f"  ❌ 排盘失败: {r1.text[:100]}", flush=True)
            continue
        chart = r1.json()['data']
        pillars = {p['label']: p['ganzhi'] for p in chart['pillars']}
        print(f"    四柱: {' '.join(pillars.values())}", flush=True)

        r2 = httpx.post(f'{BASE}/api/analyze',
            json={'chart': chart, 'style': 'modern'}, timeout=120)
        ana = r2.json().get('analysis', '')

        # Save analysis
        with open(f'{output_dir}/{name}.md', 'w', encoding='utf-8') as f:
            f.write(ana)

        # Evaluate
        findings = {}
        findings['长度'] = len(ana)
        findings['古代断语'] = [t for t in CHECK_TERMS['ancient'] if t in ana]
        findings['经典引用'] = [t for t in CHECK_TERMS['classics'] if t in ana]
        
        score = 10
        if findings['古代断语']:
            score -= 2
            print(f"  ⚠️ 古代断语: {findings['古代断语']}", flush=True)
        if not findings['经典引用']:
            score -= 0.5
            print(f"  ⚠️ 无经典引用", flush=True)
        if len(ana) < 300:
            score -= 1
            print(f"  ⚠️ 过短", flush=True)
        if ana[:100].count('身强') + ana[:100].count('身弱') > 1:
            pass  # Check if both terms used contradictorily

        results.append({
            'name': name, 'score': score, 'length': len(ana),
            'findings': findings
        })
        marks = "⭐" * (score // 2)
        print(f"  评分: {score}/10 {marks}", flush=True)

        # Brief content check
        first_line = ana.split('\n')[0][:60]
        print(f"  标题: {first_line}", flush=True)

    except Exception as e:
        print(f"  ❌ 异常: {e}", flush=True)
    
    time.sleep(1)

# Summary
print(f"\n\n{'='*60}", flush=True)
print(f"  测试完成！{len(results)}/{len(TEST_CASES)} 人", flush=True)
print(f"{'='*60}", flush=True)

avg = sum(r['score'] for r in results) / len(results) if results else 0
print(f"  平均分: {avg:.1f}/10", flush=True)

# Issues found
all_neg = []
for r in results:
    for anc in r['findings'].get('古代断语', []):
        all_neg.append((r['name'], anc))

if all_neg:
    print(f"\n  需要修复的问题:", flush=True)
    for name, issue in all_neg:
        print(f"    ❌ {name}: {issue}", flush=True)

print(f"\n  详细报告: {output_dir}/", flush=True)

# Save summary
summary = {
    'total': len(results),
    'avg_score': avg,
    'results': results,
}
with open(f'{output_dir}/summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"  结果已保存", flush=True)
