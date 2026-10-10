#!/usr/bin/env python3
"""
木雷易术引擎 - 统一分析增强（D）
给梅花/奇门/风水模块输出追加：
  1) 后天八卦方位佐证（结合先天/后天两套体系）
  2) 当代白话解读
  3) 语料佐证（向量检索相关卦例口诀）
  4) 典籍溯源
"""
from engine_core import BAGUA  # 含先天数/后天数/方位/五行

# 后天八卦方位文案
HOUTIAN_DIR = {
    "坎":("北","北方属水，主智慧、藏拙养晦、积蓄力量"),
    "坤":("西南","西南属土，主包容厚德、得母性贵人助"),
    "震":("东","东方属木，主生发行动、利开拓进取"),
    "巽":("东南","东南属木，主入财通利、利求财升学"),
    "乾":("西北","西北属金，主决策权威、利见大人上司"),
    "兑":("西","西方属金，主口舌交流、利沟通谈判"),
    "艮":("东北","东北属土，主静止积蓄、宜守不宜攻"),
    "离":("南","南方属火，主名气声量、利曝光展示"),
}

def houtian_evidence(gua_names):
    """后天八卦方位佐证段（先天取象起卦 + 后天方位定吉凶方位）"""
    lines = [f"\n🧭 【后天八卦方位佐证】"]
    lines.append(f"  （起卦用先天数取象，断方位用后天八卦·洛书数）")
    seen = []
    for g in gua_names:
        if g in HOUTIAN_DIR and g not in seen:
            dir_name, desc = HOUTIAN_DIR[g]
            seen.append(g)
            lines.append(f"  • {g}（后天位{dir_name}）：{desc}")
    if not seen:
        return []
    lines.append(f"  行事可优先利用上述有利方位，避开克卦方位。")
    return lines

# 五行喜用方位（八字用，后天八卦方位映射到五行）
_WX_DIR = {
    "木": ("东、东南", "主生发，利开拓进取、文书求学"),
    "火": ("南", "主声名，利曝光展示、求名"),
    "土": ("东北、西南", "主稳定，利置业、求稳守成"),
    "金": ("西、西北", "主决断，利贵人上司、求财"),
    "水": ("北", "主智，利藏拙蓄势、求稳"),
}

def wuxing_direction(day_wx):
    """按日主五行给出宜/忌方位佐证"""
    if day_wx not in _WX_DIR:
        return []
    good, desc = _WX_DIR[day_wx]
    ke = {"木":"金","火":"水","土":"木","金":"火","水":"土"}[day_wx]
    return [
        f"\n🧭 【方位佐证】（按日主五行）",
        f"  日主{day_wx}：宜{good}方位行事（{desc}）",
        f"  忌冲克：避开{ke}行方位，防耗损受阻。",
    ]

def corpus_evidence(query, k=2):
    """语料佐证：检索典籍正文 + 文本集 相关原文"""
    out = []
    for lib_name, fn in [("典籍正文", _vlib_search), ("卦例文本", _tlib_search)]:
        try:
            res = fn(query, k)
        except Exception:
            continue
        for r in res:
            out.append(f"  · 〔{lib_name}〕{r['text'][:90]}")
    return [f"\n📚 【语料佐证】"] + out if out else []

def _vlib_search(query, k):
    from vector_library import enhance
    return enhance(query, k=k)

def _tlib_search(query, k):
    from text_corpus_lib import search_corpus
    return search_corpus(query, k=k)

def baihua(kind, brief):
    """当代白话解读"""
    s = brief.strip()
    return [
        f"\n🗣️ 【当代白话解读】",
        f"  用大白话讲：{s}" if s else "  用大白话讲：结合上面卦象与佐证，可见事情整体走势与注意要点。",
        f"  一句话提醒：术数为参考，事在人为，抓住有利时机、避开不利方位，结果在自己手中。",
    ]

def trace(kind, query):
    """典籍溯源段"""
    return [
        f"\n📜 【典籍溯源】",
        f"  本结论依据：{trace_src(kind)} 中「{query}」相关法则推演，可回溯原书。",
    ]

def trace_src(kind):
    return {
        "梅花": "邵雍《梅花易数》体用生克篇",
        "奇门": "《奇门遁甲秘笈大全》/《遁甲演义》",
        "风水": "《黄帝宅经》《八宅明镜》",
        "六爻": "《增删卜易》《卜筮正宗》",
    }.get(kind, "相关术数典籍")

def finalize(lines, kind, query, gua_names=None, brief=""):
    """统一追加 佐证/白话/语料/溯源 四段，返回完整lines"""
    if gua_names:
        lines += houtian_evidence(gua_names)
    lines += corpus_evidence(query)
    lines += baihua(kind, brief)
    lines += trace(kind, query)
    return lines
