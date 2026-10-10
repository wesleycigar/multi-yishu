#!/usr/bin/env python3
"""
木雷易术引擎 - 高级断卦规则
在基础规则之上，加：伏神、飞伏、反吟伏吟、归魂游魂
"""
from liuyao_engine import *
from liuyao_paipan import _LOOKUP_NEI_WAI, get_gua_by_name, najia_for_gua
from engine_core import DIZHI, WUXING_SHENG, WUXING_KE, get_liuqin


# ========== 伏神规则 ==========
# 当用神不上卦时，需要找伏神（从本宫首卦借来）
def get_fu_shen(ben_gua_name, yongshen_liuqin):
    """
    找伏神：如果用神六亲在卦中不上卦，从本宫首卦找
    返回: (伏神位置, 伏神六亲, 伏神干支, 飞神六亲, 飞神干支)
    """
    info = get_gua_by_name(ben_gua_name)
    gong = info["卦宫"]
    gong_wx = info["宫五行"]
    
    # 本宫首卦（八纯卦）
    BAGONG_GUA = {
        "乾": "乾为天", "坎": "坎为水", "艮": "艮为山", "震": "震为雷",
        "巽": "巽为风", "离": "离为火", "坤": "坤为地", "兑": "兑为泽",
    }
    shou_gua = BAGONG_GUA[gong]
    
    # 本卦的六亲分布
    nei, wai = _LOOKUP_NEI_WAI[ben_gua_name]
    ben_gua = najia_for_gua(nei, wai)
    
    has_yongshen = False
    for pos, zhi, gan in ben_gua:
        zhi_wx = DIZHI[zhi]["五行"]
        lq = get_liuqin(gong_wx, zhi_wx)
        if lq == yongshen_liuqin:
            has_yongshen = True
            break
    
    if has_yongshen:
        return None  # 用神上卦，不需要伏神
    
    # 从本宫首卦找伏神
    shou_nei, shou_wai = _LOOKUP_NEI_WAI[shou_gua]
    shou_gua_data = najia_for_gua(shou_nei, shou_wai)
    
    for pos, zhi, gan in shou_gua_data:
        zhi_wx = DIZHI[zhi]["五行"]
        lq = get_liuqin(gong_wx, zhi_wx)
        if lq == yongshen_liuqin:
            # 找到了伏神，对应本卦同位置的爻就是飞神
            fei_zhi, fei_gan = ben_gua[pos-1][1], ben_gua[pos-1][2]
            fei_wx = DIZHI[fei_zhi]["五行"]
            fei_lq = get_liuqin(gong_wx, fei_wx)
            
            return {
                "fu_pos": pos,
                "fu_ganzhi": f"{gan}{zhi}",
                "fu_liuqin": lq,
                "fei_ganzhi": f"{fei_gan}{fei_zhi}",
                "fei_liuqin": fei_lq,
            }
    
    return None


# ========== 反吟伏吟规则 ==========
# 反吟：卦变时爻支相冲
# 伏吟：卦变时爻支相同
FANYIN_CHECK = {
    "子": "午", "午": "子", "丑": "未", "未": "丑",
    "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}


def check_fanyin_fuyin(ben_gua_name, dong_yao_list):
    """
    检查是否有反吟或伏吟
    返回: (类型, 说明)
    """
    if not dong_yao_list:
        return "无", "静卦无反吟伏吟"
    
    bian = bian_gua(ben_gua_name, dong_yao_list)
    
    # 取本卦和变卦的爻支
    nei, wai = _LOOKUP_NEI_WAI[ben_gua_name]
    ben_yao = najia_for_gua(nei, wai)
    
    bian_nei, bian_wai = _LOOKUP_NEI_WAI[bian]
    bian_yao = najia_for_gua(bian_nei, bian_wai)
    
    fanyin_count = 0
    fuyin_count = 0
    
    for pos in dong_yao_list:
        ben_zhi = ben_yao[pos-1][1]
        bian_zhi = bian_yao[pos-1][1]
        
        if FANYIN_CHECK.get(ben_zhi) == bian_zhi:
            fanyin_count += 1
        elif ben_zhi == bian_zhi:
            fuyin_count += 1
    
    if fanyin_count > 0:
        return "反吟", f"有{fanyin_count}爻反吟，主事有反复、动荡不安"
    elif fuyin_count > 0:
        return "伏吟", f"有{fuyin_count}爻伏吟，主事有拖延、呻吟不顺"
    else:
        return "无", "无反吟伏吟"


# ========== 归魂游魂卦 ==========
GUI_YOU_HUN = {
    "归魂卦": "事有归象，但主犹豫、反复、不动",
    "游魂卦": "事有游象，主变动、不安、外出",
}


def check_gui_you_hun(ben_gua_name):
    """检查是否是归魂卦或游魂卦"""
    info = get_gua_by_name(ben_gua_name)
    # 简化：按卦宫位置判断（第三爻归魂？不对，应该看卦名）
    # 八宫卦序列：一世、二世、三世、四世、五世、游魂、归魂
    GUI_HUN = ["泽天夬", "水地比", "山风蛊", "雷山小过", "风泽中孚", "火水未济", "地泽临", "雷归妹"]
    YOU_HUN = ["火天大有", "水地比", "火山旅", "雷山小过", "风雷益", "水火既济", "地天泰", "泽风大过"]
    
    if ben_gua_name in GUI_HUN:
        return "归魂卦", GUI_YOU_HUN["归魂卦"]
    elif ben_gua_name in YOU_HUN:
        return "游魂卦", GUI_YOU_HUN["游魂卦"]
    else:
        return "普通卦", ""


# ========== 高级断卦整合 ==========
def advanced_duangua(ben_gua_name, dong_yao_list, ri_gan, ri_zhi, yue_zhi, question_type):
    """
    完整断卦 + 高级规则（伏神、反吟伏吟、归魂游魂）
    """
    lines = []
    
    # 先跑基础断卦
    from duangua_rules import full_duangua
    basic_report = full_duangua(ben_gua_name, dong_yao_list, ri_gan, ri_zhi, yue_zhi, question_type)
    
    lines.append(basic_report)
    lines.append("")
    
    # 加高级规则
    lines.append("=" * 60)
    lines.append("【高级规则分析】")
    lines.append("=" * 60)
    
    # 1. 伏神
    yongshen_lq = select_yongshen(question_type)
    fu = get_fu_shen(ben_gua_name, yongshen_lq)
    if fu:
        lines.append(f"\n【伏神】用神不上卦，寻得伏神：")
        lines.append(f"  伏神: 第{'初二三四五上'[fu['fu_pos']-1]}爻 {fu['fu_ganzhi']} ({fu['fu_liuqin']})")
        lines.append(f"  飞神: 同位置 {fu['fei_ganzhi']} ({fu['fei_liuqin']})")
        lines.append(f"  说明: 用神伏藏，事尚未显现，待出伏之日方应")
    else:
        lines.append(f"\n【伏神】用神上卦，无需伏神")
    
    # 2. 反吟伏吟
    fy_type, fy_note = check_fanyin_fuyin(ben_gua_name, dong_yao_list)
    lines.append(f"\n【反吟伏吟】{fy_type}")
    lines.append(f"  {fy_note}")
    
    # 3. 归魂游魂
    gy_type, gy_note = check_gui_you_hun(ben_gua_name)
    lines.append(f"\n【卦性】{gy_type}")
    if gy_note:
        lines.append(f"  {gy_note}")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    print(advanced_duangua(
        "火天大有",
        [3],
        "甲",
        "子",
        "卯",
        "财运"
    ))
