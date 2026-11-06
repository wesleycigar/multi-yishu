# -*- coding: utf-8 -*-
"""
卦象编码层 hex_codec
====================
把六十四卦映射为 6bit 状态空间，并提供 错/综/互/变 对称算子。

设计依据（象数重构 V2 / L0-L1 层）：
- 阳爻=1，阴爻=0；3 爻 → 2^3=8 卦；6 爻 → 2^6=64 卦
- 先天（伏羲/邵雍）卦序与 0~63 的二进制枚举同构
- 爻位自下而上：b0=初爻 …… b5=上爻
- 六爻编码 = 下卦 3bit | 上卦 3bit << 3

本模块只做“符号结构与编码”，不参与吉凶判断。
"""

# ========== 一、八卦三比特 ==========
# 卦画自下而上：乾111 兑110 离101 震100 巽011 坎010 艮001 坤000
TRIGRAMS = {
    "乾": 0b111, "兑": 0b011, "离": 0b101, "震": 0b001,
    "巽": 0b110, "坎": 0b010, "艮": 0b100, "坤": 0b000,
}
TRIGRAM_NAMES = {v: k for k, v in TRIGRAMS.items()}
TRIGRAM_NATURE = {
    "乾": "天", "兑": "泽", "离": "火", "震": "雷",
    "巽": "风", "坎": "水", "艮": "山", "坤": "地",
}
TRIGRAM_WUXING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# ========== 二、六十四卦（文王序 1-64） ==========
# (序, 卦名, 上卦, 下卦)
HEXAGRAMS = [
    (1,  "乾为天",   "乾", "乾"),
    (2,  "坤为地",   "坤", "坤"),
    (3,  "水雷屯",   "坎", "震"),
    (4,  "山水蒙",   "艮", "坎"),
    (5,  "水天需",   "坎", "乾"),
    (6,  "天水讼",   "乾", "坎"),
    (7,  "地水师",   "坤", "坎"),
    (8,  "水地比",   "坎", "坤"),
    (9,  "风天小畜", "巽", "乾"),
    (10, "天泽履",   "乾", "兑"),
    (11, "地天泰",   "坤", "乾"),
    (12, "天地否",   "乾", "坤"),
    (13, "天火同人", "乾", "离"),
    (14, "火天大有", "离", "乾"),
    (15, "地山谦",   "坤", "艮"),
    (16, "雷地豫",   "震", "坤"),
    (17, "泽雷随",   "兑", "震"),
    (18, "山风蛊",   "艮", "巽"),
    (19, "地泽临",   "坤", "兑"),
    (20, "风地观",   "巽", "坤"),
    (21, "火雷噬嗑", "离", "震"),
    (22, "山火贲",   "艮", "离"),
    (23, "山地剥",   "艮", "坤"),
    (24, "地雷复",   "坤", "震"),
    (25, "天雷无妄", "乾", "震"),
    (26, "山天大畜", "艮", "乾"),
    (27, "山雷颐",   "艮", "震"),
    (28, "泽风大过", "兑", "巽"),
    (29, "坎为水",   "坎", "坎"),
    (30, "离为火",   "离", "离"),
    (31, "泽山咸",   "兑", "艮"),
    (32, "雷风恒",   "震", "巽"),
    (33, "天山遁",   "乾", "艮"),
    (34, "雷天大壮", "震", "乾"),
    (35, "火地晋",   "离", "坤"),
    (36, "地火明夷", "坤", "离"),
    (37, "风火家人", "巽", "离"),
    (38, "火泽睽",   "离", "兑"),
    (39, "水山蹇",   "坎", "艮"),
    (40, "雷水解",   "震", "坎"),
    (41, "山泽损",   "艮", "兑"),
    (42, "风雷益",   "巽", "震"),
    (43, "泽天夬",   "兑", "乾"),
    (44, "天风姤",   "乾", "巽"),
    (45, "泽地萃",   "兑", "坤"),
    (46, "地风升",   "坤", "巽"),
    (47, "泽水困",   "兑", "坎"),
    (48, "水风井",   "坎", "巽"),
    (49, "泽火革",   "兑", "离"),
    (50, "火风鼎",   "离", "巽"),
    (51, "震为雷",   "震", "震"),
    (52, "艮为山",   "艮", "艮"),
    (53, "风山渐",   "巽", "艮"),
    (54, "雷泽归妹", "震", "兑"),
    (55, "雷火丰",   "震", "离"),
    (56, "火山旅",   "离", "艮"),
    (57, "巽为风",   "巽", "巽"),
    (58, "兑为泽",   "兑", "兑"),
    (59, "风水涣",   "巽", "坎"),
    (60, "水泽节",   "坎", "兑"),
    (61, "风泽中孚", "巽", "兑"),
    (62,  "雷山小过", "震", "艮"),
    (63, "水火既济", "坎", "离"),
    (64, "火水未济", "离", "坎"),
]

# 索引表
BY_NAME = {h[1]: h for h in HEXAGRAMS}
BY_CODE = {}
for _order, _name, _up, _low in HEXAGRAMS:
    _code = TRIGRAMS[_low] | (TRIGRAMS[_up] << 3)
    BY_CODE[_code] = {
        "order": _order, "name": _name, "upper": _up, "lower": _low,
        "code": _code, "bits": format(_code, "06b")[::-1],  # bits 自下而上
        "upper_nature": TRIGRAM_NATURE[_up], "lower_nature": TRIGRAM_NATURE[_low],
    }


# ========== 三、基础编解码 ==========
def code_of(upper, lower):
    """由上卦、下卦名称得到 6bit 编码"""
    return TRIGRAMS[lower] | (TRIGRAMS[upper] << 3)


def split_code(code):
    """拆分 6bit 为上/下卦"""
    code &= 0b111111
    return TRIGRAM_NAMES[(code >> 3) & 0b111], TRIGRAM_NAMES[code & 0b111]


def name_of(code):
    """编码 → 卦名"""
    info = BY_CODE.get(code & 0b111111)
    return info["name"] if info else None


def code_of_name(name):
    """卦名 → 编码（支持“乾为天”“天山遁”等标准名）"""
    info = BY_NAME.get(name)
    if not info:
        return None
    return code_of(info[2], info[3])


def info_of(code):
    """编码 → 完整结构信息"""
    info = BY_CODE.get(code & 0b111111)
    if not info:
        return None
    out = dict(info)
    out["cuo"] = cuo(code)
    out["zong"] = zong(code)
    out["hu"] = hu(code)
    out["cuo_name"] = name_of(out["cuo"])
    out["zong_name"] = name_of(out["zong"])
    out["hu_name"] = name_of(out["hu"])
    return out


# ========== 四、对称算子 ==========
def cuo(code):
    """错卦：按位取反（阴阳全反）"""
    return (~code) & 0b111111


def zong(code):
    """综卦：上下颠倒（六位反转，初爻↔上爻）"""
    code &= 0b111111
    rev = 0
    for i in range(6):
        if code & (1 << i):
            rev |= 1 << (5 - i)
    return rev


def hu(code):
    """互卦：下卦取 2/3/4 爻，上卦取 3/4/5 爻"""
    code &= 0b111111
    b = [(code >> i) & 1 for i in range(6)]
    lower = b[1] | (b[2] << 1) | (b[3] << 2)
    upper = b[2] | (b[3] << 1) | (b[4] << 2)
    return lower | (upper << 3)


def bian(code, dong):
    """
    变卦：动爻翻转。
    dong: 1-based 爻位列表，如 [1,4] 表示初爻与四爻动。
    """
    mask = 0
    for p in dong or []:
        p = int(p)
        if 1 <= p <= 6:
            mask |= 1 << (p - 1)
    return code ^ mask


def hamming(a, b):
    """两卦汉明距离（0-6）"""
    return bin((a ^ b) & 0b111111).count("1")


def similarity(a, b):
    """结构相似度 = 1 - 汉明距离/6"""
    return 1.0 - hamming(a, b) / 6.0


# ========== 五、四视图（对称性面板用） ==========
def four_views(code, dong=None):
    """
    一卦四视图：本 / 错 / 综 / 互（有动爻时附变卦）+ 两两距离。
    返回可直接 JSON 化的 dict。
    """
    code &= 0b111111
    views = {
        "本卦": code,
        "错卦": cuo(code),
        "综卦": zong(code),
        "互卦": hu(code),
    }
    if dong:
        views["变卦"] = bian(code, dong)
    out = []
    for label, c in views.items():
        out.append({
            "view": label,
            "code": c,
            "binary": format(c, "06b"),
            "name": name_of(c),
            "upper": split_code(c)[0],
            "lower": split_code(c)[1],
            "upper_nature": TRIGRAM_NATURE[split_code(c)[0]],
            "lower_nature": TRIGRAM_NATURE[split_code(c)[1]],
        })
    base = code
    distances = {}
    for row in out:
        if row["view"] != "本卦":
            distances[row["view"]] = {
                "hamming": hamming(base, row["code"]),
                "similarity": round(similarity(base, row["code"]), 3),
            }
    # 错卦与综卦是否重合（八纯卦等自对称情形）
    self_symmetric = {
        "错卦自同": cuo(code) == code,
        "综卦自同": zong(code) == code,
    }
    return {
        "ok": True,
        "base": name_of(code),
        "code": code,
        "views": out,
        "distances": distances,
        "self_symmetric": self_symmetric,
    }


def encode_gua(gua=None, upper=None, lower=None, code=None):
    """统一入口：卦名 / 上下来卦 / 编码，任选其一"""
    if code is not None:
        return int(code) & 0b111111
    if gua:
        c = code_of_name(gua)
        if c is not None:
            return c
    if upper and lower:
        return code_of(upper, lower)
    return None


if __name__ == "__main__":
    for c in (code_of("乾", "艮"), code_of("乾", "乾"), code_of("坤", "坤")):
        r = four_views(c)
        print(r["base"], c, [v["name"] for v in r["views"]])
