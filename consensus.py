#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
木雷易术引擎 · 三路裁决层（P1）

把六爻、梅花、奇门三条独立推演路径压成一个结论向量：
    {方向, 强度, 时间窗}

规则：
  · 各路权重 w_k 默认按方法学成熟度给（六爻 0.45 / 梅花 0.30 / 奇门 0.25），
    并可由回测台账（consensus_weights.json）用历史命中率覆盖。
  · 方向取值 -1（凶）…+1（吉），强度取 |方向|。
  · 一致度 = 1 − 加权标准差；冲突分级：≥0.7 重大分歧，≥0.4 分歧，<0.4 基本一致。
  · 时间窗为规则推断（C 级），不是预测。

硬规则：冲突 ≥0.7 时不输出单一结论，改为并列双解。
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHT_FILE = os.path.join(HERE, "consensus_weights.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outcome_log.jsonl")

DEFAULT_WEIGHTS = {"六爻": 0.45, "梅花": 0.30, "奇门": 0.25}

# 奇门八门 / 九星 吉凶
MEN_JX = {
    "生门": "大吉", "开门": "大吉", "休门": "吉",
    "杜门": "平", "景门": "平",
    "伤门": "凶", "惊门": "凶", "死门": "大凶",
}
XING_JX = {
    "天辅": "大吉", "天心": "大吉", "天任": "吉", "天冲": "吉",
    "天英": "平",
    "天柱": "凶", "天蓬": "大凶", "天芮": "大凶",
}
JX_VAL = {"大吉": 1.0, "吉": 0.6, "平": 0.0, "凶": -0.6, "大凶": -1.0}


# ---------------- 权重台账 ----------------

def load_weights():
    try:
        with open(WEIGHT_FILE, encoding="utf-8") as f:
            w = json.load(f)
        if isinstance(w, dict) and w:
            out = dict(DEFAULT_WEIGHTS)
            out.update({k: float(v) for k, v in w.items() if isinstance(v, (int, float))})
            return out
    except Exception:
        pass
    return dict(DEFAULT_WEIGHTS)


def save_weights(weights):
    try:
        with open(WEIGHT_FILE, "w", encoding="utf-8") as f:
            json.dump(weights, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def count_outcomes():
    """回测台账已积累多少例"""
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def log_outcome(sources, hit, payload=None):
    """
    记一笔真实结果：写台账 + 按各路更新权重。
    sources: 参与本次合议的路名列表；hit: 该结论最终是否兑现。
    """
    import time as _time
    rec = {
        "ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
        "hit": bool(hit),
        "sources": list(sources),
    }
    if isinstance(payload, dict):
        for k in ("num1", "num2", "question_type", "direction", "agreement", "conflict_level", "dirs"):
            if k in payload:
                rec[k] = payload[k]
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    for src in sources:
        record_outcome(src, hit)
    return {"ok": True, "weights": load_weights(), "trained": count_outcomes(), "rec": rec}


def record_outcome(source, hit):
    """
    回测台账：每命中/落空一次，按指数滑动更新该路权重。
    hit=True 命中，False 落空。单路权重限制在 0.10–0.60 之间，避免一路通吃。
    """
    w = load_weights()
    cur = w.get(source, 0.25)
    cur = cur * 0.9 + (0.6 if hit else 0.1) * 0.1
    cur = max(0.10, min(0.60, cur))
    w[source] = round(cur, 3)
    save_weights(w)
    return w


# ---------------- 单路 → 方向 ----------------

def _tanh(x, scale):
    return math.tanh(x / scale)


def direction_of(meta):
    """把单路 meta 转成 (方向 -1..1, 说明文本)"""
    src = meta.get("source")

    if src == "六爻":
        score = float(meta.get("score") or 0)
        d = _tanh(score, 3.0)
        verdict = meta.get("verdict") or ""
        return d, "六爻分值 %s（%s），用神%s" % (score, verdict or "—", meta.get("yongshen") or "—")

    if src == "梅花":
        score = float(meta.get("score") or 0)
        d = _tanh(score, 2.5)
        return d, "体%s（%s）用%s（%s），体用分值 %s" % (
            meta.get("ti") or "—", meta.get("ti_wx") or "—",
            meta.get("yong") or "—", meta.get("yong_wx") or "—", score)

    if src == "奇门":
        men = str(meta.get("zhi_shi_men") or "")
        if men and not men.endswith("门"):
            men = men + "门"
        xing = str(meta.get("zhi_fu") or "")
        mv = JX_VAL.get(MEN_JX.get(men, "平"), 0.0)
        xv = JX_VAL.get(XING_JX.get(xing, "平"), 0.0)
        d = (mv * 0.55 + xv * 0.45)
        return d, "值符%s（%s）· 值使%s（%s）" % (
            xing or "—", XING_JX.get(xing, "平"),
            men or "—", MEN_JX.get(men, "平"))

    return 0.0, "未知来源"


# ---------------- 裁决 ----------------

def _label(d):
    if d >= 0.35:
        return "偏吉"
    if d <= -0.35:
        return "偏凶"
    return "中性偏观望"


def _window(metas, overall):
    """时间窗：规则推断，C 级，不承诺"""
    liu = next((m for m in metas if m.get("source") == "六爻"), None)
    s = abs(float(liu.get("score") or 0)) if liu else 0
    if s >= 4:
        return "1–2 周内见分晓"
    if s >= 2:
        return "1–3 个月"
    return "3 个月以上，或待条件成熟"


def vote(metas):
    weights = load_weights()
    votes = []
    for m in metas:
        d, note = direction_of(m)
        votes.append({
            "source": m.get("source"),
            "dir": round(d, 3),
            "weight": weights.get(m.get("source"), 0.20),
            "note": note,
        })

    total_w = sum(v["weight"] for v in votes) or 1.0
    overall = sum(v["dir"] * v["weight"] for v in votes) / total_w

    var = sum(v["weight"] * ((v["dir"] - overall) ** 2) for v in votes) / total_w
    std = math.sqrt(max(0.0, var))
    agreement = max(0.0, 1.0 - std)

    if std >= 0.7:
        level, code = "重大分歧", "conflict_high"
    elif std >= 0.4:
        level, code = "存在分歧", "conflict_mid"
    else:
        level, code = "基本一致", "agree"

    mean_strength = sum(abs(v["dir"]) * v["weight"] for v in votes) / total_w
    confidence = agreement * (0.4 + 0.6 * mean_strength)

    return {
        "ok": True,
        "direction": round(overall, 3),
        "direction_label": _label(overall),
        "strength": round(abs(overall), 3),
        "agreement": round(agreement, 3),
        "divergence": round(std, 3),
        "conflict_level": level,
        "conflict_code": code,
        "confidence": round(confidence, 3),
        "confidence_label": ("高" if confidence >= 0.65 else "中" if confidence >= 0.40 else "低"),
        "window": _window(metas, overall),
        "votes": votes,
        "dual_solution": std >= 0.7,
    }


def render(result):
    """裁决结果的文字段（放进报告 / 前端）"""
    lines = []
    lines.append("⚖️ 【三路合议 · 一致度与置信】")
    for v in result["votes"]:
        lines.append("  · %s：%s（方向 %+.2f，权重 %.2f）—— %s" % (
            v["source"], _label(v["dir"]), v["dir"], v["weight"], v["note"]))

    lines.append("  → 综合方向：%s（%+.2f）｜一致度 %.2f｜冲突等级：%s" % (
        result["direction_label"], result["direction"],
        result["agreement"], result["conflict_level"]))
    lines.append("  → 置信：%s（%.2f）｜时间窗：%s（规则推断，C 级）" % (
        result["confidence_label"], result["confidence"], result["window"]))

    if result["dual_solution"]:
        lines.append("  ⚠️ 三路分歧过大，不合并为单一结论。建议按「吉向/凶向」两套解法并列执行：")
        lines.append("     · 吉向解法：按占优路径（方向最高者）先做小仓试探，设止损。")
        lines.append("     · 凶向解法：按方向最低者做防御准备，延迟不可逆决策。")
    elif result["conflict_code"] == "conflict_mid":
        lines.append("  ⚠️ 存在分歧：结论只作倾向，不宜据此做重仓或不可逆决定。")
    else:
        lines.append("  ✅ 三路基本同向，结论可用，但仍以 B/C 级规则为限。")

    lines.append("  📌 分级：方向/强度＝C 级（需回测）；单路规则＝B 级（古籍可溯源）；")
    lines.append("      「三路同向即更可信」是方法学假设（D 级），不构成证据。")
    return "\n".join(lines)


def assess(metas):
    """一步出结果 + 文本"""
    r = vote(metas)
    r["text"] = render(r)
    r["weights"] = load_weights()
    r["trained"] = count_outcomes()
    return r


if __name__ == "__main__":
    demo = [
        {"source": "六爻", "score": 3.5, "verdict": "吉", "yongshen": "妻财"},
        {"source": "梅花", "score": 2, "ti": "乾", "ti_wx": "金", "yong": "兑", "yong_wx": "金"},
        {"source": "奇门", "zhi_fu": "天辅", "zhi_shi_men": "生"},
    ]
    r = assess(demo)
    print(r["text"])
    print()
    print("一致度", r["agreement"], "冲突", r["conflict_level"], "置信", r["confidence_label"])
