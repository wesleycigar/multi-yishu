#!/usr/bin/env python3
"""
木雷易术引擎 - 皇极经世·国运/大运模块（I）
基于邵雍《皇极经世》「元会运世」体系：
  1元=12会(10800年/会)  1会=30运(360年/运)  1运=12世(30年/世)
锚点（据《皇极经世·以运经世》）：唐尧甲辰(公元前2357年)肇位，为「午会」之始
据此推算任意年份所处 会/运/世，并配世运卦（以六十四卦表）作大势解读
"""
from yijing_yaoci import YIJING_GUACI

HUI_NAMES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
# 午会起点（公元前2357，唐尧甲辰）
WU_HUI_START = -2357
YEAR_PER_YUN = 360
YEAR_PER_SHI = 30

def yuan_hui_yun_shi(year):
    """返回 (会, 运, 世) 定位。会以午会为第7会（子=1）。"""
    offset = year - WU_HUI_START          # 距午会起点年数
    if offset < 0:
        return None
    # 会
    total_hui_offset = WU_HUI_START      # 子会起点 = 午会起点 - 6*10800
    zi_start = WU_HUI_START - 6 * 10800
    n_abs = year - zi_start              # 距元内子会起点的绝对年数
    hui_idx = int(n_abs // 10800)
    hui = HUI_NAMES[hui_idx] if hui_idx < 12 else "过一元"
    # 该会内的运/世
    in_hui = n_abs - hui_idx * 10800
    yun = int(in_hui // YEAR_PER_YUN) + 1       # 第N运
    in_yun = in_hui - (yun-1) * YEAR_PER_YUN
    shi = int(in_yun // YEAR_PER_SHI) + 1       # 第M世
    in_shi = in_yun - (shi-1) * YEAR_PER_SHI
    return {"hui": hui, "yun": yun, "shi": shi,
            "year_in_shi": in_shi+1, "zi_start": zi_start}

# 邵雍先天六十四卦卦气序（自复卦一阳生起，阳仪32卦升、阴仪32卦降）
# 《皇极经世》以先天卦气序配值世卦，此为正法（非文王卦序 mod 64）
XIANTIAN_GUA = [
    "复", "颐", "屯", "益", "震", "噬嗑", "随", "无妄", "明夷", "贲", "既济", "家人", "丰", "离", "革", "同人",
    "临", "损", "节", "中孚", "归妹", "睽", "兑", "履", "泰", "大畜", "需", "小畜", "大壮", "大有", "夬", "乾",
    "姤", "大过", "鼎", "恒", "巽", "井", "蛊", "升", "讼", "困", "未济", "解", "涣", "坎", "蒙", "师",
    "遁", "咸", "旅", "小过", "渐", "蹇", "艮", "谦", "否", "萃", "晋", "豫", "观", "比", "剥", "坤",
]


def shiyun_gua(year):
    """世运卦：按邵雍先天卦气序（复起）配值世卦，循环64卦。"""
    loc = yuan_hui_yun_shi(year)
    if not loc:
        return None
    idx = ((loc["yun"] - 1) * 12 + (loc["shi"] - 1)) % 64
    name = XIANTIAN_GUA[idx]
    guaci = ""
    for i, g in YIJING_GUACI.items():
        if g.get("name", "").replace("卦", "") == name:
            guaci = g.get("guaci", "")
            break
    return {"卦序": idx + 1, "卦名": name, "卦辞": guaci,
            "依据": "邵雍先天六十四卦卦气序（自复卦一阳生起）配值世卦"}

def huangji_analysis(year, personal_wx=None, question="国运"):
    """皇极经世·国运/个人大运分析"""
    lines = ["="*60, "🌏 木雷易术引擎 · 皇极经世·元会运世", "="*60]
    loc = yuan_hui_yun_shi(year)
    if not loc:
        lines.append(f"  年份超出推算范围"); return "\n".join(lines)
    lines.append(f"\n📜 【元会运世定位】{year}年")
    lines.append(f"  • 会：{loc['hui']}会（第{int((year-loc['zi_start'])//10800)+1}会）")
    lines.append(f"  • 运：{loc['yun']}运（每运360年）")
    lines.append(f"  • 世：{loc['shi']}世（每世30年，本年为此世第{loc['year_in_shi']}年）")
    # 世运卦
    sg = shiyun_gua(year)
    if sg:
        lines.append(f"\n🧭 【世运卦】{sg['卦名']}（先天卦气序第{sg['卦序']}）")
        lines.append(f"  卦辞：{sg['卦辞']}")
        lines.append(f"  （配法：{sg['依据']}）")
    # 年干支五行
    from engine_core import TIANGAN, DIZHI
    n = year - 4
    gan = TIANGAN[n % 10] if isinstance(TIANGAN, list) else ""
    # 简化：用年份推干支（公历→干支年）
    try:
        from lunar_python import Solar
        s = Solar.fromYmd(year, 1, 1)
        ygz = s.getLunar().getYearInGanZhiExact()
        gan, zhi = ygz[0], ygz[1]
        wx = DIZHI[zhi]["五行"]
    except Exception:
        gan, zhi, wx = "", "", "未知"
    lines.append(f"\n📅 【值年干支】{gan}{zhi}（{year}年）")
    lines.append(f"  • 年五行：{wx}气当令" if wx != "未知" else f"  • 年五行：未知")
    # 大势判断
    lines.append(f"\n🏆 【{question}·大势研判】")
    lines.append(f"  {gushi(question, wx, sg)}")
    # 把握建议
    lines.append(f"\n💡 【把握建议】")
    for a in advice(wx, question):
        lines.append(f"  {a}")
    # 结合个人日主
    if personal_wx:
        lines.append(f"\n🧑 【结合个人日主{personal_wx}】")
        sheng = {"木":"水","火":"木","土":"火","金":"土","水":"金"}[personal_wx]
        same = "旺" if personal_wx == wx else ("受生" if sheng==wx else "平")
        lines.append(f"  年运{wx}对你日主{personal_wx}：{same}。{personal_advice(personal_wx, wx)}")
    lines.append(f"\n{'='*60}")
    lines.append(f"⚠️ 皇极经世为传统时运学说，仅供参考")
    lines.append(f"{'='*60}")
    return "\n".join(lines)

def gushi(question, wx, sg):
    base = {
        "国运": f"本年值{wx}气当令，大环境侧重「{wx}」相关领域；",
        "事态": f"本年走势随{wx}气起伏，宜顺势而为；",
        "大运": f"本年运势整体趋「{wx}」，时机属性明确；",
    }.get(question, f"本年{question}随{wx}气演化；")
    gua = f"世运卦{sg['卦名']}之象提示：{sg['卦辞']}。" if sg else ""
    return base + gua + ("顺势则吉，逆势则滞。" if question=="国运" else "把握关键节点则有利。")

def advice(wx, question):
    m = {
        "木":["利文教、农林、医药、传媒","宜顺势生长，忌操之过急"],
        "火":["利能源、文化、互联网、品牌","宜张扬声量，忌焦躁冲动"],
        "土":["利地产、基建、实业、稳定行业","宜厚积稳进，忌冒进"],
        "金":["利金融、金属、机械、权威机构","宜果决审慎，忌优柔"],
        "水":["利物流、贸易、智谋、水相关","宜蓄势待发，忌随波逐流"],
    }.get(wx, ["稳中求进","量力而行"])
    return [f"1. {m[0]}", f"2. {m[1]}", f"3. {question}关键在顺应时气、把握节奏"]

def personal_advice(pwx, ywx):
    rel = {"木":{"木":"同气，顺遂","火":"生火，泄力需养","土":"克土，可成事","金":"被金克，受压","水":"得水生，助力"},
           "火":{"木":"得木生，助力","火":"同气，顺遂","土":"生土，泄力","金":"克金，可成","水":"被水克，受压"},
           "土":{"火":"得火生，助力","土":"同气，顺遂","金":"生金，泄力","水":"克水，可成","木":"被木克，受压"},
           "金":{"土":"得土生，助力","金":"同气，顺遂","水":"生水，泄力","木":"克木，可成","火":"被火克，受压"},
           "水":{"金":"得金生，助力","水":"同气，顺遂","木":"生木，泄力","火":"克火，可成","土":"被土克，受压"}}
    return rel.get(pwx, {}).get(ywx, "平")

if __name__ == "__main__":
    print(huangji_analysis(2026, "火", "国运"))
