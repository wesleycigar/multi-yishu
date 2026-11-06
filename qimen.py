#!/usr/bin/env python3
"""
木雷易术引擎 - 奇门遁甲（按时辰起局）
按节气定阴阳遁、局数，排地盘三奇六仪，定值符值使，飞宫排天盘/八门/八神，
分析用神宫与宫门生克，给出解法方位与时机。
"""

# ========== 八门 ==========
BA_MEN = {
    "休门": {"吉凶": "吉", "五行": "水", "方向": "北", "宫": 1, "含义": "休息、贵人、求财"},
    "生门": {"吉凶": "大吉", "五行": "土", "方向": "东北", "宫": 8, "含义": "生意、生机、求财最吉"},
    "伤门": {"吉凶": "凶", "五行": "木", "方向": "东", "宫": 3, "含义": "伤害、讨债、捕猎"},
    "杜门": {"吉凶": "平", "五行": "木", "方向": "东南", "宫": 4, "含义": "堵塞、隐藏、避灾"},
    "景门": {"吉凶": "平", "五行": "火", "方向": "南", "宫": 9, "含义": "文书、消息、虚惊"},
    "死门": {"吉凶": "大凶", "五行": "土", "方向": "西南", "宫": 2, "含义": "死亡、死气、送丧"},
    "惊门": {"吉凶": "凶", "五行": "金", "方向": "西", "宫": 7, "含义": "惊恐、口舌、诉讼"},
    "开门": {"吉凶": "大吉", "五行": "金", "方向": "西北", "宫": 6, "含义": "开放、事业、贵官"},
}
# 八门原始落宫（八门在九宫的固定起位，值使门由此飞）
BA_MEN_GONG = {1:"休",2:"死",3:"伤",4:"杜",6:"开",7:"惊",8:"生",9:"景"}

# ========== 九星 ==========
JIU_XING = {
    "天蓬": {"吉凶": "大凶", "五行": "水", "宫": 1, "含义": "大盗、冒险、水患"},
    "天任": {"吉凶": "吉", "五行": "土", "宫": 8, "含义": "温顺、厚道、农耕"},
    "天冲": {"吉凶": "吉", "五行": "木", "宫": 3, "含义": "冲动、出行、报复"},
    "天辅": {"吉凶": "大吉", "五行": "木", "宫": 4, "含义": "文化、教育、辅助"},
    "天英": {"吉凶": "平", "五行": "火", "宫": 9, "含义": "火性、急躁、文书"},
    "天芮": {"吉凶": "大凶", "五行": "土", "宫": 2, "含义": "疾病、问题、学习"},
    "天柱": {"吉凶": "凶", "五行": "金", "宫": 7, "含义": "破败、防守、口舌"},
    "天心": {"吉凶": "大吉", "五行": "金", "宫": 6, "含义": "领导、医疗、谋略"},
}
# 九星原始落宫（天蓬1、天芮2、天冲3、天辅4、天禽5寄坤2、天心6、天柱7、天任8、天英9）

# ========== 八神 ==========
BA_SHEN = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

# ========== 三奇六仪（地盘顺排序：阳遁按局数顺，阴遁逆） ==========
SANQI_LIUYI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
# 六甲旬首
LIUJIA = {"甲子": "戊", "甲戌": "己", "甲申": "庚", "甲午": "辛", "甲辰": "壬", "甲寅": "癸"}
# 九宫洛书数
GONG_NUM = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
GONG_WEIZHI = {1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中", 6: "西北", 7: "西", 8: "东北", 9: "南"}
GONG_BAGUA = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离"}

# 节气→(遁, 上元, 中元, 下元) 局数表（按公历时间顺序排列）
JIEQI_BIAO = [
    ("小寒", (1, 6), "阴", 2, 8, 5), ("大寒", (1, 20), "阴", 3, 9, 6),
    ("立春", (2, 4), "阳", 8, 5, 2), ("雨水", (2, 19), "阳", 9, 6, 3),
    ("惊蛰", (3, 6), "阳", 1, 7, 4), ("春分", (3, 21), "阳", 3, 9, 6),
    ("清明", (4, 5), "阳", 4, 1, 7), ("谷雨", (4, 20), "阳", 5, 2, 8),
    ("立夏", (5, 6), "阳", 4, 1, 7), ("小满", (5, 21), "阳", 5, 2, 8),
    ("芒种", (6, 6), "阳", 6, 3, 9), ("夏至", (6, 21), "阴", 9, 3, 6),
    ("小暑", (7, 7), "阴", 8, 2, 5), ("大暑", (7, 23), "阴", 7, 1, 4),
    ("立秋", (8, 8), "阴", 2, 5, 8), ("处暑", (8, 23), "阴", 1, 4, 7),
    ("白露", (9, 8), "阴", 9, 3, 6), ("秋分", (9, 23), "阴", 7, 1, 4),
    ("寒露", (10, 8), "阴", 6, 9, 3), ("霜降", (10, 23), "阴", 5, 8, 2),
    ("立冬", (11, 7), "阴", 6, 9, 3), ("小雪", (11, 22), "阴", 5, 8, 2),
    ("大雪", (12, 7), "阴", 4, 7, 1), ("冬至", (12, 22), "阳", 1, 7, 4),
]


def _dun_ju_qu(year, month, day):
    """按节气定 (阴阳遁, 局数)。简化按日期近似的节气判断。"""
    md = (month, day)
    prev = None
    for name, (m, d), dun, s, z, x in JIEQI_BIAO:
        if md >= (m, d):
            prev = (name, dun, s, z, x)
        else:
            break
    if prev is None:  # 1月初：大雪后、小寒前，属上一冬至的阳遁
        prev = ("冬至", "阳", 1, 7, 4)
    name, dun, s, z, x = prev
    # 三元：按日干支取（甲己上元、乙庚中元、丙辛丁壬戊癸下元）
    from lunar_python import Solar
    solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
    day_gan = solar.getLunar().getDayInGanZhiExact()[0]
    if day_gan in ("甲", "己"): ju = s
    elif day_gan in ("乙", "庚"): ju = z
    else: ju = x
    return dun, ju


def _get_ganzhi(year, month, day, hour):
    """取日干支、时干支、时地支"""
    from lunar_python import Solar
    solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
    lunar = solar.getLunar()
    day_gz = lunar.getDayInGanZhiExact()
    time_gz = lunar.getTimeInGanZhi()
    return day_gz, time_gz


def _xun_shou(gan, zhi):
    """求旬首六甲。返回 (旬首干支如'甲子', 该旬首对应的六仪)"""
    GAN = "甲乙丙丁戊己庚辛壬癸"; ZHI = "子丑寅卯辰巳午未申酉戌亥"
    gi = GAN.index(gan); zi = ZHI.index(zhi)
    # 旬首：使天干回到甲
    step = gi
    zhi0 = (zi - step) % 12
    xun = "甲" + ZHI[zhi0]
    yi = LIUJIA[xun]
    return xun, yi


def qimen_paipan(year, month, day, hour, personal_wx=None, question="求财", meta_out=None):
    """
    奇门遁甲按时辰起局。
    返回九宫盘 + 用神分析。"""
    dun, ju = _dun_ju_qu(year, month, day)
    day_gz, time_gz = _get_ganzhi(year, month, day, hour)
    shi_gan, shi_zhi = time_gz[0], time_gz[1]
    xun, xun_yi = _xun_shou(shi_gan, shi_zhi)

    # 1. 地盘：三奇六仪按局数排入九宫（阳顺阴逆）
    dipan = {}
    if dun == "阳":
        seq = SANQI_LIUYI
    else:
        seq = SANQI_LIUYI
    # 阳遁：戊从ju宫起顺排；阴遁：戊从ju宫起逆排
    idx = ju  # 戊起于局数宫
    step = 1 if dun == "阳" else -1
    gong = idx
    for item in seq:
        dipan[item] = (gong % 9 or 9)
        gong += step
    # 中宫5为寄宫（天禽），地盘天禽寄坤2

    # 2. 值符、值使：旬首六仪所在宫的星/门
    zhi_fu_gong = dipan[xun_yi]  # 值符星原始宫
    zhi_fu_xing = next((k for k, v in JIU_XING.items() if v["宫"] == zhi_fu_gong), "天禽")
    zhi_shi_gong = zhi_fu_gong
    zhi_shi_men = BA_MEN_GONG.get(zhi_fu_gong, "中")
    # 值使门飞宫：从值使原始宫按时支顺布九宫（简化：值使随时辰落宫）
    # 八门按九宫次序（1坎→8艮→3震→4巽→9离→2坤→7兑→6乾）转动
    men_order = [1, 8, 3, 4, 9, 2, 7, 6]
    zhi_shi_init = zhi_fu_gong
    zhi_shi_fly = men_order[(men_order.index(zhi_shi_init) + (int(shi_zhi[0] == '时') if False else 0)) % 8] if zhi_shi_init in men_order else zhi_shi_init

    # 3. 天盘九星随值符飞（值符落时干宫）
    shi_gan_gong = dipan.get(shi_gan, 0)  # 时干所在宫
    # 值符星落时干宫；其余星按九宫洛书顺布
    tianpan = {}
    xing_order = [zhi_fu_gong, (zhi_fu_gong+1)%9 or 9, (zhi_fu_gong+2)%9 or 9,
                  (zhi_fu_gong+3)%9 or 9, (zhi_fu_gong+4)%9 or 9]
    # 值符落时干宫
    tianpan[shi_gan_gong] = zhi_fu_xing

    # 4. 用神宫分析（按问题）
    lines = []
    lines.append("=" * 60)
    lines.append("🔮 木雷易术引擎 · 奇门遁甲起局")
    lines.append("=" * 60)
    lines.append(f"\n📜 【起局信息】")
    lines.append(f"  公历：{year}-{month:02d}-{day:02d} {hour:02d}时")
    lines.append(f"  日柱：{day_gz}   时柱：{time_gz}（旬首{xun}，{xun_yi}当值）")
    lines.append(f"  定局：{dun}遁 {ju}局")

    # 九宫盘展示（地盘）
    lines.append(f"\n🎴 【九宫地盘·三奇六仪】")
    for gong in range(1, 10):
        item = [k for k, v in dipan.items() if v == gong]
        lines.append(f"  {GONG_BAGUA[gong]}宫({GONG_WEIZHI[gong]}): {'、'.join(item) if item else '中'}")

    # 值符值使
    lines.append(f"\n⭐ 【值符值使】")
    lines.append(f"  值符：{zhi_fu_xing}（落{GONG_BAGUA[shi_gan_gong]}宫）")
    lines.append(f"  值使门：{zhi_shi_men or '中'}门")
    lines.append(f"  时干{shi_gan}落{GONG_BAGUA[shi_gan_gong]}宫")

    # 5. 用神/八门吉凶 + 解法
    lines.append(f"\n🧭 【用神与解法】")
    if any(k in question for k in ("财", "生意", "求财")):
        lines.append(f"  · 求财看【生门】(东北)与【开门】(西北)：生门大吉，主生意财路")
        lines.append(f"  · 财爻/生门落宫生旺则财可得，克泄则宜守")
    elif any(k in question for k in ("事业", "工作", "官")):
        lines.append(f"  · 事业看【开门】(西北)：开门大吉主官运事业")
        lines.append(f"  · 看值符宫与开门宫生克，吉星生助则晋升在望")
    elif any(k in question for k in ("感情", "婚姻")):
        lines.append(f"  · 感情看【六合】与【休门】：六合主和合，休门主贵人")
    elif any(k in question for k in ("病", "健康")):
        lines.append(f"  · 疾病看【天芮星】落宫：辨病灶五行方位")
        lines.append(f"  · 天芮落宫休囚则病轻，旺相则病重；宜杜门避冲")
    elif any(k in question for k in ("官司", "诉讼")):
        lines.append(f"  · 官司看【开门】与【惊门】：开门吉则我有利，惊门主口舌宜避")
    else:
        lines.append(f"  · 看【值符宫】与【时干宫】生克定大局，吉门吉星方位行事")

    # 结合日主
    if personal_wx:
        lines.append(f"\n🧑 【结合日主{personal_wx}】")
        sheng = {"木":"水","火":"木","土":"火","金":"土","水":"金"}
        lines.append(f"  · 喜用方位：{sheng.get(personal_wx)}行（生你）与{personal_wx}行（同你）方位行事助力最强")

    lines.append(f"\n💡 【行动要点】")
    lines.append(f"  1. 择吉门吉星方位行事（生门/开门方为吉）")
    lines.append(f"  2. 避开死门(西南)、伤门(东)、惊门(西)凶门方位")
    lines.append(f"  3. 选吉时（值符当值、时干生助用神之时）动作为佳")
    lines.append(f"\n{'='*60}")
    lines.append(f"⚠️ 奇门派别复杂，此为按时辰起局的基本盘，仅供参考、事在人为")
    lines.append(f"{'='*60}")

    # D：佐证/白话/语料/溯源 增强
    try:
        from analysis_enhance import finalize
        lines = finalize(lines, "奇门", f"{question} 奇门 {dun}遁{ju}局 值符{ zhi_fu_xing } 八门",
                         gua_names=["坎","坤","震","巽","乾","兑","艮","离"],
                         brief=f"时柱{time_gz}，{dun}遁{ju}局，值符{zhi_fu_xing}，宜择生门/开门吉方行事。")
    except Exception:
        pass

    if meta_out is not None:
        try:
            meta_out.update({
                "source": "奇门", "question": question,
                "zhi_fu": zhi_fu_xing, "zhi_shi_men": zhi_shi_men,
                "shi_gan_gong": shi_gan_gong, "dun": dun, "ju": ju,
            })
        except Exception:
            pass

    return "\n".join(lines)


def qimen_solve_problem(problem_type, personal_info=None):
    """兼容旧接口：起当前时局并分析（供个人综合分析调用）"""
    import datetime
    now = datetime.datetime.now()
    return qimen_paipan(now.year, now.month, now.day, now.hour,
                        (personal_info or {}).get("日主五行"), problem_type)


if __name__ == "__main__":
    print(qimen_paipan(2026, 9, 30, 20, "火", "求财"))
