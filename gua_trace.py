#!/usr/bin/env python3
"""
木雷易术引擎 - 典籍溯源模块（手写，不被 extract_yaoci 覆盖）
按本卦名+动爻，从《六十四卦卦辞爻辞》数据里取卦辞/爻辞
"""
from yijing_yaoci import YIJING_GUACI

# 八卦爻象（下→上，1=阳0=阴）
_BAGUA_YAO = {"乾":[1,1,1],"兑":[1,1,0],"离":[1,0,1],"震":[1,0,0],
              "巽":[0,1,1],"坎":[0,1,0],"艮":[0,0,1],"坤":[0,0,0]}

# 六字全名 -> 卦序
FULL_NAME_TO_ORDER = {
    "乾为天":1,"坤为地":2,"水雷屯":3,"山水蒙":4,"水天需":5,"天水讼":6,
    "地水师":7,"水地比":8,"风天小畜":9,"天泽履":10,"地天泰":11,"天地否":12,
    "天火同人":13,"火天大有":14,"地山谦":15,"雷地豫":16,"泽雷随":17,"山风蛊":18,
    "地泽临":19,"风地观":20,"火雷噬嗑":21,"山火贲":22,"山地剥":23,"地雷复":24,
    "天雷无妄":25,"山天大畜":26,"山雷颐":27,"泽风大过":28,"坎为水":29,"离为火":30,
    "泽山咸":31,"雷风恒":32,"天山遁":33,"雷天大壮":34,"火地晋":35,"地火明夷":36,
    "风火家人":37,"火泽睽":38,"水山蹇":39,"雷水解":40,"山泽损":41,"风雷益":42,
    "泽天夬":43,"天风姤":44,"泽地萃":45,"地风升":46,"泽水困":47,"水风井":48,
    "泽火革":49,"火风鼎":50,"震为雷":51,"艮为山":52,"风山渐":53,"雷泽归妹":54,
    "雷火丰":55,"火山旅":56,"巽为风":57,"兑为泽":58,"风水涣":59,"水泽节":60,
    "风泽中孚":61,"雷山小过":62,"水火既济":63,"火水未济":64,
}

def yao_label(nei_gua, wai_gua, pos):
    """由内外卦推算第 pos 爻（1-6）的爻名（初九/六二…）"""
    tri = _BAGUA_YAO[nei_gua] + _BAGUA_YAO[wai_gua]
    if pos < 1 or pos > 6:
        return None
    yang = tri[pos-1] == 1
    name = {1:"初",2:"二",3:"三",4:"四",5:"五",6:"上"}[pos]
    y = ("九" if yang else "六")
    return (name + y) if name in ("初", "上") else (y + name)

# 后天八卦方位佐证（断方位用文王后天·洛书）
_HOUTIAN = {
    "坎":("北","北方属水，主藏拙蓄势、积蓄后再动"),
    "坤":("西南","西南属土，主包容厚德、得母性贵人助"),
    "震":("东","东方属木，主生发进取、利开新局"),
    "巽":("东南","东南属木，主入财通利、利求财与文书"),
    "乾":("西北","西北属金，主决策权威、利见贵人上司"),
    "兑":("西","西方属金，主沟通交流、利谈判结盟"),
    "艮":("东北","东北属土，主静止积蓄、宜守不宜攻"),
    "离":("南","南方属火，主名气声量、利曝光与展示"),
}

def _gua_yi(full_name):
    """卦意佐证（从断卦规则库的卦意表取）"""
    try:
        from duangua_rules import GUA_CI
        return GUA_CI.get(full_name, "")
    except Exception:
        return ""

def gua_trace(full_name, dong_yao_list, nei_gua=None, wai_gua=None):
    """按本卦名+动爻返回 卦辞/爻辞/卦意/后天方位 溯源段落"""
    order = FULL_NAME_TO_ORDER.get(full_name)
    if not order:
        return ""
    g = YIJING_GUACI.get(order, {})
    lines = [f"  典籍溯源·本卦卦辞：{g.get('guaci','')}"]
    gy = _gua_yi(full_name)
    if gy:
        lines.append(f"  典籍溯源·卦意简释：{gy}")
    yaoci = g.get('yaoci', {})
    for d in sorted(dong_yao_list):
        label = yao_label(nei_gua, wai_gua, d) if (nei_gua and wai_gua) else None
        if label and label in yaoci:
            lines.append(f"  典籍溯源·{label}爻爻辞：{yaoci[label]}")
        # 用九/用六
        if label in ("用九", "用六") or (label is None and str(d) in ("用九","用六")):
            if label in yaoci:
                lines.append(f"  典籍溯源·{label}爻辞：{yaoci[label]}")
    # 后天八卦方位佐证
    if nei_gua and nei_gua in _HOUTIAN:
        dn, dd = _HOUTIAN[nei_gua]
        lines.append(f"  后天方位佐证·{nei_gua}（{dn}）：{dd}")
    return "\n".join(lines)


def _lines_from_nei_wai(nei_gua, wai_gua):
    """由内外卦取六爻阴阳序列（下→上）"""
    return _BAGUA_YAO.get(nei_gua, [0,0,0]) + _BAGUA_YAO.get(wai_gua, [0,0,0])


def build_gua_visual(ben_name, dong_yao_list, nei_gua, wai_gua):
    """起卦可视化数据：本卦/互卦/变卦六爻序列 + 动爻 + 卦名"""
    ben = _lines_from_nei_wai(nei_gua, wai_gua)          # 6爻，下→上
    # 互卦：取本卦 2,3,4 为下互，3,4,5 为上互（按爻位1-6）
    hu_nei = [ben[1], ben[2], ben[3]]
    hu_wai = [ben[2], ben[3], ben[4]]
    hu = hu_nei + hu_wai
    # 变卦：动爻取反
    bian = list(ben)
    for d in (dong_yao_list or []):
        if 1 <= d <= 6:
            bian[d-1] = 1 - bian[d-1]
    return {
        "ben": {"name": ben_name, "lines": ben},
        "hu": {"name": "互卦", "lines": hu},
        "bian": {"name": "变卦", "lines": bian},
        "dong": sorted(dong_yao_list or []),
    }


if __name__ == "__main__":
    print(gua_trace("火雷噬嗑", [6], "震", "离"))
