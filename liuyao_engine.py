#!/usr/bin/env python3
"""
木雷易术引擎 - 六爻断卦核心
在排盘基础上，加动爻变卦、旺衰判断、用神选取、原神忌神分析
"""
from engine_core import *
from liuyao_paipan import _LOOKUP_NEI_WAI, GUA_TABLE, BAGONG, NAJIA, get_gua_by_name

# ========== 旺衰判断体系 ==========
# 月建对爻的作用
def yao_wang_by_yue(zhi, yue_zhi):
    """
    判断爻支在月建下的旺衰状态
    返回: (旺衰状态, 说明)
    旺衰等级: 旺(月建同五行)、相(月生)、休(月克)、囚(克月)、死(月月生我)
    以及特殊: 月破(爻支与月建相冲)
    """
    yue_wx = DIZHI[yue_zhi]["五行"]
    yao_wx = DIZHI[zhi]["五行"]
    
    # 六冲: 子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲
    LIUCHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
    
    if LIUCHONG.get(zhi) == yue_zhi:
        return "月破", f"{zhi}被月建{yue_zhi}冲，月破之爻，动而无力"
    
    if yao_wx == yue_wx:
        return "旺", f"{zhi}五行{yao_wx}与月建{yue_zhi}同气，旺相"
    
    # 月生爻 -> 相
    if WUXING_SHENG.get(yue_wx) == yao_wx:
        return "相", f"月建{yue_wx}生{yao_wx}，爻得月生，相气"
    
    # 爻生月 -> 休
    if WUXING_SHENG.get(yao_wx) == yue_wx:
        return "休", f"{yao_wx}生{yue_wx}，爻泄气，休囚"
    
    # 爻克月 -> 囚
    if WUXING_KE.get(yao_wx) == yue_wx:
        return "囚", f"{yao_wx}克{yue_wx}，爻克月，囚地"
    
    # 月克爻 -> 死
    if WUXING_KE.get(yue_wx) == yao_wx:
        return "死", f"月建{yue_wx}克{yao_wx}，爻受月克，死绝"
    
    return "?", "未知"


def yao_wang_by_ri(zhi, ri_zhi):
    """
    日辰对爻的作用
    特殊: 日冲(暗动/日破)、旬空
    """
    LIUCHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
                "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
    
    if LIUCHONG.get(zhi) == ri_zhi:
        # 旺相之爻遇日冲=暗动，休囚之爻遇日冲=日破
        return "日冲", f"{zhi}被日辰{ri_zhi}冲，旺则暗动，衰则日破"
    
    yue_wx = DIZHI[ri_zhi]["五行"]
    yao_wx = DIZHI[zhi]["五行"]
    
    if yao_wx == yue_wx:
        return "日扶", f"{zhi}得日辰{ri_zhi}同气帮扶"
    
    if WUXING_SHENG.get(yue_wx) == yao_wx:
        return "日生", f"日辰{ri_zhi}生{zhi}，爻得日生"
    
    if WUXING_KE.get(yue_wx) == yao_wx:
        return "日克", f"日辰{ri_zhi}克{zhi}，爻受日克"
    
    return "平", f"{zhi}与日辰{ri_zhi}无特殊关系"


# 旬空计算
XUNKONG_TABLE = {
    # 甲子旬: 戌亥空
    "甲子": ("戌", "亥"), "甲戌": ("申", "酉"), "甲申": ("午", "未"),
    "甲午": ("辰", "巳"), "甲辰": ("寅", "卯"), "甲寅": ("子", "丑"),
}

def get_xunkong(ri_ganzhi):
    """根据日干支求旬空"""
    gan = ri_ganzhi[0]
    zhi = ri_ganzhi[1]
    GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"
    ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"
    
    gan_idx = GAN_ORDER.index(gan)
    zhi_idx = ZHI_ORDER.index(zhi)
    
    # 旬首地支 = 日支 - 日干（甲子是(0,0)，差为0）
    # 例：乙丑(1,1) → 旬首地支 = 1-1 = 0 = 子 → 甲子旬
    xun_shou_zhi_idx = (zhi_idx - gan_idx) % 12
    xun_shou_zhi = ZHI_ORDER[xun_shou_zhi_idx]
    xun_shou = f"甲{xun_shou_zhi}"
    
    return XUNKONG_TABLE.get(xun_shou, ("?", "?"))


# ========== 用神选取 ==========
YONGSHEN_RULES = {
    # 占问类别: 对应六亲
    "财运": "妻财",
    "求财": "妻财",
    "生意": "妻财",
    "功名": "官鬼",
    "事业": "官鬼",
    "工作": "官鬼",
    "官职": "官鬼",
    "考试": "父母",
    "文书": "父母",
    "合同": "父母",
    "房屋": "父母",
    "车辆": "父母",
    "老人": "父母",
    "父亲": "父母",
    "母亲": "父母",
    "子女": "子孙",
    "儿子": "子孙",
    "女儿": "子孙",
    "下属": "子孙",
    "宠物": "子孙",
    "疾病": "官鬼",
    "健康": "官鬼",
    "婚姻": "妻财",  # 男占妻
    "感情": "妻财",
    "竞争对手": "兄弟",
    "兄弟朋友": "兄弟",
    "出行": "子孙",  # 出行看子孙，主解忧、平安
    "失物": "妻财",
    "官司": "官鬼",
    "诉讼": "官鬼",
}

def select_yongshen(question_type, gender="男"):
    """根据占问类别选取用神六亲。婚姻/感情：男占取妻财(妻)、女占取官鬼(夫)。"""
    if question_type in ("婚姻", "感情"):
        return "妻财" if gender != "女" else "官鬼"
    return YONGSHEN_RULES.get(question_type, "不确定")


# ========== 原神忌神仇神 ==========
def get_shen_relations(liuqin):
    """
    给定用神六亲，返回原神、忌神、仇神
    六亲五行: 兄弟(同我)、子孙(我生)、妻财(我克)、官鬼(克我)、父母(生我)
    """
    # 反推：六亲之间的生克关系
    # 相生环（前生后）：父母生兄弟、兄弟生子孙、子孙生妻财、妻财生官鬼、官鬼生父母
    SHENG_CHAIN = ["父母", "兄弟", "子孙", "妻财", "官鬼"]
    # 相克环（前克后）：官鬼克兄弟、兄弟克妻财、妻财克父母、父母克子孙、子孙克官鬼
    KE_CHAIN = ["官鬼", "兄弟", "妻财", "父母", "子孙"]

    # 如果用神不在列表里，返回默认值，不要崩溃
    if liuqin not in SHENG_CHAIN:
        return {
            "用神": "不确定",
            "原神": "不确定",
            "忌神": "不确定",
            "仇神": "不确定",
        }

    def sheng_of(lq):
        """生X者 = 相生环中X的前一位（前一个生后一个）"""
        idx = SHENG_CHAIN.index(lq)
        return SHENG_CHAIN[(idx - 1) % 5]

    def ke_of(lq):
        """克X者 = 相克环中X的前一位（前一个克后一个）"""
        idx = KE_CHAIN.index(lq)
        return KE_CHAIN[(idx - 1) % 5]

    return {
        "用神": liuqin,
        "原神": sheng_of(liuqin),   # 生用神者
        "忌神": ke_of(liuqin),      # 克用神者
        "仇神": sheng_of(ke_of(liuqin)),  # 生忌神者
    }


# ========== 动爻变卦（动态生成，不硬编码） ==========
# 八卦卦画（从下到上三爻）: 1=阳, 0=阴
BAGUA_HUA = {
    "乾": [1,1,1], "兑": [1,1,0], "离": [1,0,1], "震": [1,0,0],
    "巽": [0,1,1], "坎": [0,1,0], "艮": [0,0,1], "坤": [0,0,0],
}

def _build_64_gua_hua():
    """从内外卦组合动态生成64卦卦画表，从根本上杜绝硬编码错误"""
    result = {}
    for gua_name, (nei, wai) in _LOOKUP_NEI_WAI.items():
        hua = BAGUA_HUA[nei] + BAGUA_HUA[wai]  # 下卦三爻 + 上卦三爻
        result[gua_name] = hua
    return result

GUA_HUA = _build_64_gua_hua()
GUA_HUA_REV = {tuple(v): k for k, v in GUA_HUA.items()}

def bian_gua(ben_gua_name, dong_yao_list):
    """本卦有变爻，求变卦。dong_yao_list: 动爻位置列表(1-6)"""
    if ben_gua_name not in GUA_HUA:
        return None
    ben_hua = GUA_HUA[ben_gua_name][:]
    for yao in dong_yao_list:
        ben_hua[yao - 1] = 1 - ben_hua[yao - 1]
    return GUA_HUA_REV.get(tuple(ben_hua), "未知")


# ========== 综合断卦 ==========
def duan_gua(ben_gua_name, dong_yao_list, ri_gan, ri_zhi, yue_zhi, question_type="财运", gender="男"):
    """
    完整断卦流程
    """
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"木雷易术引擎 - 六爻断卦报告")
    lines.append(f"{'='*60}")
    
    # 1. 本卦信息
    info = get_gua_by_name(ben_gua_name)
    lines.append(f"\n【本卦】{ben_gua_name}")
    lines.append(f"  卦宫: {info['卦宫']}宫({info['宫五行']})  世爻:第{info['世爻']}爻  应爻:第{info['应爻']}爻")
    
    # 2. 动爻与变卦
    if dong_yao_list:
        bian = bian_gua(ben_gua_name, dong_yao_list)
        lines.append(f"\n【动爻】第{','.join(map(str, dong_yao_list))}爻动")
        lines.append(f"【变卦】{bian}")
    else:
        lines.append(f"\n【动爻】无动爻(静卦)")
        bian = None
    
    # 3. 月日建
    kong1, kong2 = get_xunkong(ri_gan + ri_zhi)
    lines.append(f"\n【月建】{yue_zhi}  【日辰】{ri_gan}{ri_zhi}  【旬空】{kong1}{kong2}")
    
    # 4. 用神选取
    yongshen_lq = select_yongshen(question_type, gender)
    shen_rel = get_shen_relations(yongshen_lq)
    lines.append(f"\n【占问】{question_type}")
    lines.append(f"  用神: {shen_rel['用神']}  原神: {shen_rel['原神']}  忌神: {shen_rel['忌神']}  仇神: {shen_rel['仇神']}")
    
    # 5. 逐爻分析
    lines.append(f"\n【逐爻分析】")
    lines.append(f"  {'爻位':<6}{'六亲':<6}{'月建':<8}{'日辰':<8}{'旬空':<6}{'动变':<8}")
    lines.append(f"  {'-'*50}")
    
    # 简化：列出六亲分布
    gong_wx = info["宫五行"]
    nei, wai = _LOOKUP_NEI_WAI[ben_gua_name]
    gua = None
    # 重新获取爻支
    from liuyao_paipan import najia_for_gua
    gua = najia_for_gua(nei, wai)
    
    for i, (pos, zhi, gan) in enumerate(gua):
        zhi_wx = DIZHI[zhi]["五行"]
        lq = get_liuqin(gong_wx, zhi_wx)
        
        yue_status, yue_note = yao_wang_by_yue(zhi, yue_zhi)
        ri_status, ri_note = yao_wang_by_ri(zhi, ri_zhi)
        is_kong = "空" if zhi in [kong1, kong2] else ""
        is_dong = "动" if pos in dong_yao_list else ""
        is_shi = "世" if pos == info["世爻"] else ""
        is_ying = "应" if pos == info["应爻"] else ""
        
        marker = is_dong + is_shi + is_ying
        
        lines.append(
            f"  {'初二三四五上'[pos-1]+'爻':<6}"
            f"{lq:<6}"
            f"{yue_status:<8}"
            f"{ri_status:<8}"
            f"{is_kong:<6}"
            f"{marker:<8}"
        )
    
    # 6. 初步判断
    lines.append(f"\n【初步判断逻辑】")
    lines.append(f"  1. 先找用神爻，看其在月日下的旺衰状态")
    lines.append(f"  2. 看原神是否发动生用，忌神是否发动克用")
    lines.append(f"  3. 用神旺相有生源则吉，休囚受克则凶")
    lines.append(f"  4. 动爻有变则看变爻对用神的作用")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试：占财运，火天大有卦，三爻动，甲子日丁卯月
    print(duan_gua("火天大有", [3], "甲", "子", "卯", "财运"))
    print("\n")
    
    # 测试：旬空
    print(f"甲子日旬空: {get_xunkong('甲子')}")
    print(f"甲寅日旬空: {get_xunkong('甲寅')}")
    
    # 测试：变卦
    print(f"\n乾为天初爻动 -> {bian_gua('乾为天', [1])}")
    print(f"乾为天二爻动 -> {bian_gua('乾为天', [2])}")
