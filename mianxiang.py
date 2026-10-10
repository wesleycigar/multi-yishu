#!/usr/bin/env python3
"""
木雷易术引擎 - 相术模块（面相 × 八字 → 气运走势与解法）
中国传统相学三停五岳五官 + 八字日主合参：
  上停(额)主15岁前少运、中停(眉-鼻)主15-50中运、下停(颏)主50岁后晚运
  气色分 红润(运开)/黄明(吉)/青黑(滞)/苍白(弱)
输出：相面基调 → 少中晚运走势 → 当下气色 → 方位/时机解法（结合日主五行）
"""
from bazi_paipan import paipan_bazi

# 三停基调（相学口诀：额主少运、鼻主中运、颏主晚运）
_SANTING = {
    "上停": {
        "天庭开阔": ("先天福分厚", "早慧得宠，少运顺，贵人早遇", 1.0),
        "天庭平满": ("禀赋中上", "少运平顺，宜早立根基", 0.6),
        "天庭低窄": ("先天福分薄", "少运多磨，须自立发奋", -0.3),
    },
    "中停": {
        "鼻丰印明": ("中运渐起", "中年得力，贵人扶持，事业渐兴", 0.8),
        "中停平正": ("中运中平", "中年平稳，靠勤勉累积", 0.3),
        "中停塌陷": ("中运多阻", "中年奔波，防破财损业", -0.4),
    },
    "下停": {
        "地阁圆润": ("晚运丰隆", "老来有靠，子女缘分厚，善终", 0.7),
        "下停中平": ("晚运平顺", "晚年安稳，守成有余", 0.2),
        "下停尖削": ("晚运孤薄", "晚年宜早积福，修身养性", -0.3),
    },
}

_QISE = {
    "红润": ("气运正开", "面色红润主运开，宜乘势而动，把握当前窗口", 0.8),
    "黄明": ("有吉庆之象", "面色黄明为吉，利求财进业，稳中可进", 0.5),
    "青黑": ("气运暂滞", "面色青黑主气滞，宜守静待时，忌躁进", -0.6),
    "苍白": ("元气稍弱", "面色苍白主气虚，宜休养蓄力，缓图进取", -0.3),
}

# 五官细相（相学常识，各主一段运程，评分为加分/减分）
_WUGUAN = {
    "眉": {
        "眉清目秀": ("有才学，主性情温和、兄弟和", 0.4),
        "眉浓眉扬": ("性情刚直、主权威，宜收锋芒", 0.2),
        "眉疏而淡": ("兄弟缘薄，宜自立自强", -0.2),
    },
    "眼": {
        "眼神明亮": ("心正目明，贵人常助，主聪慧", 0.5),
        "眼形细长": ("谋略深、心机足，宜以诚立身", 0.2),
        "眼小神浊": ("心性易杂，宜静心修为", -0.3),
    },
    "鼻": {
        "鼻隆有肉": ("财帛丰盈，聚财之相，主41-50财运", 0.5),
        "鼻梁中正": ("守成稳进，中财之相", 0.2),
        "鼻小尖削": ("财来财去，宜勤俭节流", -0.3),
    },
    "嘴": {
        "嘴形方正": ("口福人缘佳，食禄丰", 0.3),
        "唇红齿白": ("贵显清秀之相，晚年得养", 0.4),
        "嘴角下垂": ("劳苦之相，宜多养气宽心", -0.3),
    },
    "耳": {
        "耳大有轮": ("聪明福厚，主1-14岁智慧", 0.4),
        "耳垂厚实": ("有福有寿，晚年安稳", 0.3),
        "耳薄无垂": ("劳碌之相，宜修德积福", -0.2),
    },
}


def _day_wx_from_bazi(year, month, day, hour):
    """从八字报告提取日主五行（简）"""
    try:
        rep = paipan_bazi(year, month, day, hour)
        for line in rep.split("\n"):
            if "日主:" in line or "日主" in line and "(" in line:
                import re
                m = re.search(r"\((\w)\)", line)
                if m:
                    return m.group(1)
    except Exception:
        pass
    return None

def mianxiang_analysis(year, month, day, hour, s_sang="天庭平满",
                       s_zhong="中停平正", s_xia="下停中平", qise="黄明",
                       wg_mei="眉清目秀", wg_yan="眼神明亮", wg_bi="鼻隆有肉",
                       wg_zui="嘴形方正", wg_er="耳大有轮"):
    """面相×八字 → 气运走势与解法（三停 + 五官细相 + 气色）"""
    lines = ["="*60, "👤 木雷易术引擎 · 相术·面相×八字气运", "="*60]

    # 1. 八字合参
    lines.append(f"\n📅 【八字合参】")
    day_wx = _day_wx_from_bazi(year, month, day, hour)
    try:
        rep = paipan_bazi(year, month, day, hour)
        lines.append(f"  （{rep.splitlines()[3] if len(rep.splitlines())>3 else ''}）")
    except Exception as e:
        lines.append(f"  排盘注意：{e}")
    lines.append(f"  · 日主五行：{day_wx or '待补'}")

    # 2. 相面基调（三停）
    lines.append(f"\n🧭 【相面基调·三停定气运】")
    score = 0.0
    parts = {"上停": s_sang, "中停": s_zhong, "下停": s_xia}
    for k, v in parts.items():
        if v in _SANTING[k]:
            desc, note, s = _SANTING[k][v]
            score += s
            lines.append(f"  · {k}（{v}）：{desc}——{note}")
        else:
            lines.append(f"  · {k}：未择，按中平计")

    # 3. 少/中/晚运走势（三停分主）
    lines.append(f"\n📈 【气运走势·少中晚运】")
    shang = parts["上停"]; zhong = parts["中停"]; xia = parts["下停"]
    lines.append(f"  · 少运（额相主）：{_SANTING['上停'].get(shang, ('','少运平顺',0))[1]}")
    lines.append(f"  · 中运（眉鼻主）：{_SANTING['中停'].get(zhong, ('','中运平稳',0))[1]}")
    lines.append(f"  · 晚运（颏相主）：{_SANTING['下停'].get(xia, ('','晚运平顺',0))[1]}")

    # 4. 当下气色
    qdesc, qnote, qs = _QISE.get(qise, ("", "气色平", 0))
    lines.append(f"\n🎨 【当下气色·{qise}】{qdesc}——{qnote}")

    # 4.5 五官细相
    lines.append(f"\n🔎 【五官细相】")
    wg_score = 0.0
    for part, val in (("眉", wg_mei), ("眼", wg_yan), ("鼻", wg_bi), ("嘴", wg_zui), ("耳", wg_er)):
        if val in _WUGUAN[part]:
            desc, s = _WUGUAN[part][val]
            wg_score += s
            lines.append(f"  · {part}相（{val}）：{desc}")
        else:
            lines.append(f"  · {part}相：未择，按平计")

    total = score + qs * 0.8 + wg_score * 0.6
    if total > 0.5:
        trend = "运势上行，主动进取有利"
    elif total > -0.3:
        trend = "运势中平，守正待时"
    else:
        trend = "运势偏滞，宜静养蓄力、慎作重大决定"
    lines.append(f"  · 综合气运：{trend}")

    # 5. 解法（方位/时机/改运，结合日主五行）
    lines.append(f"\n💡 【解法·改运建议】")
    from analysis_enhance import wuxing_direction
    lines += wuxing_direction(day_wx) if day_wx else []
    lines.append(f"  · 时机：红润/黄明之日乘势而动；青黑/苍白之日守静蓄力")
    lines.append(f"  · 改运：修额(积福)、养鼻(聚财)、正颏(安晚)，辅以对应五行方位活动")
    lines.append(f"  · 心性：相由心生，宽厚待人则气色自明")

    # 6. 语料/白话/溯源 增强
    try:
        from analysis_enhance import corpus_evidence, baihua, trace
        lines += corpus_evidence(f"面相 三停 气色 气运 {day_wx or ''}", k=1)
        lines += baihua("相术", f"三停定先天福分，气色断当下吉凶，{trend}。")
        lines += trace("相术", "相由心生 观其气色 定其吉凶")
    except Exception:
        pass

    lines.append(f"\n{'='*60}")
    lines.append(f"⚠️ 相术为传统观人术，仅供参考，事在人为")
    lines.append(f"{'='*60}")
    return "\n".join(lines)

if __name__ == "__main__":
    print(mianxiang_analysis(1979, 5, 15, 14, "天庭开阔", "鼻丰印明", "地阁圆润", "红润"))
