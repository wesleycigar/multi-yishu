#!/usr/bin/env python3
"""
木雷易术引擎 - 今日一卦 / 今日宜忌（S）
按当前时刻时间起卦，给出今日卦象、卦辞与宜忌
"""
import datetime
from qigua import solar_to_lunar_time, time_qigua
from yijing_yaoci import YIJING_GUACI

# 通用今日宜忌（结合卦意生成）
_YI = ["宜静观其变", "宜守正持中", "宜主动出击", "宜审慎决策", "宜顺势而为", "宜积蓄待发"]
_JI = ["忌冲动冒进", "忌轻信许诺", "忌锋芒过露", "忌操之过急", "忌见利忘义", "忌优柔寡断"]

def today_hexagram():
    """按当前时间起卦，返回 本卦/动爻/卦序/卦辞"""
    now = datetime.datetime.now()
    y_num, m_num, d_num, h_num = solar_to_lunar_time(now.year, now.month, now.day, now.hour)
    ben, dong = time_qigua(y_num, m_num, d_num, h_num)
    order = None
    from gua_trace import FULL_NAME_TO_ORDER
    order = FULL_NAME_TO_ORDER.get(ben)
    guaci = YIJING_GUACI.get(order, {}).get("guaci", "") if order else ""
    return {"date": now.strftime("%Y-%m-%d"), "hexagram": ben, "dong": dong,
            "order": order, "guaci": guaci, "time": now.strftime("%H:%M")}

def today_advice(hexagram, day_wx=None):
    """今日宜忌（依卦意 + 日主微调）"""
    import hashlib
    # 用卦序做确定性取词，避免每日随机感
    seed = hexagram
    h = hashlib.md5(seed.encode()).hexdigest()
    i1 = int(h[0], 16) % len(_YI)
    i2 = int(h[1], 16) % len(_JI)
    yi, ji = _YI[i1], _JI[i2]
    if day_wx:
        # 日主五行微调
        wx_tip = {
            "木": "利文书求索、西北方",
            "火": "利展现声名、南方",
            "土": "利置业安定、东北方",
            "金": "利决断贵人、西方",
            "水": "利藏拙蓄势、北方",
        }.get(day_wx, "")
    else:
        wx_tip = ""
    return {"宜": yi, "忌": ji, "wx_tip": wx_tip}

if __name__ == "__main__":
    t = today_hexagram()
    print(t)
    print(today_advice(t["hexagram"], "火"))
