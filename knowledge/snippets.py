# -*- coding: utf-8 -*-
"""典籍知识片段库（检索用，非全文）。参考 bazi-skill MIT。"""
from __future__ import annotations

SNIPPETS: list[dict[str, str | list[str]]] = [
    # 穷通宝鉴
    {"id": "qt_principle", "source": "穷通宝鉴", "tags": ["tiao_hou", "always"],
     "text": "论命首重调候，其次论格局旺衰；调候为「药」，缺失则格局难发。"},
    {"id": "qt_summer", "source": "穷通宝鉴", "tags": ["tiao_hou"],
     "text": "夏生火旺，须用水调候；冬生水旺，须用火调候。"},
    # 滴天髓
    {"id": "dts_sande", "source": "滴天髓", "tags": ["strength", "always"],
     "text": "旺衰看三得：得令、得地、得势；得令为基，通根为地，天干印比为势。"},
    {"id": "dts_tiandi", "source": "滴天髓", "tags": ["always"],
     "text": "天道看天干配合，地道看地支根基，人道看干支配合关系。"},
    {"id": "dts_liutong", "source": "滴天髓", "tags": ["wuxing", "relations", "yongshen"],
     "text": "气势宜流通；金木交战取水通关；旺极宜泄，衰极看从势。"},
    {"id": "dts_wangji", "source": "滴天髓", "tags": ["strength"],
     "text": "旺极宜泄不宜克，衰极宜扶不宜帮；从格则顺其势。"},
    # 子平真诠
    {"id": "zp_chunzhuo", "source": "子平真诠", "tags": ["pattern", "geju"],
     "text": "格局以清纯为贵，杂浊为贱；用神一位为清，多神受冲为浊。"},
    {"id": "zp_yongxiang", "source": "子平真诠", "tags": ["pattern", "geju", "yongshen", "always"],
     "text": "用神维护格局，相神辅助；成格需用神得力、相神辅佐。"},
    {"id": "zp_chengge", "source": "子平真诠", "tags": ["pattern", "geju"],
     "text": "成格：用神得力、相神辅佐、忌神有制；败格：用神受克、无相神、忌神当道。"},
    # 渊海子平
    {"id": "yh_shishen", "source": "渊海子平", "tags": ["shishen"],
     "text": "十神以日干为太极：印比帮身，食伤泄秀，财耗身，官杀制身。"},
    {"id": "yh_liuqin", "source": "渊海子平", "tags": ["shishen"],
     "text": "正印为母，偏财为父（男）；正财为妻（男），正官为夫（女）；食伤为子女（女命）。"},
    {"id": "yh_yongfa", "source": "渊海子平", "tags": ["yongshen", "strength"],
     "text": "用神取法：扶抑（弱扶强抑）、调候（寒暖燥湿）、通关（两行交战）、顺势（从格）。"},
    # 三命通会
    {"id": "sm_geju", "source": "三命通会", "tags": ["pattern", "geju", "shishen"],
     "text": "月令透干定格局：正官忌伤官破格，七杀宜食制或印化，食神忌枭夺，伤官才高忌无制见官。"},
    {"id": "sm_shensha", "source": "三命通会", "tags": ["shensha"],
     "text": "神煞为辅助，须配合格局旺衰；天乙、文昌、驿马、桃花等不可单论。"},
    {"id": "sm_tianyi", "source": "三命通会", "tags": ["shensha"],
     "text": "天乙贵人主逢凶化吉；甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，庚辛逢虎马。"},
    # 千里命稿
    {"id": "ql_gongwei", "source": "千里命稿", "tags": ["always", "dayun"],
     "text": "年柱祖上幼年，月柱父母青年，日柱自身配偶，时柱子女晚年；断事合大运流年。"},
    {"id": "ql_duanshi", "source": "千里命稿", "tags": ["dayun", "pattern"],
     "text": "先看格局高低，再看用神有力无力；大运帮扶用神、流年引动关键位置为应期。"},
    # 神峰通考
    {"id": "sf_bingyao", "source": "神峰通考", "tags": ["pattern", "dayun", "yongshen"],
     "text": "病药说：命局有「病」，大运流年见「药」方有成就；不可机械套神煞。"},
    {"id": "sf_bian", "source": "神峰通考", "tags": ["pattern"],
     "text": "格局有定法而须变通，以五行生克为根本，反对执一而论。"},
    # 协纪辨方书
    {"id": "xj_shensha", "source": "协纪辨方书", "tags": ["shensha"],
     "text": "吉神逢克则力减，凶神有制则祸轻；神煞不可单独论命。"},
    # 果老星宗
    {"id": "gl_fuzhu", "source": "果老星宗", "tags": ["optional"],
     "text": "星命与八字可互参，命宫身宫仅作辅助，非子平必需。"},
]

# 格局专条 tags: geju:正官格
GEJU_SNIPPETS: dict[str, dict[str, str | list[str]]] = {
    "正官格": {"id": "geju_zhengguan", "source": "三命通会",
               "text": "正官格主端正贵气，喜印绶护官、财星生官，忌伤官破格。"},
    "七杀格": {"id": "geju_qisha", "source": "三命通会",
               "text": "七杀格主威权果断，宜食神制杀或印星化杀，忌财星党杀。"},
    "正财格": {"id": "geju_zhengcai", "source": "渊海子平",
               "text": "正财格主勤劳持家、稳定收入，身强财旺为美，忌比劫争财。"},
    "偏财格": {"id": "geju_piancai", "source": "渊海子平",
               "text": "偏财格主机遇与人缘财，宜身强任财，忌比劫夺财。"},
    "正印格": {"id": "geju_zhengyin", "source": "子平真诠",
               "text": "正印格主聪慧学业，官印相生为贵，忌财星坏印。"},
    "偏印格": {"id": "geju_pianyin", "source": "三命通会",
               "text": "偏印格主偏门学术，忌枭神夺食，宜七杀配印。"},
    "食神格": {"id": "geju_shishen", "source": "渊海子平",
               "text": "食神格主食禄才华，宜生财泄秀，忌偏印夺食。"},
    "伤官格": {"id": "geju_shangguan", "source": "三命通会",
               "text": "伤官格主才华外露，宜财星化泄，忌无制见正官。"},
    "建禄格": {"id": "geju_jianlu", "source": "子平真诠",
               "text": "建禄格月令临官，身强宜食伤泄秀或财官任之。"},
    "羊刃格": {"id": "geju_yangren", "source": "渊海子平",
               "text": "羊刃格月令帝旺，宜官杀制刃或食伤泄，忌再逢冲刃。"},
}

# 十神专条 tags: ss:正官
SHISHEN_SNIPPETS: dict[str, dict[str, str]] = {
    "正官": "正官主贵气、规则与名誉，女命为夫星。",
    "七杀": "七杀主压力、权威与决断，宜有制化。",
    "正财": "正财主稳定收入与务实，男命为妻星。",
    "偏财": "偏财主机遇、人缘与流动财。",
    "正印": "正印主学业、庇护与母亲。",
    "偏印": "偏印主偏学、灵感与孤独。",
    "食神": "食神主才华、口福与温和表达。",
    "伤官": "伤官主创意、叛逆与表现欲。",
    "比肩": "比肩主同辈、自主与竞争。",
    "劫财": "劫财主合作与分财，亦主冲动。",
}

STEM_MONTH_NOTES: dict[tuple[str, str], tuple[str, str]] = {
    ("甲", "寅"): ("穷通宝鉴", "初春余寒，丙癸并用，以丙为先"),
    ("甲", "酉"): ("穷通宝鉴", "秋金当令，先丁制金，再丙火暖木"),
    ("庚", "子"): ("穷通宝鉴", "水冷金寒，丁丙暖局为急"),
    ("丙", "午"): ("滴天髓", "火炎土燥，宜水润土、不可过塞"),
    ("癸", "丑"): ("穷通宝鉴", "寒湿并重，丙火为先，甲木次之"),
}
