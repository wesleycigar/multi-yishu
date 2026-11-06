#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 outcome_log.jsonl 增量同步到飞书多维表格「木雷易术·回测台账」。

动机：Render 免费实例磁盘非持久，重启/休眠唤醒后台账与权重归零。
飞书 Base 是持久侧，本脚本负责把本地每一次合议判定搬上去。

用法：
    python3 sync_ledger.py            # 增量同步
    python3 sync_ledger.py --dry-run  # 只打印将要写入的记录，不落库
    python3 sync_ledger.py --all      # 忽略去重标记，全量重放（会产生重复记录，慎用）

依赖：本机已登录的 lark-cli（which lark-cli 有结果即可）。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(HERE, "outcome_log.jsonl")
STATE_FILE = os.path.join(HERE, ".ledger_synced.json")

BASE_TOKEN = "FgSqbfzu8asrGosxEFecyO3hnDh"
TABLE_ID = "tblyHMomrUXXko51"
CLI = os.environ.get("LARK_CLI") or "lark-cli"
BATCH = 100


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("ts", []))
    except Exception:
        return set()


def save_state(ts_set):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"ts": sorted(ts_set)}, f, ensure_ascii=False, indent=1)


def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    out = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def to_record(rec):
    """把台账一行映射成 Base 记录；字段名必须与表结构一致。"""
    ts = rec.get("ts") or ""
    n1, n2 = rec.get("num1"), rec.get("num2")
    qt = rec.get("question_type") or "综合"
    dirs = rec.get("dirs") or {}
    return {
        "判定": "%s · %s/%s · %s" % (ts, n1, n2, qt),
        "判定时间": ts,
        "问题类型": [qt],
        "报数一": n1,
        "报数二": n2,
        "六爻方向": dirs.get("六爻"),
        "梅花方向": dirs.get("梅花"),
        "奇门方向": dirs.get("奇门"),
        "综合方向": rec.get("direction"),
        "一致度": rec.get("agreement"),
        "冲突等级": [rec.get("conflict_level") or "基本一致"],
        "是否兑现": ["兑现"] if rec.get("hit") else ["落空"],
        "权重快照": rec.get("weights_snapshot") or "自动同步",
        "备注": "sync_ledger 自动记录",
    }


def push(records, dry_run=False):
    payload = {"create_records": records}
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return True
    proc = subprocess.run(
        [CLI, "base", "+record-batch-create", "--base-token", BASE_TOKEN,
         "--table-id", TABLE_ID, "--json", json.dumps(payload, ensure_ascii=False),
         "--as", "user"],
        capture_output=True, text=True, timeout=120,
    )
    body = proc.stdout.strip() or proc.stderr.strip()
    try:
        res = json.loads(body)
    except Exception:
        print("同步返回无法解析：", body[:400], file=sys.stderr)
        return False
    if not res.get("ok"):
        print("同步失败：", json.dumps(res.get("error", res), ensure_ascii=False)[:400], file=sys.stderr)
        return False
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    replay_all = "--all" in sys.argv

    rows = load_log()
    if not rows:
        print("台账为空：%s 还没有记录。" % LOG_FILE)
        return 0

    done = set() if replay_all else load_state()
    pending = [r for r in rows if str(r.get("ts")) not in done]
    if not pending:
        print("没有新记录，已同步 %d 条。" % len(done))
        return 0

    ok_all = True
    for i in range(0, len(pending), BATCH):
        chunk = pending[i:i + BATCH]
        if not push([to_record(r) for r in chunk], dry_run):
            ok_all = False
            break
        if not dry_run:
            done.update(str(r.get("ts")) for r in chunk)
            save_state(done)

    if dry_run:
        print("dry-run：%d 条待写入。" % len(pending))
        return 0
    if ok_all:
        print("同步完成：本次 %d 条，累计 %d 条。" % (len(pending), len(done)))
        return 0
    print("同步中断，已成功 %d 条。" % len(done), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
