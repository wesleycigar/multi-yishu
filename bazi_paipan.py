#!/usr/bin/env python3
"""
木雷易术引擎 - 八字排盘模块
基于 lunar-python 计算四柱，接入十神/格局/旺衰分析
"""
from lunar_python import Solar, Lunar
from engine_core import TIANGAN, DIZHI, WUXING_SHENG, WUXING_KE, get_shishen


def analyze_strength_xiyong(bazi, day_gan):
    """综合判定日主旺衰（月令得令 + 地支通根 + 天干印比）并定喜用神。
    bazi: lunar-python 的 EightChar 对象；day_gan: 日主天干。"""
    day_wx = TIANGAN[day_gan]["五行"]
    score = 0.0
    reasons = []
    # 1. 月令得令（以月支藏干本气论）
    month_zhi = bazi.getMonth()[1]
    month_hide = bazi.getMonthHideGan() or []
    if month_hide:
        qi_wx = TIANGAN[month_hide[0]]["五行"]
        if qi_wx == day_wx:
            score += 3; reasons.append(f"月令{month_zhi}本气{month_hide[0]}与日主同五行，得令当权 (+3)")
        elif WUXING_SHENG.get(qi_wx) == day_wx:
            score += 2; reasons.append(f"月令{qi_wx}生日主{day_wx}，得令得生 (+2)")
        elif WUXING_KE.get(qi_wx) == day_wx:
            score -= 2; reasons.append(f"月令{qi_wx}克日主{day_wx}，失令受克 (-2)")
        else:
            score += 0.5; reasons.append(f"月令{qi_wx}与日主{day_wx}非生克，中和计")
    else:
        score += 1; reasons.append("月令藏干未取，暂按平计")
    # 2. 地支通根（四柱本气同五行之数）
    root_n = 0
    for hide in (bazi.getYearHideGan(), bazi.getMonthHideGan(),
                 bazi.getDayHideGan(), bazi.getTimeHideGan()):
        if hide and TIANGAN[hide[0]]["五行"] == day_wx:
            root_n += 1
    score += root_n * 1.0
    reasons.append(f"地支本气通根 {root_n} 处（禄刃库根）")
    # 3. 天干印比生扶
    assist = 0
    for gz in (bazi.getYear(), bazi.getMonth(), bazi.getTime()):
        gw = TIANGAN[gz[0]]["五行"]
        if gw == day_wx or WUXING_SHENG.get(gw) == day_wx:
            assist += 1
    score += assist * 0.5
    reasons.append(f"天干印比生扶 {assist} 个（比劫+印）")
    # 4. 强弱判定
    if score >= 4: strength = "身强"
    elif score >= 2: strength = "偏强"
    elif score >= -1: strength = "中和"
    elif score >= -3: strength = "偏弱"
    else: strength = "身弱"
    # 5. 喜用神（按日主五行动态取）
    sheng_me = {v: k for k, v in WUXING_SHENG.items()}.get(day_wx)  # 生我=印
    wo_sheng = WUXING_SHENG.get(day_wx)                             # 我生=食伤
    wo_ke = WUXING_KE.get(day_wx)                                   # 我克=财
    ke_me = {v: k for k, v in WUXING_KE.items()}.get(day_wx)        # 克我=官杀
    if strength in ("身强", "偏强"):
        xiyong = (f"喜用神：{wo_ke}(财)、{ke_me}(官杀)、{wo_sheng}(食伤) "
                  f"——身强宜克泄耗，忌再补{day_wx}、{sheng_me}比印")
    elif strength in ("身弱", "偏弱"):
        xiyong = (f"喜用神：{sheng_me}(印)、{day_wx}(比劫) "
                  f"——身弱宜生扶助身，忌{wo_ke}(财)、{ke_me}(官杀)再泄克")
    else:
        xiyong = f"中和之命，喜用随大运流年扶抑取用，忌过旺过弱；日主{day_wx}，扶抑以印比、财官相济"
    return strength, score, reasons, xiyong, day_wx

def paipan_bazi(year, month, day, hour, gender="男"):
    """
    八字排盘
    year, month, day, hour: 公历时间
    gender: 男/女
    """
    solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()
    
    # 四柱
    year_gz = bazi.getYear()    # 如 "甲子"
    month_gz = bazi.getMonth()
    day_gz = bazi.getDay()
    time_gz = bazi.getTime()
    
    # 日主
    day_gan = day_gz[0]
    day_zhi = day_gz[1]
    
    lines = [
        f"{'='*60}",
        f"木雷易术引擎 - 八字排盘",
        f"{'='*60}",
        f"公历: {year}-{month:02d}-{day:02d} {hour:02d}时  性别: {gender}",
        f"农历: {lunar.toString()}",
        f"",
        f"        年柱    月柱    日柱    时柱",
        f"天干:   {year_gz[0]}      {month_gz[0]}      {day_gz[0]}(日主)  {time_gz[0]}",
        f"地支:   {year_gz[1]}      {month_gz[1]}      {day_gz[1]}      {time_gz[1]}",
    ]
    
    # 十神
    lines.append(f"\n【十神】")
    pillars = [("年", year_gz), ("月", month_gz), ("日", day_gz), ("时", time_gz)]
    for name, gz in pillars:
        if name == "日":
            lines.append(f"  {name}柱: {gz} (日主)")
        else:
            shi = get_shishen(day_gan, gz[0])
            lines.append(f"  {name}柱: {gz[0]} = {shi}")
    
    # 地支藏干
    lines.append(f"\n【地支藏干十神】")
    # lunar-python 的藏干
    year_hidden = bazi.getYearHideGan()
    month_hidden = bazi.getMonthHideGan()
    day_hidden = bazi.getDayHideGan()
    time_hidden = bazi.getTimeHideGan()
    
    for name, hidden in [("年", year_hidden), ("月", month_hidden), ("日", day_hidden), ("时", time_hidden)]:
        shi_list = [get_shishen(day_gan, g) for g in hidden]
        lines.append(f"  {name}支藏干: {list(zip(hidden, shi_list))}")
    
    # 日主旺衰初步判断
    day_wx = TIANGAN[day_gan]["五行"]
    month_zhi = month_gz[1]
    month_wx = DIZHI[month_zhi]["五行"]
    
    wangshuai = ""
    if month_wx == day_wx:
        wangshuai = "得令(月令同气) - 偏旺"
    elif WUXING_SHENG.get(month_wx) == day_wx:
        wangshuai = "得令(月令生日主) - 相"
    elif WUXING_KE.get(month_wx) == day_wx:
        wangshuai = "失令(月令克日主) - 弱"
    elif WUXING_SHENG.get(day_wx) == month_wx:
        wangshuai = "失令(日主生月令) - 休"
    else:
        wangshuai = "失令(日主克月令) - 囚"
    
    lines.append(f"\n【日主旺衰初步】")
    lines.append(f"  日主: {day_gan}({day_wx})")
    lines.append(f"  月令: {month_zhi}({month_wx})")
    lines.append(f"  判断: {wangshuai}")
    
    # 大运
    lines.append(f"\n【大运】(从月柱起)")
    yun = bazi.getYun(gender)
    da_yun = yun.getDaYun()[:8]  # 前8步大运
    for i, dy in enumerate(da_yun):
        if dy.getStartYear() > 0:
            lines.append(f"  {dy.getStartAge()}岁起运: {dy.getGanZhi()} ({dy.getStartYear()}-{dy.getEndYear()}年)")

    # 日主强弱综合判定 + 喜用神
    lines.append(f"\n【日主强弱与喜用神】")
    strength, score, reasons, xiyong, day_wx2 = analyze_strength_xiyong(bazi, day_gan)
    for rn in reasons:
        lines.append(f"  • {rn}")
    lines.append(f"  强弱评分：{score:+.1f} → 判定【{strength}】")
    lines.append(f"  🌟 喜用神取向：{xiyong}")

    # G：方位/语料/白话/溯源 增强
    try:
        from analysis_enhance import wuxing_direction, corpus_evidence, baihua, trace
        lines += wuxing_direction(day_wx)
        lines += corpus_evidence(f"八字 命理 日主旺衰 {day_wx}", k=1)
        lines += baihua("八字", f"日主{day_gan}({day_wx})，月令{month_zhi}({month_wx})，{wangshuai}。")
        lines += trace("八字", "日主旺衰 用神")
    except Exception:
        pass

    return "\n".join(lines)


if __name__ == "__main__":
    # 测试：1990年5月15日 14时 男
    print(paipan_bazi(1990, 5, 15, 14, "男"))
    print("\n")
    # 测试：2000年1月1日 8时 女
    print(paipan_bazi(2000, 1, 1, 8, "女"))
