#!/usr/bin/env python3
"""
木雷易术引擎 - 卦例数据库自动记录（L）
每次断卦自动追加到 99_索引表格/卦例数据库.csv，满足「每卦必记录、每断必验证」
"""
import csv, os, threading, datetime

_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "99_索引表格", "卦例数据库.csv")
_lock = threading.Lock()

_HEADER = ["案例编号","起卦日期","占问类别","问题描述","本卦","变卦","动爻位置",
           "月建","日辰","旬空","用神","原神","忌神","世爻六亲","应爻六亲",
           "断卦结论","置信度(高/中/低)","实际应验结果","应验日期","是否准确",
           "复盘备注","录入人","录入日期"]

def _next_id():
    try:
        with open(_CSV, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if rows:
            last = rows[-1]["案例编号"]
            return f"L{int(last[1:])+1:03d}"
    except Exception:
        pass
    return "L001"

def record_gua(module, q_type, gua_ben, dong_list, gua_bian="", conclusion="",
               confidence="", desc="", ri_zhi="", yue_zhi=""):
    """追加一条卦例记录；返回案例编号"""
    with _lock:
        rid = _next_id()
        today = datetime.date.today().isoformat()
        row = {
            "案例编号": rid, "起卦日期": today, "占问类别": q_type,
            "问题描述": desc, "本卦": gua_ben, "变卦": gua_bian,
            "动爻位置": "、".join(map(str, dong_list or [])),
            "月建": yue_zhi, "日辰": ri_zhi, "旬空": "",
            "用神": "", "原神": "", "忌神": "", "世爻六亲": "", "应爻六亲": "",
            "断卦结论": conclusion, "置信度(高/中/低)": confidence,
            "实际应验结果": "", "应验日期": "", "是否准确": "",
            "复盘备注": f"来源模块:{module}", "录入人": "木雷引擎", "录入日期": today,
        }
        need_header = not os.path.exists(_CSV)
        with open(_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_HEADER)
            if need_header:
                w.writeheader()
            w.writerow(row)
        return rid

def parse_report_meta(report):
    """从报告文本提取 结论/置信度/本卦/变卦/动爻（简）"""
    import re
    conclusion, confidence = "", ""
    m = re.search(r"最终结论[】：]?\s*([^（\n]+)(?:（置信度：(\w+)）)?", report)
    if m:
        conclusion = m.group(1).strip()
        confidence = m.group(2) if m.group(2) else ""
    return conclusion, confidence


def list_records():
    """读取全部卦例记录（清洗 None 键/值，保证 JSON 可序列化）"""
    if not os.path.exists(_CSV):
        return []
    with open(_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    clean = []
    for r in rows:
        if r.get(None) is not None:          # 去掉 None 键（多出的空列）
            del r[None]
        clean.append({k: ("" if v is None else v) for k, v in r.items()})
    return clean


def update_outcome(rid, correct="应验", note=""):
    """复盘：更新某卦例的 是否准确 与 复盘备注。correct: 应验/未验/待验证"""
    if not os.path.exists(_CSV):
        return False
    with _lock:
        rows = list_records()
        if not rows:
            return False
        hit = False
        today = datetime.date.today().isoformat()
        for r in rows:
            if r.get("案例编号") == rid:
                r["是否准确"] = correct
                r["应验日期"] = today
                r["复盘备注"] = (r.get("复盘备注","") + " | " + note).strip(" |") if note else r.get("复盘备注","")
                hit = True
                break
        if not hit:
            return False
        with open(_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_HEADER)
            w.writeheader()
            w.writerows(rows)
        return True

def lines_to_name(lines):
    """由六爻阴阳序列反查六字卦名"""
    from liuyao_paipan import _LOOKUP_NEI_WAI
    from gua_trace import _BAGUA_YAO
    if len(lines) != 6:
        return ""
    nei = wai = None
    for g, y in _BAGUA_YAO.items():
        if y == lines[:3]: nei = g
        if y == lines[3:]: wai = g
    if not (nei and wai):
        return ""
    for name, pair in _LOOKUP_NEI_WAI.items():
        if pair == (nei, wai):
            return name
    return ""

if __name__ == "__main__":
    # 自测
    print("记录测试:", record_gua("test", "财运", "火地晋", [5], "天地否", "平", "中", "自测"))
