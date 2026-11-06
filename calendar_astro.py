# -*- coding: utf-8 -*-
"""
天文历法层 calendar_astro
=========================
用天文计算替代查表：太阳黄经 → 二十四节气、真太阳时、月相、岁星。

依据（象数重构 V2 / L2 层）：
- 二十四节气 = 地球公转黄道每 15° 切一刀
- 干支 = LCM(10,12)=60 的周期，历法应由天文量驱动
- 八字时柱、六爻时辰须用真太阳时（平太阳时 + 均时差 + 经度修正）

纯标准库实现，无第三方依赖。
"""

import math
from functools import lru_cache
from datetime import datetime, timedelta, timezone

# ========== 一、儒略日 ==========
def jd_from_datetime(dt):
    """dt 必须为 aware datetime（UTC）"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
            + d + B - 1524.5)


def datetime_from_jd(jd):
    """儒略日 → UTC datetime"""
    jd += 0.5
    Z = int(math.floor(jd))
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - alpha // 4
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715
    d_int = int(math.floor(day))
    frac = day - d_int
    secs = frac * 86400
    return datetime(year, month, d_int, tzinfo=timezone.utc) + timedelta(seconds=secs)


# ========== 二、太阳黄经（Meeus 低精度，误差 < 0.01°） ==========
def sun_longitude(jd):
    """太阳视黄经（度，0-360）"""
    T = (jd - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    Mr = math.radians(M % 360)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mr)
         + (0.019993 - 0.000101 * T) * math.sin(2 * Mr)
         + 0.000289 * math.sin(3 * Mr))
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    apparent = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega % 360))
    return apparent % 360


def _angle_diff(a, b):
    """a-b 规范化到 [-180, 180)"""
    d = (a - b) % 360
    if d >= 180:
        d -= 360
    return d


# ========== 三、二十四节气 ==========
# 名称与目标黄经（春分 = 0°）
SOLAR_TERMS = [
    ("春分", 0), ("清明", 15), ("谷雨", 30), ("立夏", 45),
    ("小满", 60), ("芒种", 75), ("夏至", 90), ("小暑", 105),
    ("大暑", 120), ("立秋", 135), ("处暑", 150), ("白露", 165),
    ("秋分", 180), ("寒露", 195), ("霜降", 210), ("立冬", 225),
    ("小雪", 240), ("大雪", 255), ("冬至", 270), ("小寒", 285),
    ("大寒", 300), ("立春", 315), ("雨水", 330), ("惊蛰", 345),
]


def solar_term_time(year, target_deg, guess_month=3):
    """求某年太阳黄经达到 target_deg 的 UTC 时刻（牛顿+二分混合）"""
    # 初估：以春分 3/20 为基准，每 15° 约 15.22 天
    base = datetime(year, 3, 20, tzinfo=timezone.utc)
    guess = base + timedelta(days=(target_deg % 360) / 360.0 * 365.2422)
    # 在 ±20 天内扫描符号变化
    step = 0.5
    lo = jd_from_datetime(guess) - 20
    hi = jd_from_datetime(guess) + 20
    f_lo = _angle_diff(sun_longitude(lo), target_deg)
    t = lo
    while t < hi:
        f_t = _angle_diff(sun_longitude(t), target_deg)
        if f_lo == 0:
            break
        if f_lo * f_t < 0 and abs(f_lo) < 90 and abs(f_t) < 90:
            # 二分
            a, b = t - step, t
            for _ in range(50):
                mid = (a + b) / 2
                fm = _angle_diff(sun_longitude(mid), target_deg)
                if _angle_diff(sun_longitude(a), target_deg) * fm <= 0:
                    b = mid
                else:
                    a = mid
            return datetime_from_jd((a + b) / 2)
        f_lo = f_t
        t += step
    return datetime_from_jd(guess)


@lru_cache(maxsize=8)
def solar_terms_of_year(year):
    """全年 24 节气（北京时间）"""
    out = []
    for name, deg in SOLAR_TERMS:
        utc = solar_term_time(year, deg)
        bj = utc + timedelta(hours=8)
        out.append({"name": name, "degree": deg,
                    "time_bj": bj.strftime("%Y-%m-%d %H:%M"),
                    "month": bj.month, "day": bj.day})
    out.sort(key=lambda x: x["time_bj"])
    return out


def current_term(dt_bj):
    """给定北京时间，返回所处节气区间（上一个节气 / 下一个节气）"""
    year = dt_bj.year
    terms = solar_terms_of_year(year - 1)[-6:] + solar_terms_of_year(year) + solar_terms_of_year(year + 1)[:6]
    prev_t = next_t = None
    for t in terms:
        tt = datetime.strptime(t["time_bj"], "%Y-%m-%d %H:%M")
        if tt <= dt_bj:
            prev_t = t
        elif next_t is None:
            next_t = t
            break
    return prev_t, next_t


# ========== 四、均时差与真太阳时 ==========
def equation_of_time(jd):
    """均时差（分钟），Meeus 简化式"""
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360
    e = 0.016709 - 0.0000001236 * T
    y = math.tan(math.radians(23.4397 / 2)) ** 2
    Mr = math.radians(M)
    Lr = math.radians(L0)
    E = (y * math.sin(2 * Lr) - 2 * e * math.sin(Mr)
         + 4 * e * y * math.sin(Mr) * math.cos(2 * Lr)
         - 0.5 * y * y * math.sin(4 * Lr)
         - 1.25 * e * e * math.sin(2 * Mr))
    return 4.0 * math.degrees(E)


def true_solar_time(dt_bj, longitude):
    """
    dt_bj: 北京时间 datetime（naive）
    longitude: 当地经度（东经为正）
    返回 (真太阳时 datetime, 均时差分钟, 经度修正分钟)
    """
    utc = dt_bj.replace(tzinfo=timezone.utc) - timedelta(hours=8)
    jd = jd_from_datetime(utc)
    eot = equation_of_time(jd)
    lon_fix = (longitude - 120.0) * 4.0  # 分钟
    total = eot + lon_fix
    return dt_bj + timedelta(minutes=total), eot, lon_fix


# ========== 五、月相与岁星 ==========
SYNODIC = 29.53058867
NEW_MOON_EPOCH = 2451550.1  # 2000-01-06 18:14 UTC


def moon_phase(jd):
    """月相：返回月龄、相位角、阶段名"""
    age = (jd - NEW_MOON_EPOCH) % SYNODIC
    frac = age / SYNODIC
    if frac < 0.03 or frac > 0.97:
        phase = "新月（朔）"
    elif frac < 0.22:
        phase = "娥眉月"
    elif frac < 0.28:
        phase = "上弦"
    elif frac < 0.47:
        phase = "盈凸月"
    elif frac < 0.53:
        phase = "满月（望）"
    elif frac < 0.72:
        phase = "亏凸月"
    elif frac < 0.78:
        phase = "下弦"
    else:
        phase = "残月"
    return {"age_days": round(age, 2), "phase": phase, "illum_frac": round(frac, 3)}


JUPITER_PERIOD_YEARS = 11.8618


def jupiter_position(dt_bj):
    """岁星（木星）所在十二次/地支（近似，用于太岁校验）"""
    utc = dt_bj.replace(tzinfo=timezone.utc) - timedelta(hours=8)
    jd = jd_from_datetime(utc)
    years = (jd - 2451545.0) / 365.25
    cycle = (years % JUPITER_PERIOD_YEARS) / JUPITER_PERIOD_YEARS
    idx = int(cycle * 12) % 12
    names = ["星纪", "玄枵", "娵訾", "降娄", "大梁", "实沈",
             "鹑首", "鹑火", "鹑尾", "寿星", "大火", "析木"]
    zhi = ["丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅"]
    return {"cycle_frac": round(cycle, 3), "xi": names[idx], "zhi": zhi[idx],
            "period_years": JUPITER_PERIOD_YEARS}


# ========== 六、汇总接口 ==========
def compute(date_str="", time_str="", longitude=116.4, latitude=39.9):
    """
    date_str: YYYY-MM-DD；time_str: HH:MM
    返回可直接 JSON 化的历法面板数据。
    """
    dt_bj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    utc = dt_bj.replace(tzinfo=timezone.utc) - timedelta(hours=8)
    jd = jd_from_datetime(utc)

    tst, eot, lon_fix = true_solar_time(dt_bj, longitude)
    prev_t, next_t = current_term(dt_bj)

    return {
        "ok": True,
        "input": {"date": date_str, "time": time_str,
                  "longitude": longitude, "latitude": latitude},
        "sun": {
            "longitude_deg": round(sun_longitude(jd), 3),
            "equation_of_time_min": round(eot, 2),
            "longitude_correction_min": round(lon_fix, 2),
        },
        "true_solar_time": tst.strftime("%Y-%m-%d %H:%M"),
        "solar_term": {
            "prev": prev_t, "next": next_t,
        },
        "moon": moon_phase(jd),
        "jupiter": jupiter_position(dt_bj),
        "julian_day": round(jd, 4),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(compute("2026-11-06", "12:00", 113.3, 23.1),
                     ensure_ascii=False, indent=2))
