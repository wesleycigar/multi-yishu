#!/usr/bin/env python3
"""
木雷易术引擎 - 梅花易数模块
体用生克法，看气运吉凶
"""
from engine_core import *
from liuyao_paipan import _LOOKUP_NEI_WAI, GUA_TABLE

# 八卦五行
BAGUA_WUXING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八卦万物类象
BAGUA_LEIXIANG = {
    "乾": "天、君、父、金、玉、大赤、良马、老马",
    "坤": "地、母、布、釜、吝啬、均、子母牛、大舆",
    "震": "雷、龙、玄黄、旉、大涂、决躁、苍筤竹",
    "巽": "木、风、长女、绳直、工、白、长、高、进退",
    "坎": "水、沟渎、隐伏、矫輮、弓轮、赤、血卦",
    "离": "火、日、电、中女、甲胄、戈兵、大腹、乾卦",
    "艮": "山、径路、小石、门阙、果蓏、阍寺、指、狗",
    "兑": "泽、少女、巫、口舌、毁折、附决、刚卤",
}


# 八卦三爻阴阳（自下而上：初/中/上，1阳0阴）——用于推互卦
BA_GUA_YAO = {
    "乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}
_YAO_TO_GUA = {v: k for k, v in BA_GUA_YAO.items()}


def get_hugua(shang, xia):
    """梅花互卦：本卦 234爻为下互、345爻为上互。
    shang: 上卦(三爻卦名)；xia: 下卦(三爻卦名)。返回 (互卦卦名, 互上卦, 互下卦)。"""
    a, b, c = BA_GUA_YAO[xia]      # 下卦 初/二/三
    d, e, f = BA_GUA_YAO[shang]    # 上卦 四/五/上
    # 本卦六爻（初→上）= [a,b,c,d,e,f]
    hx = _YAO_TO_GUA[(b, c, d)]    # 二三四爻 → 互下卦
    hs = _YAO_TO_GUA[(c, d, e)]    # 三四五爻 → 互上卦
    for gname, (nei, wai) in _LOOKUP_NEI_WAI.items():
        if nei == hx and wai == hs:
            return gname, hs, hx
    return "未知卦", hs, hx


_HUGUA_HINT = {
    "乾": "刚健推进，过程主动", "坤": "顺势承载，过程平稳",
    "泰": "上下通泰，过程顺利", "否": "闭塞不通，过程受阻",
    "既济": "事已过半，过程接近成", "未济": "事未成，过程尚需努力",
    "谦": "以柔克刚，过程宜低调", "豫": "顺势而兴，过程较快",
    "屯": "艰难始生，过程起步难", "蒙": "蒙昧初启，过程需启蒙",
    "需": "静候时机，过程宜等待", "讼": "有争辩，过程或有口舌",
    "小畜": "小有蓄积，过程积少成多", "履": "如履薄冰，过程须谨慎",
    "大有": "盛大丰有，过程收获多", "大畜": "大有蓄积，过程厚积薄发",
    "中孚": "诚信相感，过程以诚动人", "家人": "家内之事，过程主内和",
    "同人": "和同于人，过程需合作", "归妹": "情有所归，过程主合",
    "革": "变革之象，过程有变", "鼎": "鼎新之象，过程有成",
    "大壮": "阳刚壮盛，过程力道足", "小过": "宜守常，过程有过越之虞",
    "大过": "过甚之象，过程须防过", "离": "明丽相照，过程渐明",
    "坎": "险陷波折，过程多艰", "震": "震动惊起，过程有波",
    "巽": "顺而入，过程循序渐进", "兑": "悦而合，过程和悦通畅",
    "艮": "止而不进，过程宜暂停", "益": "增益之象，过程得助",
    "损": "损减之象，过程宜舍", "咸": "感应相合，过程情通",
    "恒": "恒久之道，过程贵坚持", "渐": "渐进有序，过程循次",
    "晋": "晋升之象，过程向上", "明夷": "明入地中，过程暂晦",
    "睽": "乖离之象，过程有分歧", "蹇": "行路艰难，过程多阻",
}


def _hugua_process(name):
    # 支持"水山蹇"等全名：优先按核心卦名（末字）查表，未命中取全名
    if len(name) >= 2 and name[-1] in _HUGUA_HINT:
        return _HUGUA_HINT[name[-1]]
    return _HUGUA_HINT.get(name, "卦气中和，过程宜审时度势")


def meihua_qigua(num1, num2, hour_num=None):
    """
    梅花易数起卦
    num1: 上卦数（先天数1-8）
    num2: 下卦数（先天数1-8）
    hour_num: 时辰数（可选，用于求动爻）
    """
    XIANTIAN = {1:"乾",2:"兑",3:"离",4:"震",5:"巽",6:"坎",7:"艮",8:"坤"}
    
    shang = XIANTIAN[num1 % 8 if num1 % 8 != 0 else 8]
    xia = XIANTIAN[num2 % 8 if num2 % 8 != 0 else 8]
    
    if hour_num:
        dong = (num1 + num2 + hour_num) % 6
        if dong == 0: dong = 6
    else:
        dong = None
    
    # 找卦名
    for gua_name, (nei, wai) in _LOOKUP_NEI_WAI.items():
        if nei == xia and wai == shang:
            return gua_name, shang, xia, dong
    
    return "未知卦", shang, xia, dong


def meihua_duangua(num1, num2, hour_num, question_type="气运", personal_info=None):
    """
    梅花易数完整断卦
    核心：体卦（我） vs 用卦（事）
    personal_info: 可选，个人信息字典（八字日主、现状等）
    """
    gua_name, shang, xia, dong = meihua_qigua(num1, num2, hour_num)
    
    lines = []
    lines.append("=" * 60)
    lines.append("🌸 木雷易术引擎 · 梅花易数报告")
    lines.append("=" * 60)
    
    lines.append(f"\n📋 【起卦信息】")
    lines.append(f"  上卦：{shang}（{BAGUA_WUXING[shang]}）")
    lines.append(f"  下卦：{xia}（{BAGUA_WUXING[xia]}）")
    lines.append(f"  本卦：{gua_name}")
    if dong:
        lines.append(f"  动爻：第{dong}爻")
    
    # 分体用：有动爻的卦为用，无动爻的卦为体
    # 动爻在下卦(1-3爻) → 下卦为用、上卦为体；动爻在上卦(4-6爻) → 上卦为用、下卦为体
    if dong:
        if dong <= 3:
            ti = shang  # 上卦静为体
            yong = xia  # 下卦动为用
        else:
            ti = xia  # 下卦静为体
            yong = shang  # 上卦动为用
    else:
        ti = xia
        yong = shang
    
    ti_wx = BAGUA_WUXING[ti]
    yong_wx = BAGUA_WUXING[yong]
    
    lines.append(f"\n🎯 【体用分析】")
    lines.append(f"  体卦（我）：{ti}（{ti_wx}）")
    lines.append(f"  用卦（事）：{yong}（{yong_wx}）")
    
    # 如果有个人信息，结合八字分析
    if personal_info:
        day_master_wx = personal_info.get('日主五行', '')
        lines.append(f"\n🧑 【结合个人八字】")
        lines.append(f"  你的日主五行：{day_master_wx}")
        
        # 体卦五行与日主五行的关系
        if day_master_wx:
            if ti_wx == day_master_wx:
                lines.append(f"  ✅ 体卦五行与你日主同气，卦与你命相合，感应强")
            elif WUXING_SHENG.get(day_master_wx) == ti_wx:
                lines.append(f"  ✅ 你的生日体卦，卦受你生，事在你掌控中")
            elif WUXING_KE.get(day_master_wx) == ti_wx:
                lines.append(f"  💡 你克体卦，你能改变事情走向")
            elif WUXING_SHENG.get(ti_wx) == day_master_wx:
                lines.append(f"  ⚠️ 体卦生你，事来就你，但消耗你的精力")
            elif WUXING_KE.get(ti_wx) == day_master_wx:
                lines.append(f"  ❌ 体卦克你，事情对你有压力")
    
    # 体用生克
    lines.append(f"\n⚖️ 【体用生克】")
    score = 0
    if ti_wx == yong_wx:
        score += 2
        lines.append(f"  ✅ 体用比和（都是{ti_wx}）：事事顺利，贵人相助")
    elif WUXING_SHENG.get(ti_wx) == yong_wx:
        score += 0
        lines.append(f"  💡 体生用（{ti_wx}生{yong_wx}）：我付出多、泄气耗力，事可成但劳心，宜蓄力")
    elif WUXING_SHENG.get(yong_wx) == ti_wx:
        score += 2
        lines.append(f"  ✅ 用生体（{yong_wx}生{ti_wx}）：事来就我，大吉大利")
    elif WUXING_KE.get(ti_wx) == yong_wx:
        score += 0.5
        lines.append(f"  💡 体克用（{ti_wx}克{yong_wx}）：我能成事，但需费力")
    elif WUXING_KE.get(yong_wx) == ti_wx:
        score -= 2
        lines.append(f"  ❌ 用克体（{yong_wx}克{ti_wx}）：事来克我，凶多吉少")
    
    # 卦象类象
    lines.append(f"\n📖 【卦象类象】")
    lines.append(f"  {ti}（体）：{BAGUA_LEIXIANG[ti]}")
    lines.append(f"  {yong}（用）：{BAGUA_LEIXIANG[yong]}")
    
    # 互卦：本卦 234爻为下互、345爻为上互，主中间过程变化
    hg_name, hg_shang, hg_xia = get_hugua(shang, xia)
    lines.append(f"\n🔄 【互卦】（过程）")
    lines.append(f"  互卦：{hg_name}（上{hg_shang}{BAGUA_WUXING[hg_shang]}，下{hg_xia}{BAGUA_WUXING[hg_xia]}）")
    lines.append(f"  互卦取本卦二三四爻为下互、三四五爻为上互，主事情发展中间的过程变化")
    lines.append(f"  · 互卦{BAGUA_LEIXIANG[hg_shang]}（上）与{BAGUA_LEIXIANG[hg_xia]}（下）：中间过程多需{_hugua_process(hg_name)}")
    
    # 结论
    lines.append(f"\n{'='*60}")
    if score >= 2:
        result = "大吉"
        advice = "时机很好，大胆推进，必有收获"
    elif score >= 1:
        result = "小吉"
        advice = "事情顺利，但需自己努力"
    elif score >= 0:
        result = "平"
        advice = "平平之象，宜守不宜攻"
    elif score >= -1:
        result = "小凶"
        advice = "多阻碍，需小心谨慎"
    else:
        result = "大凶"
        advice = "大事不宜，暂缓推进"
    
    lines.append(f"🏆 【结论】{result}")
    lines.append(f"💡 【建议】{advice}")
    lines.append(f"{'='*60}")

    # D：佐证/白话/语料/溯源 增强
    try:
        from analysis_enhance import finalize
        guas = [ti, yong, shang, xia] if ti in ("乾","兑","离","震","巽","坎","艮","坤") else [shang, xia]
        lines = finalize(lines, "梅花", f"{question_type} 体用生克 {ti}{yong}",
                         gua_names=guas, brief=f"{result}，{advice}。")
    except Exception:
        pass

    return "\n".join(lines)


if __name__ == "__main__":
    print(meihua_duangua(3, 8, 6, "气运"))
