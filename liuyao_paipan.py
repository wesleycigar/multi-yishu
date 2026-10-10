#!/usr/bin/env python3
"""
木雷易术引擎 - 六爻排盘器
输入起卦信息，输出完整卦象、纳甲、六亲、世应、六神
"""
from engine_core import *

# 64卦查表: (上卦, 下卦) -> (卦名, 卦宫, 世爻位)
# 先建立查表
GUA_TABLE = {}
for gong, info in BAGONG.items():
    for i, gua_name in enumerate(info["卦"]):
        shi_yao = info["世爻"][i]
        GUA_TABLE[gua_name] = {"卦宫": gong, "世爻": shi_yao, "宫序": i}

# 八纯卦的内外卦
CHUN_GUA = {
    "乾为天": ("乾", "乾"), "坤为地": ("坤", "坤"),
    "震为雷": ("震", "震"), "巽为风": ("巽", "巽"),
    "坎为水": ("坎", "坎"), "离为火": ("离", "离"),
    "艮为山": ("艮", "艮"), "兑为泽": ("兑", "兑"),
}

def get_gua_by_name(name):
    """根据卦名返回排盘信息"""
    if name not in GUA_TABLE:
        return None
    info = GUA_TABLE[name]
    return {
        "卦名": name,
        "卦宫": info["卦宫"],
        "宫五行": BAGONG[info["卦宫"]]["五行"],
        "世爻": info["世爻"],
        "应爻": info["世爻"] + 3 if info["世爻"] <= 3 else info["世爻"] - 3,
        "宫序": info["宫序"],
    }

def najia_for_gua(nei_gua, wai_gua):
    """
    给定内卦(下卦)和外卦(上卦)，返回六爻的干支
    返回: [(爻位1, 地支, 天干), ...] 从初爻到上爻
    """
    result = []
    # 内卦(初爻到三爻)
    nei_data = NAJIA[nei_gua]
    nei_zhis = nei_data["内卦"][0]  # 如 "子寅辰"
    nei_gans = nei_data["天干"][0]  # 如 "甲甲甲"
    for i in range(3):
        result.append((i+1, nei_zhis[i], nei_gans[i]))
    # 外卦(四爻到上爻)
    wai_data = NAJIA[wai_gua]
    wai_zhis = wai_data["外卦"][0]
    wai_gans = wai_data["天干"][1]
    for i in range(3):
        result.append((i+4, wai_zhis[i], wai_gans[i]))
    return result

def paint_gua(gua_name, ri_gan="甲"):
    """完整排盘"""
    info = get_gua_by_name(gua_name)
    if not info:
        return f"未知卦名: {gua_name}"
    
    # 直接用硬编码查表获取内外卦
    nei, wai = _LOOKUP_NEI_WAI[gua_name]
    
    gua = najia_for_gua(nei, wai)
    gong_wx = info["宫五行"]
    
    lines = [
        f"{'='*50}",
        f"【{gua_name}】",
        f"卦宫: {info['卦宫']}宫 ({gong_wx})",
        f"世爻: 第{info['世爻']}爻  应爻: 第{info['应爻']}爻",
        f"{'='*50}",
        f"{'爻位':<6}{'干支':<8}{'五行':<6}{'六亲':<6}{'六神':<6}",
        f"{'-'*50}",
    ]
    
    for i, (pos, zhi, gan) in enumerate(gua):
        zhi_wx = DIZHI[zhi]["五行"]
        liuqin = get_liuqin(gong_wx, zhi_wx)
        liushen = get_liushen(ri_gan, i)
        
        # 标世应
        marker = ""
        if pos == info["世爻"]: marker += "世"
        if pos == info["应爻"]: marker += "应"
        
        lines.append(
            f"{'初二三四五上'[pos-1]+'爻':<6}"
            f"{gan+zhi:<8}"
            f"{zhi_wx:<6}"
            f"{liuqin:<6}"
            f"{liushen:<6}"
            f"{marker}"
        )
    
    return "\n".join(lines)

def infer_nei_wai(gua_name, gong, gong_idx):
    """根据卦宫和宫序推导内外卦 - 八宫卦变规则"""
    # 本宫卦：内外都是本宫卦
    if gong_idx == 0:
        return (gong, gong)
    
    # 从本宫卦开始变爻
    # 一世卦：初爻变
    # 二世卦：二爻变
    # ...
    # 五世卦：五爻变
    # 游魂卦：四爻变回本宫（四爻变）
    # 归魂卦：下卦全变回本宫
    
    # 简化：用卦画二进制来推
    # 本宫卦的卦画
    ben_gua_hua = BAGUA[gong]["卦画"]  # e.g. "111" for 乾
    
    if gong_idx <= 5:
        # 一世到五世：从下往上变
        changed = list(ben_gua_hua)
        changed[gong_idx - 1] = "0" if changed[gong_idx-1] == "1" else "1"
        # 内卦变了，外卦不变
        nei_hua = "".join(changed)
        wai_hua = ben_gua_hua
    elif gong_idx == 6:
        # 游魂卦：四爻变（外卦最下一爻）
        nei_hua = "".join([
            "0" if ben_gua_hua[i] == "1" else "1" for i in range(3)
        ])  # 内卦是五世卦的内卦
        # 实际上游魂是四爻变回本宫
        wai_changed = list(ben_gua_hua)
        wai_changed[2] = "0" if wai_changed[2] == "1" else "1"
        wai_hua = "".join(wai_changed)
        # 内卦要从五世卦推
        nei_5 = list(ben_gua_hua)
        nei_5[4] = "0" if nei_5[4] == "1" else "1"  # 不对，这思路太复杂
    
    # 这个推导逻辑太复杂了，直接用硬编码查表更可靠
    return _LOOKUP_NEI_WAI.get(gua_name, (gong, gong))

# 硬编码64卦内外卦查表（从下到上：内卦, 外卦）
_LOOKUP_NEI_WAI = {
    # 乾宫
    "乾为天": ("乾", "乾"), "天风姤": ("巽", "乾"), "天山遁": ("艮", "乾"),
    "天地否": ("坤", "乾"), "风地观": ("坤", "巽"), "山地剥": ("坤", "艮"),
    "火地晋": ("坤", "离"), "火天大有": ("乾", "离"),
    # 坎宫
    "坎为水": ("坎", "坎"), "水泽节": ("兑", "坎"), "水雷屯": ("震", "坎"),
    "水火既济": ("离", "坎"), "泽火革": ("离", "兑"), "雷火丰": ("离", "震"),
    "地火明夷": ("离", "坤"), "地水师": ("坎", "坤"),
    # 艮宫
    "艮为山": ("艮", "艮"), "山火贲": ("离", "艮"), "山天大畜": ("乾", "艮"),
    "山泽损": ("兑", "艮"), "火泽睽": ("兑", "离"), "天泽履": ("兑", "乾"),
    "风泽中孚": ("兑", "巽"), "风山渐": ("艮", "巽"),
    # 震宫
    "震为雷": ("震", "震"), "雷地豫": ("坤", "震"), "雷水解": ("坎", "震"),
    "雷风恒": ("巽", "震"), "地风升": ("巽", "坤"), "水风井": ("巽", "坎"),
    "泽风大过": ("巽", "兑"), "泽雷随": ("震", "兑"),
    # 巽宫
    "巽为风": ("巽", "巽"), "风天小畜": ("乾", "巽"), "风火家人": ("离", "巽"),
    "风雷益": ("震", "巽"), "天雷无妄": ("震", "乾"), "火雷噬嗑": ("震", "离"),
    "山雷颐": ("震", "艮"), "山风蛊": ("巽", "艮"),
    # 离宫
    "离为火": ("离", "离"), "火山旅": ("艮", "离"), "火风鼎": ("巽", "离"),
    "火水未济": ("坎", "离"), "山水蒙": ("坎", "艮"), "风水涣": ("坎", "巽"),
    "天水讼": ("坎", "乾"), "天火同人": ("离", "乾"),
    # 坤宫
    "坤为地": ("坤", "坤"), "地雷复": ("震", "坤"), "地泽临": ("兑", "坤"),
    "地天泰": ("乾", "坤"), "雷天大壮": ("乾", "震"), "泽天夬": ("乾", "兑"),
    "水天需": ("乾", "坎"), "水地比": ("坤", "坎"),
    # 兑宫
    "兑为泽": ("兑", "兑"), "泽水困": ("坎", "兑"), "泽地萃": ("坤", "兑"),
    "泽山咸": ("艮", "兑"), "水山蹇": ("艮", "坎"), "地山谦": ("艮", "坤"),
    "雷山小过": ("艮", "震"), "雷泽归妹": ("兑", "震"),
}

if __name__ == "__main__":
    # 测试几个卦
    test_guas = ["乾为天", "火天大有", "水山蹇", "泽雷随", "山水蒙"]
    for g in test_guas:
        print(paint_gua(g, "甲"))
        print()
