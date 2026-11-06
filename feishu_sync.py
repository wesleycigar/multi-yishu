#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端把回测台账写进飞书多维表格（Base「木雷易术·回测台账」）。

为什么需要它：Render 免费实例磁盘不持久，outcome_log.jsonl 在这里随时会归零；
飞书 Base 才是持久侧。

启用条件（未配置时本模块静默跳过，不影响引擎运行）：
    FEISHU_APP_ID      飞书自建应用 app_id
    FEISHU_APP_SECRET  飞书自建应用 app_secret
应用需开通多维表格写权限（bitable:app 或 bitable:app:readonly 对应写权限），
并把该 Base 的协作者加上这个应用。

字段口径与回测台账表一致；判定时间用毫秒时间戳写 datetime 字段。
"""
import json
import os
import time
import urllib.request

BASE_TOKEN = "FgSqbfzu8asrGosxEFecyO3hnDh"
TABLE_ID = "tblyHMomrUXXko51"
CONFLICT_CODE = {"基本一致": 0, "存在分歧": 1, "重大分歧": 2}

_token_cache = {"value": None, "expire": 0}


def _post(url, payload, headers=None, timeout=20):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tenant_token():
    app_id = os.environ.get("FEISHU_APP_ID")
    secret = os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not secret:
        return None
    if _token_cache["value"] and time.time() < _token_cache["expire"] - 60:
        return _token_cache["value"]
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    res = _post(url, {"app_id": app_id, "app_secret": secret})
    token = res.get("tenant_access_token")
    if token:
        _token_cache["value"] = token
        _token_cache["expire"] = time.time() + int(res.get("expire", 3600))
    return token


def _ts_to_ms(ts):
    try:
        t = time.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(t) * 1000)
    except Exception:
        return None


def build_fields(rec):
    """把台账一行映射成 Base 字段值（bitable v1 格式）。"""
    dirs = rec.get("dirs") or {}
    ts = rec.get("ts") or time.strftime("%Y-%m-%d %H:%M:%S")
    qt = rec.get("question_type") or "综合"
    fields = {
        "判定": "%s · %s/%s · %s" % (ts, rec.get("num1"), rec.get("num2"), qt),
        "问题类型": qt,
        "报数一": rec.get("num1"),
        "报数二": rec.get("num2"),
        "六爻方向": dirs.get("六爻"),
        "梅花方向": dirs.get("梅花"),
        "奇门方向": dirs.get("奇门"),
        "综合方向": rec.get("direction"),
        "一致度": rec.get("agreement"),
        "冲突等级": rec.get("conflict_level") or "基本一致",
        "是否兑现": "兑现" if rec.get("hit") else "落空",
        "命中": 1 if rec.get("hit") else 0,
        "冲突值": CONFLICT_CODE.get(rec.get("conflict_level"), 0),
        "备注": "云端自动入库",
    }
    ms = _ts_to_ms(ts)
    if ms:
        fields["判定时间"] = ms
    return {k: v for k, v in fields.items() if v is not None}


def push_outcome(rec):
    """写一条记录；凭证缺失或失败返回 False，不抛异常。"""
    token = _tenant_token()
    if not token:
        return False
    url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/%s/tables/%s/records"
           % (BASE_TOKEN, TABLE_ID))
    try:
        res = _post(url, {"fields": build_fields(rec)},
                    headers={"Authorization": "Bearer " + token})
        return bool(res.get("code") == 0)
    except Exception:
        return False


if __name__ == "__main__":
    print("凭证状态：", "已配置" if _tenant_token() else "未配置（设置 FEISHU_APP_ID / FEISHU_APP_SECRET）")
