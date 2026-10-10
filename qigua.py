#!/usr/bin/env python3
"""
木雷易术引擎 - 起卦模块
支持三种起卦方式：
1. 铜钱法（手动输入六次摇卦结果）
2. 时间起卦（年月日时）
3. 报数起卦（两个数字）
"""
from liuyao_engine import *
from liuyao_paipan import _LOOKUP_NEI_WAI, get_gua_by_name
from engine_core import BAGUA

# ========== 八卦数字对应（先天数） ==========
# 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
XIANTIAN_NUM = {
    "乾": 1, "兑": 2, "离": 3, "震": 4,
    "巽": 5, "坎": 6, "艮": 7, "坤": 8,
}
NUM_TO_GUA = {v: k for k, v in XIANTIAN_NUM.items()}


# ========== 方式1：铜钱法 ==========
def qian_qian_method(results):
    """
    铜钱法起卦
    results: 六次摇卦结果列表，从初爻到上爻
    每次结果：
    - 2 = 背面（字）= 阴爻 --
    - 3 = 正面（背）= 阳爻 —
    - 6 = 老阴（三个背面）= 动阴爻 → 变阳
    - 9 = 老阳（三个正面）= 动阳爻 → 变阴
    
    或者简化输入：每次输入几正几背
    """
    # 转换为卦画和动爻
    gua_hua = []
    dong_yao = []
    
    for i, r in enumerate(results):
        if r == 2:  # 少阴，静阴
            gua_hua.append(0)
        elif r == 3:  # 少阳，静阳
            gua_hua.append(1)
        elif r == 6:  # 老阴，动阴
            gua_hua.append(0)
            dong_yao.append(i + 1)
        elif r == 9:  # 老阳，动阳
            gua_hua.append(1)
            dong_yao.append(i + 1)
        else:
            raise ValueError(f"无效的摇卦结果: {r}，应为2/3/6/9")
    
    # 从卦画找卦名
    # 内卦 = 前3爻，外卦 = 后3爻
    nei_hua = tuple(gua_hua[:3])
    wai_hua = tuple(gua_hua[3:])
    
    # 反查八卦
    BAGUA_HUA = {
        (1,1,1): "乾", (1,1,0): "兑", (1,0,1): "离", (1,0,0): "震",
        (0,1,1): "巽", (0,1,0): "坎", (0,0,1): "艮", (0,0,0): "坤",
    }
    
    nei = BAGUA_HUA[nei_hua]
    wai = BAGUA_HUA[wai_hua]
    
    # 找卦名
    for gua_name, (n, w) in _LOOKUP_NEI_WAI.items():
        if n == nei and w == wai:
            return gua_name, dong_yao
    
    return "未知卦", dong_yao


# ========== 方式2：时间起卦（梅花易数法） ==========
def time_qigua(year_num, month_num, day_num, hour_num):
    """
    时间起卦法（邵雍梅花易数）
    year_num: 年数（地支数，子1丑2...亥12）
    month_num: 农历月份（1-12）
    day_num: 农历日期（1-30）
    hour_num: 时辰数（子1丑2...亥12）
    
    上卦 = (年+月+day) % 8
    下卦 = (年+月+day+时) % 8
    动爻 = (年+月+day+时) % 6
    """
    # 上卦
    shang_num = (year_num + month_num + day_num) % 8
    if shang_num == 0:
        shang_num = 8
    
    # 下卦
    xia_num = (year_num + month_num + day_num + hour_num) % 8
    if xia_num == 0:
        xia_num = 8
    
    # 动爻
    dong = (year_num + month_num + day_num + hour_num) % 6
    if dong == 0:
        dong = 6
    
    shang_gua = NUM_TO_GUA[shang_num]
    xia_gua = NUM_TO_GUA[xia_num]
    
    # 找卦名
    for gua_name, (nei, wai) in _LOOKUP_NEI_WAI.items():
        if nei == xia_gua and wai == shang_gua:
            return gua_name, [dong]
    
    return "未知卦", [dong]


# ========== 方式3：报数起卦 ==========
def number_qigua(num1, num2):
    """
    报数起卦法
    num1: 第一个数字 → 上卦
    num2: 第二个数字 → 下卦
    动爻 = (num1 + num2) % 6
    """
    shang_num = num1 % 8
    if shang_num == 0:
        shang_num = 8
    
    xia_num = num2 % 8
    if xia_num == 0:
        xia_num = 8
    
    dong = (num1 + num2) % 6
    if dong == 0:
        dong = 6
    
    shang_gua = NUM_TO_GUA[shang_num]
    xia_gua = NUM_TO_GUA[xia_num]
    
    for gua_name, (nei, wai) in _LOOKUP_NEI_WAI.items():
        if nei == xia_gua and wai == shang_gua:
            return gua_name, [dong]
    
    return "未知卦", [dong]


# ========== 辅助：从公历时间转农历 ==========
def solar_to_lunar_time(year, month, day, hour):
    """
    公历时间转农历时间，返回（年地支数，月数，日数，时辰数）
    年地支：子1丑2寅3卯4辰5巳6午7未8申9酉10戌11亥12
    """
    from lunar_python import Solar
    solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
    lunar = solar.getLunar()
    
    # 年地支数
    year_zhi = lunar.getYearZhi()
    ZHI_NUM = {"子":1,"丑":2,"寅":3,"卯":4,"辰":5,"巳":6,
               "午":7,"未":8,"申":9,"酉":10,"戌":11,"亥":12}
    year_num = ZHI_NUM[year_zhi]
    
    # 月数（农历）
    month_num = abs(lunar.getMonth())
    
    # 日数（农历）
    day_num = lunar.getDay()
    
    # 时辰数
    time_zhi = lunar.getTimeZhi()
    hour_num = ZHI_NUM[time_zhi]
    
    return year_num, month_num, day_num, hour_num


def get_time_ganzhi(year, month, day, hour):
    """从公历时间取：日辰干支 + 月建地支（按节气月）。
    返回 (ri_gan, ri_zhi, yue_zhi)，供断卦旺衰/旬空使用。"""
    from lunar_python import Solar
    solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
    lunar = solar.getLunar()
    day_gz = lunar.getDayInGanZhiExact()     # 日辰干支，如 "甲子"
    month_gz = lunar.getMonthInGanZhiExact() # 月干支（节气月），如 "丙寅"
    return day_gz[0], day_gz[1], month_gz[1]


# ========== 一键起卦+排盘+断卦 ==========
def qigua_and_duangua(method="time", **kwargs):
    """
    一键完成：起卦 → 排盘 → 断卦
    
    method:
    - "time": 时间起卦，需要 year, month, day, hour
    - "number": 报数起卦，需要 num1, num2
    - "coin": 铜钱法，需要 results（6次摇卦结果列表）
    
    其他参数：ri_gan, ri_zhi, yue_zhi, question_type, gender
    若未显式传 ri_gan/ri_zhi/yue_zhi，将按实际问卦时间自动取月建日辰。
    """
    # 1. 起卦
    if method == "time":
        year = kwargs.get("year")
        month = kwargs.get("month")
        day = kwargs.get("day")
        hour = kwargs.get("hour")
        y_num, m_num, d_num, h_num = solar_to_lunar_time(year, month, day, hour)
        ben_gua, dong_list = time_qigua(y_num, m_num, d_num, h_num)
        print(f"时间起卦: 农历{y_num}年{m_num}月{d_num}日{h_num}时")
    
    elif method == "number":
        num1 = kwargs.get("num1")
        num2 = kwargs.get("num2")
        ben_gua, dong_list = number_qigua(num1, num2)
        print(f"报数起卦: {num1}, {num2}")
    
    elif method == "coin":
        results = kwargs.get("results")
        ben_gua, dong_list = qian_qian_method(results)
        print(f"铜钱法起卦: {results}")
    
    else:
        raise ValueError(f"未知起卦方式: {method}")
    
    # 2. 断卦（月建日辰：优先显式传入，否则按实际问卦时间自动取）
    ri_gan = kwargs.get("ri_gan")
    ri_zhi = kwargs.get("ri_zhi")
    yue_zhi = kwargs.get("yue_zhi")
    gender = kwargs.get("gender", "男")
    question_type = kwargs.get("question_type", "财运")
    if not (ri_gan and ri_zhi and yue_zhi):
        import datetime
        if method == "time" and kwargs.get("year"):
            t_y, t_m, t_d, t_h = kwargs["year"], kwargs["month"], kwargs["day"], kwargs["hour"]
        else:
            now = datetime.datetime.now()
            t_y, t_m, t_d, t_h = now.year, now.month, now.day, now.hour
        ri_gan, ri_zhi, yue_zhi = get_time_ganzhi(t_y, t_m, t_d, t_h)
        print(f"月建日辰: 月建{yue_zhi} 日辰{ri_gan}{ri_zhi}")
    
    from duangua_rules import full_duangua
    return full_duangua(ben_gua, dong_list, ri_gan, ri_zhi, yue_zhi, question_type, gender)


if __name__ == "__main__":
    # 测试1：报数起卦
    print("=== 测试1：报数起卦（3, 8）===")
    print(qigua_and_duangua(
        method="number",
        num1=3, num2=8,
        ri_gan="甲", ri_zhi="子", yue_zhi="申",
        question_type="财运"
    ))
    
    print("\n\n")
    
    # 测试2：时间起卦（今天）
    print("=== 测试2：时间起卦（2026-09-25 14:00）===")
    print(qigua_and_duangua(
        method="time",
        year=2026, month=9, day=25, hour=14,
        ri_gan="乙", ri_zhi="丑", yue_zhi="酉",
        question_type="事业"
    ))
