#!/usr/bin/env python3
"""
木雷易术引擎 - 真实数据库层（SQLite）
在线版本 app 的数据底座：卦例、用户命盘档案、占问历史
SQLite 为落盘关系数据库，可平滑迁移到 MySQL/PostgreSQL
"""
import os, sqlite3, datetime, csv

_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "木雷易术.db")
_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "99_索引表格", "卦例数据库.csv")

def get_conn():
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS gua_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT UNIQUE, date TEXT, q_type TEXT, note TEXT,
        ben_gua TEXT, bian_gua TEXT, dong TEXT,
        month_zhi TEXT, day_zhi TEXT, xunkong TEXT,
        yongshen TEXT, yuanshen TEXT, jishen TEXT,
        shi_liuqin TEXT, ying_liuqin TEXT,
        conclusion TEXT, confidence TEXT,
        correct TEXT DEFAULT '', verified_date TEXT DEFAULT '',
        module TEXT, recorder TEXT DEFAULT '木雷引擎', created TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT '我', birth_year INTEGER, birth_month INTEGER,
        birth_day INTEGER, birth_hour INTEGER, gender TEXT DEFAULT '男',
        rank TEXT DEFAULT '', day_wx TEXT DEFAULT '', created TEXT, updated TEXT
    )""")
    # 兼容旧库：补齐 rank 列
    try:
        c.execute("ALTER TABLE user_profile ADD COLUMN rank TEXT DEFAULT ''")
    except Exception:
        pass
    c.execute("""CREATE TABLE IF NOT EXISTS consultations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, module TEXT, q_type TEXT, method TEXT,
        case_id TEXT, summary TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS visit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, ip TEXT, ua TEXT, path TEXT, module TEXT,
        is_family INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS family_ips (
        ip TEXT PRIMARY KEY, note TEXT DEFAULT '', created TEXT
    )""")
    conn.commit()
    conn.close()

# ---------- 卦例 ----------
def record_gua_sql(module, q_type, ben, dong_list, bian="", conclusion="",
                   confidence="", desc="", ri_zhi="", yue_zhi=""):
    init_db()
    conn = get_conn(); c = conn.cursor()
    today = datetime.date.today().isoformat()
    n = c.execute("SELECT COUNT(*) FROM gua_records").fetchone()[0]
    case_id = f"L{n+1:03d}"
    c.execute("""INSERT INTO gua_records
        (case_id, date, q_type, note, ben_gua, bian_gua, dong,
         month_zhi, day_zhi, conclusion, confidence, module, recorder, created)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (case_id, today, q_type, desc, ben, bian,
         "、".join(map(str, dong_list or [])), yue_zhi, ri_zhi,
         conclusion, confidence, module, "木雷引擎", today))
    conn.commit(); conn.close()
    return case_id

def list_records_sql():
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM gua_records ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_outcome_sql(case_id, correct="应验", note=""):
    init_db()
    conn = get_conn(); c = conn.cursor()
    today = datetime.date.today().isoformat()
    cur = c.execute("""SELECT note FROM gua_records WHERE case_id=?""", (case_id,)).fetchone()
    if not cur:
        conn.close(); return False
    new_note = (cur["note"] + " | " + note).strip(" |") if note else cur["note"]
    c.execute("""UPDATE gua_records SET correct=?, verified_date=?, note=?
                 WHERE case_id=?""", (correct, today, new_note, case_id))
    conn.commit(); conn.close()
    return True

def stats_sql():
    init_db()
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM gua_records").fetchone()[0]
    reviewed = conn.execute("SELECT COUNT(*) FROM gua_records WHERE correct IN ('应验','未验')").fetchone()[0]
    acc = conn.execute("SELECT COUNT(*) FROM gua_records WHERE correct='应验'").fetchone()[0]
    rows = conn.execute("SELECT module, COUNT(*) c FROM gua_records GROUP BY module").fetchall()
    by_module = {r["module"] or "未标注": r["c"] for r in rows}
    conn.close()
    return {"total": total, "reviewed": reviewed, "accurate": acc,
            "accuracy": round(acc / reviewed * 100, 1) if reviewed else 0.0,
            "by_module": by_module}

# ---------- 用户命盘档案 ----------
def save_profile_sql(year, month, day, hour, name="我", gender="男", rank=""):
    init_db()
    from bazi_paipan import paipan_bazi
    day_wx = ""
    try:
        rep = paipan_bazi(year, month, day, hour, gender)
        for line in rep.split("\n"):
            if "日主" in line and "(" in line:
                import re
                m = re.search(r"\((\w)\)", line)
                if m: day_wx = m.group(1); break
    except Exception:
        pass
    conn = get_conn(); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    old = c.execute("SELECT id FROM user_profile ORDER BY id LIMIT 1").fetchone()
    if old:
        c.execute("""UPDATE user_profile SET name=?, birth_year=?, birth_month=?, birth_day=?,
                     birth_hour=?, gender=?, rank=?, day_wx=?, updated=? WHERE id=?""",
                  (name, year, month, day, hour, gender, rank, day_wx, now, old["id"]))
    else:
        c.execute("""INSERT INTO user_profile
            (name, birth_year, birth_month, birth_day, birth_hour, gender, rank, day_wx, created, updated)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (name, year, month, day, hour, gender, rank, day_wx, now, now))
    conn.commit(); conn.close()
    return day_wx

def get_profile_sql():
    init_db()
    conn = get_conn()
    r = conn.execute("SELECT * FROM user_profile ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(r) if r else None

# ---------- 占问历史 ----------
def log_consult(module, q_type, method, case_id, summary=""):
    init_db()
    conn = get_conn(); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO consultations (ts, module, q_type, method, case_id, summary) VALUES (?,?,?,?,?,?)",
              (now, module, q_type, method, case_id, summary))
    conn.commit(); conn.close()

def list_consults_sql(limit=50):
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM consultations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------- 一次性迁移：CSV → SQLite ----------
def migrate_csv_to_sql():
    if not os.path.exists(_CSV):
        return 0
    init_db()
    conn = get_conn(); c = conn.cursor()
    n0 = c.execute("SELECT COUNT(*) FROM gua_records").fetchone()[0]
    if n0 > 0:
        conn.close(); return 0
    with open(_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    moved = 0
    for r in rows:
        if not r.get("案例编号"):
            continue
        today = r.get("起卦日期") or datetime.date.today().isoformat()
        c.execute("""INSERT OR IGNORE INTO gua_records
            (case_id, date, q_type, note, ben_gua, bian_gua, dong,
             month_zhi, day_zhi, xunkong, yongshen, yuanshen, jishen,
             shi_liuqin, ying_liuqin, conclusion, confidence, correct, verified_date, module)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r.get("案例编号",""), today, r.get("占问类别",""), r.get("问题描述",""),
             r.get("本卦",""), r.get("变卦",""), r.get("动爻位置",""),
             r.get("月建",""), r.get("日辰",""), r.get("旬空",""),
             r.get("用神",""), r.get("原神",""), r.get("忌神",""),
             r.get("世爻六亲",""), r.get("应爻六亲",""),
             r.get("断卦结论",""), r.get("置信度(高/中/低)",""),
             r.get("是否准确","") or "", r.get("应验日期","") or "",
             (r.get("复盘备注","") or "").replace("来源模块:","").split("|")[0].strip() or "未标注"))
        moved += 1
    conn.commit(); conn.close()
    return moved

# ---------- 访客留档 & 家人白名单 ----------

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def record_visit(ip, ua="", path="", module=""):
    """记录一次访问。ip 为来访者地址；家人 IP 自动标记"""
    try:
        conn = get_conn(); c = conn.cursor()
        is_family = 1 if c.execute("SELECT 1 FROM family_ips WHERE ip=?", (ip,)).fetchone() else 0
        c.execute("INSERT INTO visit_log (ts, ip, ua, path, module, is_family) VALUES (?,?,?,?,?,?)",
                  (_now(), ip, (ua or "")[:120], path or "", module or "", is_family))
        conn.commit(); conn.close()
        return True
    except Exception:
        return False

def get_family_ips():
    """返回家人 IP 集合"""
    try:
        conn = get_conn()
        rows = conn.execute("SELECT ip FROM family_ips").fetchall()
        conn.close()
        return {r["ip"] for r in rows}
    except Exception:
        return set()

def list_visits_grouped(limit=100):
    """按 IP 分组统计访问：ip, 次数, 首/末次, 使用模块, 是否家人"""
    try:
        conn = get_conn(); c = conn.cursor()
        rows = c.execute("""
            SELECT ip, COUNT(*) AS cnt, MIN(ts) AS first_ts, MAX(ts) AS last_ts,
                   GROUP_CONCAT(DISTINCT module) AS modules, MAX(is_family) AS is_family
            FROM visit_log GROUP BY ip ORDER BY last_ts DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def set_family_ip(ip, is_family=True, note=""):
    """把某 IP 标记为家人（True）或取消（False）"""
    try:
        conn = get_conn(); c = conn.cursor()
        if is_family:
            c.execute("INSERT OR REPLACE INTO family_ips (ip, note, created) VALUES (?,?,?)",
                      (ip, note or "", _now()))
            c.execute("UPDATE visit_log SET is_family=1 WHERE ip=?", (ip,))
        else:
            c.execute("DELETE FROM family_ips WHERE ip=?", (ip,))
            c.execute("UPDATE visit_log SET is_family=0 WHERE ip=?", (ip,))
        conn.commit(); conn.close()
        return True
    except Exception:
        return False

def visit_stats():
    """总览：总次数、去重IP、非家人IP、模块分布"""
    try:
        conn = get_conn(); c = conn.cursor()
        total = c.execute("SELECT COUNT(*) FROM visit_log").fetchone()[0]
        ips = c.execute("SELECT COUNT(DISTINCT ip) FROM visit_log").fetchone()[0]
        stranger = c.execute("SELECT COUNT(DISTINCT ip) FROM visit_log WHERE is_family=0").fetchone()[0]
        mods = c.execute("SELECT module, COUNT(*) c FROM visit_log WHERE module!='' GROUP BY module ORDER BY c DESC").fetchall()
        conn.close()
        return {"total": total, "ips": ips, "stranger_ips": stranger,
                "modules": {r["module"]: r["c"] for r in mods}}
    except Exception:
        return {}

if __name__ == "__main__":
    init_db()
    m = migrate_csv_to_sql()
    print("迁移 CSV→SQLite 卦例:", m, "条")
    print("库内总卦例:", stats_sql()["total"])
    print("档案:", get_profile_sql())
