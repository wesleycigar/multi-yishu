# -*- coding: utf-8 -*-
"""
五行耦合矩阵 wuxing_matrix
==========================
把“生克”从文字规则升级为可计算的 5×5 耦合矩阵 + 反馈系统。

依据（象数重构 V2 / L1-L3 层）：
- 河图十数两两差 5 → 模 5 分类 → 五行
- 生环（促进）+ 克环（制约）→ 扰动后是否回归平衡，等价于负反馈控制
- 谱半径 ρ(M) < 1 收敛（稳），≥ 1 发散/震荡（动）

纯标准库实现。
"""

# ========== 一、五行基础 ==========
ORDER = ["木", "火", "土", "金", "水"]     # 相生顺序
IDX = {w: i for i, w in enumerate(ORDER)}


def sheng_target(i):
    """i 所生之行"""
    return (i + 1) % 5


def ke_target(i):
    """i 所克之行"""
    return (i + 2) % 5


# ========== 二、耦合矩阵 ==========
def build_matrix(sheng_w=0.55, ke_w=0.35, self_w=0.0):
    """
    M[i][j] = 行 i 对行 j 的作用强度（正=生，负=克）
    """
    M = [[0.0] * 5 for _ in range(5)]
    for i in range(5):
        M[i][sheng_target(i)] += sheng_w
        M[i][ke_target(i)] += -ke_w
        M[i][i] += self_w
    return M


def mat_vec(M, x):
    return [sum(M[i][j] * x[j] for j in range(5)) for i in range(5)]


def spectral_radius(M, iters=200):
    """
    求最大特征值模 |λmax|。
    生克矩阵是循环矩阵（M[i][j] = c[(j-i)%5]），可用解析式；
    非循环时退回幂迭代。避免 numpy 依赖。
    """
    # 判定是否循环
    c = M[0][:]
    is_circulant = all(
        abs(M[i][j] - c[(j - i) % 5]) < 1e-12
        for i in range(5) for j in range(5)
    )
    if is_circulant:
        import cmath, math as _m
        lam_max = 0.0
        for k in range(5):
            lam = sum(c[j] * cmath.exp(2j * _m.pi * j * k / 5.0) for j in range(5))
            lam_max = max(lam_max, abs(lam))
        return lam_max

    x = [0.11, 0.23, 0.35, 0.47, 0.59]
    lam = 0.0
    for _ in range(iters):
        y = mat_vec(M, x)
        norm = math_sqrt(sum(v * v for v in y))
        if norm < 1e-12:
            return 0.0
        lam = norm / math_sqrt(sum(v * v for v in x))
        x = [v / norm for v in y]
    return lam


def math_sqrt(v):
    return v ** 0.5


# ========== 三、旺衰演化 ==========
def assess(month_wx="", day_wx="", year_wx="",
           sheng_w=0.55, ke_w=0.35, steps=60, gain=None):
    """
    以月令为主增益、日辰与流年为扰动，迭代求五行状态。

    返回：
      - rho：耦合矩阵谱半径（系统稳定性）
      - converged：是否收敛
      - scores：五行得分（0-2）
      - curve：归一化演化曲线（抽样 12 点）
      - verdict：稳定/动荡判语
      - strongest / weakest
    """
    M = build_matrix(sheng_w, ke_w)
    rho = spectral_radius(M)

    g = gain or {"月令": 1.00, "日辰": 0.25, "流年": 0.15}
    base = [0.5] * 5
    if month_wx in IDX:
        base[IDX[month_wx]] += g["月令"]
    if day_wx in IDX:
        base[IDX[day_wx]] += g["日辰"]
    if year_wx in IDX:
        base[IDX[year_wx]] += g["流年"]

    x = [0.5] * 5
    curve = []
    diffs = []
    for t in range(steps):
        nx = mat_vec(M, x)
        xn = []
        for i in range(5):
            v = nx[i] + base[i]
            v = max(0.0, min(2.0, v))   # 截断，防止无界
            xn.append(v)
        diff = max(abs(xn[i] - x[i]) for i in range(5))
        diffs.append(diff)
        x = xn
        if t % max(1, steps // 12) == 0:
            curve.append([round(v, 3) for v in x])

    converged = diffs[-1] < 1e-3
    scores = {ORDER[i]: round(x[i], 3) for i in range(5)}
    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)

    if converged and rho < 1:
        verdict = "收敛：扰动后可回归平衡，主稳"
    elif rho >= 1:
        verdict = "发散/震荡：扰动放大，主变动"
    else:
        verdict = "未完全收敛：仍在调整中"

    return {
        "ok": True,
        "matrix": M,
        "rho": round(rho, 3),
        "converged": converged,
        "final_diff": round(diffs[-1], 5),
        "inputs": {"month": month_wx, "day": day_wx, "year": year_wx},
        "scores": scores,
        "strongest": strongest,
        "weakest": weakest,
        "curve": curve,
        "verdict": verdict,
    }


if __name__ == "__main__":
    import json
    r = assess("木", "水", "火")
    print(json.dumps({k: v for k, v in r.items() if k != "matrix"},
                     ensure_ascii=False, indent=2))
    print("rho =", r["rho"], "M =", r["matrix"])
