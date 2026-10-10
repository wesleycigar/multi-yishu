#!/usr/bin/env python3
"""
木雷易术引擎 - 断卦规则库（详细版）
源自《增删卜易》《卜筮正宗》核心法则
"""
from liuyao_engine import *
from liuyao_paipan import najia_for_gua, _LOOKUP_NEI_WAI, get_gua_by_name
try:
    from gua_trace import gua_trace   # 典籍溯源（卦辞/爻辞）
except Exception:
    gua_trace = None


# ========== 64卦卦辞简释 ==========
GUA_CI = {
    "乾为天": "刚健中正，自强不息，元亨利贞",
    "坤为地": "厚德载物，柔顺包容，先迷后得",
    "水雷屯": "初创艰难，万事开头难，宜守正待时",
    "山水蒙": "蒙昧初开，需启蒙学习，虚心求教",
    "水天需": "等待时机，饮食宴乐，不急不躁",
    "天水讼": "争讼是非，谨慎息事，勿与人争",
    "地水师": "兴师动众，需纪律严明，正道而行",
    "水地比": "亲密辅佐，团结众人，择善而从",
    "风天小畜": "小有积蓄，力量未足，待时而动",
    "天泽履": "如履虎尾，谨慎行事，终无大碍",
    "地天泰": "天地交泰，通泰顺遂，吉祥之象",
    "天地否": "天地不交，闭塞不通，君子俭德辟难",
    "天火同人": "与人和同，同心协力，可成大事",
    "火天大有": "大有所获，富有的象，顺天休命",
    "地山谦": "谦谦君子，卑以自牧，谦尊而光",
    "雷地豫": "安乐愉悦，顺时而动，利建侯行师",
    "泽雷随": "随顺时势，随机应变，出门有功",
    "山风蛊": "整饬腐败，革故鼎新，先甲后甲",
    "地泽临": "居高临下，阳气渐长，元亨利贞",
    "风地观": "观察审视，静观其变，观我生进退",
    "火雷噬嗑": "咬合障碍，排除阻碍，利用狱",
    "山火贲": "文饰装饰，粉饰表面，白贲无咎",
    "山地剥": "剥落衰败，阴盛阳衰，顺而止之",
    "地雷复": "一阳来复，否极泰来，反复其道",
    "天雷无妄": "无妄之灾，顺其自然，勿有所往",
    "山天大畜": "大积蓄，厚德载物，利贞不家食",
    "山雷颐": "颐养之道，慎言语节饮食，自求口实",
    "泽风大过": "大为过越，栋梁弯曲，独立不惧",
    "坎为水": "重重险陷，心孚维亨，行有尚",
    "离为火": "光明依附，利贞亨，畜牝牛吉",
    "泽山咸": "感应交感，男女相感，亨利贞",
    "雷风恒": "恒久之道，久于其道，利贞",
    "天山遁": "退避隐居，远小人，不恶严",
    "雷天大壮": "大为壮盛，利贞，非礼弗履",
    "火地晋": "晋升前进，康侯用锡马蕃庶",
    "地火明夷": "光明受损，利艰贞，内文明外柔顺",
    "风火家人": "家庭伦理，利女贞，家人有严君",
    "火泽睽": "乖离不和，小事吉，二女同居志不同",
    "水山蹇": "艰难险阻，利西南不利东北，见大人",
    "雷水解": "解难纾困，利西南，无所往其来复吉",
    "山泽损": "减损下益上，惩忿窒欲，损而有孚",
    "风雷益": "损上益下，利有攸往，利涉大川",
    "泽天夬": "决断清除，扬于王庭，不利即戎",
    "天风姤": "不期而遇，女壮勿用取女",
    "泽地萃": "聚集汇合，王假有庙，利见大人",
    "地风升": "上升进阶，地中生木，升虚邑",
    "泽水困": "困穷窘迫，亨贞大人吉，有言不信",
    "水风井": "井养不穷，改邑不改井，无丧无得",
    "泽火革": "变革革命，巳日乃孚，元亨利贞悔亡",
    "火风鼎": "鼎新革故，鼎颠趾利出否，得妾以其子",
    "震为雷": "震动惊惧，震惊百里，不丧匕鬯",
    "艮为山": "抑止静止，艮其背不获其身，行其庭不见其人",
    "风山渐": "循序渐进，鸿雁于飞，女归吉利贞",
    "雷泽归妹": "婚嫁匹配，征凶无攸利",
    "雷火丰": "丰大盛大，王假之勿忧，宜日中",
    "火山旅": "旅行羁旅，小亨旅贞吉",
    "巽为风": "随顺渗入，小亨利有攸往利见大人",
    "兑为泽": "喜悦和悦，亨利贞，和兑吉",
    "风水涣": "涣散离散，亨王假有庙利涉大川",
    "水泽节": "节制节度，亨苦节不可贞",
    "风泽中孚": "中心诚信，豚鱼吉利涉大川利贞",
    "雷山小过": "小有过越，可小事不可大事，飞鸟遗音",
    "水火既济": "事成定局，亨小利贞初吉终乱",
    "火水未济": "事未完成，亨小狐汔济濡其尾",
}


# ========== 规则1：用神状态总评 ==========
def evaluate_yongshen_state(yong_yao_zhi, yong_yao_lq, yue_zhi, ri_zhi, is_dong, is_kong, is_shi):
    """综合判断用神爻的状态"""
    reasons = []
    score = 0
    
    # 1. 月建旺衰
    yue_status, yue_note = yao_wang_by_yue(yong_yao_zhi, yue_zhi)
    if yue_status == "旺":
        score += 2
        reasons.append(f"✅ 用神得月建{yue_zhi}旺相，根基牢固 (+2)")
    elif yue_status == "相":
        score += 1
        reasons.append(f"✅ 用神得月建生扶，有外援 (+1)")
    elif yue_status == "月破":
        score -= 3
        reasons.append(f"❌ 用神月破，动而无力，大凶 (-3)")
    elif yue_status == "死":
        score -= 2
        reasons.append(f"❌ 用神被月建克绝，根基虚弱 (-2)")
    elif yue_status == "囚":
        score -= 1
        reasons.append(f"⚠️ 用神居囚地，力量受限 (-1)")
    elif yue_status == "休":
        score -= 0.5
        reasons.append(f"⚠️ 用神休囚，气势不足 (-0.5)")
    
    # 2. 日辰作用
    ri_status, ri_note = yao_wang_by_ri(yong_yao_zhi, ri_zhi)
    if ri_status == "日扶":
        score += 1
        reasons.append(f"✅ 用神得日辰{ri_zhi}帮扶，当下有力 (+1)")
    elif ri_status == "日生":
        score += 1
        reasons.append(f"✅ 用神得日辰生扶，得人助 (+1)")
    elif ri_status == "日克":
        score -= 1
        reasons.append(f"❌ 用神被日辰{ri_zhi}克，当下受压制 (-1)")
    elif ri_status == "日冲":
        if score > 0:
            score += 0.5
            reasons.append(f"💡 用神旺而逢日冲=暗动，暗中发力，有意外助力 (+0.5)")
        else:
            score -= 2
            reasons.append(f"❌ 用神衰而逢日冲=日破，彻底无力，事难成 (-2)")
    
    # 3. 旬空
    if is_kong:
        if score > 1:
            reasons.append("💡 用神旺相而旬空，目前暂无实据，出空之日（约10天内）方见效")
        else:
            score -= 1
            reasons.append(f"❌ 用神休囚又逢旬空，虚而不实，事多空想 (-1)")
    
    # 4. 持世
    if is_shi:
        score += 1
        reasons.append(f"✅ 用神持世，事在我手，主动权在握 (+1)")
    
    # 5. 动爻
    if is_dong:
        reasons.append("🔄 用神发动，事在动中，必有变化")
        if score > 0:
            score += 0.5
            reasons.append(f"✅ 用神旺而动，事必可成，动而愈显 (+0.5)")
        else:
            score -= 0.5
            reasons.append(f"❌ 用神衰而动，动而难成，徒劳无功 (-0.5)")
    
    # 综合判断
    if score >= 2:
        result = "大吉"
        confidence = "高"
    elif score >= 0.5:
        result = "小吉"
        confidence = "中"
    elif score >= -0.5:
        result = "平"
        confidence = "中"
    elif score >= -2:
        result = "小凶"
        confidence = "中"
    else:
        result = "大凶"
        confidence = "高"
    
    return result, confidence, reasons, score


# ========== 规则2：原神忌神分析 ==========
def evaluate_yuanji_shen(gua_data, yong_lq, yuan_lq, ji_lq, yue_zhi, ri_zhi):
    """分析原神、忌神对用神的影响"""
    reasons = []
    
    yuan_yaos = [y for y in gua_data if y["六亲"] == yuan_lq]
    ji_yaos = [y for y in gua_data if y["六亲"] == ji_lq]
    
    # 原神
    if yuan_yaos:
        yuan_yao = yuan_yaos[0]
        reasons.append(f"【原神】{yuan_lq}：第{'初二三四五上'[yuan_yao['位置']-1]}爻 {yuan_yao['天干']}{yuan_yao['地支']}")
        if yuan_yao["动"]:
            yue_s, _ = yao_wang_by_yue(yuan_yao["地支"], yue_zhi)
            if yue_s in ["旺", "相"]:
                reasons.append(f"  ✅ 原神发动且旺相，源源不断生用神，事有后援")
            else:
                reasons.append(f"  ⚠️ 原神发动但休囚，生用之力有限，后援不足")
        else:
            reasons.append(f"  原神安静，暂无明显助力")
    else:
        reasons.append(f"【原神】卦中无{yuan_lq}爻，生用神之力不足")
    
    # 忌神
    if ji_yaos:
        ji_yao = ji_yaos[0]
        reasons.append(f"\n【忌神】{ji_lq}：第{'初二三四五上'[ji_yao['位置']-1]}爻 {ji_yao['天干']}{ji_yao['地支']}")
        if ji_yao["动"]:
            yue_s, _ = yao_wang_by_yue(ji_yao["地支"], yue_zhi)
            if yue_s in ["旺", "相"]:
                reasons.append(f"  ❌ 忌神发动且旺相，直克用神，是最大阻碍！")
            else:
                reasons.append(f"  ⚠️ 忌神发动但休囚，虽有阻碍但力量有限")
        else:
            reasons.append(f"  忌神安静，暂无明显阻碍")
    else:
        reasons.append(f"\n【忌神】卦中无{ji_lq}爻，无明显克制之力")
    
    return reasons


# ========== 规则3：世应分析 ==========
def evaluate_shiying(gua_data, shi_yao_pos, ying_yao_pos, question_type):
    """分析世爻应爻状态"""
    reasons = []
    
    shi_yao = next((y for y in gua_data if y["位置"] == shi_yao_pos), None)
    ying_yao = next((y for y in gua_data if y["位置"] == ying_yao_pos), None)
    
    if shi_yao:
        reasons.append(f"【世爻（我）】第{'初二三四五上'[shi_yao_pos-1]}爻 {shi_yao['六亲']} {shi_yao['天干']}{shi_yao['地支']}")
        reasons.append(f"  月建: {shi_yao['月建']}  日辰: {shi_yao['日辰']}")
        if shi_yao["动"]:
            reasons.append(f"  🔄 世爻发动：我心已定，主动求变，或事情有变动")
        else:
            reasons.append(f"  世爻安静：我心未定，或被动等待")
    
    if ying_yao:
        reasons.append(f"\n【应爻（事/对方）】第{'初二三四五上'[ying_yao_pos-1]}爻 {ying_yao['六亲']} {ying_yao['天干']}{ying_yao['地支']}")
        reasons.append(f"  月建: {ying_yao['月建']}  日辰: {ying_yao['日辰']}")
        if ying_yao["动"]:
            reasons.append(f"  🔄 应爻发动：对方/事情有变化，事出主动")
    
    # 世应生克关系
    if shi_yao and ying_yao:
        shi_wx = DIZHI[shi_yao["地支"]]["五行"]
        ying_wx = DIZHI[ying_yao["地支"]]["五行"]
        if shi_wx == ying_wx:
            reasons.append(f"\n  💡 世应比和：我与事/对方同心协力，顺利")
        elif WUXING_SHENG.get(shi_wx) == ying_wx:
            reasons.append(f"\n  💡 世生应：我付出多，主动迁就对方/事情")
        elif WUXING_SHENG.get(ying_wx) == shi_wx:
            reasons.append(f"  💡 应生世：对方/事情生我，有贵人相助")
        elif WUXING_KE.get(shi_wx) == ying_wx:
            reasons.append(f"  ⚠️ 世克应：我能掌控局面，但较费力")
        elif WUXING_KE.get(ying_wx) == shi_wx:
            reasons.append(f"  ❌ 应克世：对方/事情克我，被动受制约")
    
    return reasons


# ========== 规则4：动爻详解 ==========
def analyze_dong_yao(gua_data, dong_yao_list):
    """逐个分析动爻的含义"""
    reasons = []
    
    if not dong_yao_list:
        reasons.append("静卦，事情发展平稳，无大变动")
        return reasons
    
    reasons.append(f"共{len(dong_yao_list)}个动爻：")
    for pos in dong_yao_list:
        yao = next((y for y in gua_data if y["位置"] == pos), None)
        if yao:
            pos_name = "初二三四五上"[pos-1] + "爻"
            reasons.append(f"\n  【{pos_name}】{yao['六亲']} {yao['天干']}{yao['地支']}")
            reasons.append(f"    月建: {yao['月建']}  日辰: {yao['日辰']}")
            if yao["空"]:
                reasons.append(f"    ⚠️ 逢旬空，此动暂时无力，出空方应")
    
    return reasons


# ========== 规则5：应期推断 ==========
def predict_yingqi(yong_yao_zhi, is_dong, yue_status, is_kong):
    """推断应期"""
    if is_kong:
        return f"用神旬空，目前暂无实果，出空之日（约10天内）或出空之月应事"
    if is_dong:
        return f"动爻主事，应期较快，约在{yong_yao_zhi}日或冲{yong_yao_zhi}之日（约1-2周内）"
    if "旺" in yue_status:
        return f"用神旺相，事已成局，快则{yong_yao_zhi}日，慢则{yong_yao_zhi}月（约1-3个月）"
    else:
        return f"用神休囚，需待旺相之时，约需3-6个月方有结果"


# ========== 规则6：行动建议 ==========
def give_advice(result, yong_lq, question_type, score):
    """根据结论给出具体行动建议"""
    advice = []
    
    if "大吉" in result:
        advice.append("1. 时机成熟，可大胆推进，抓住机遇")
        advice.append("2. 乘胜追击，扩大成果")
    elif "小吉" in result:
        advice.append("1. 谨慎推进，稳中求进")
        advice.append("2. 有小成，但不可贪多")
    elif "平" in result:
        advice.append("1. 平平之象，宜守不宜攻")
        advice.append("2. 静待时机，不可轻举妄动")
    elif "小凶" in result:
        advice.append("1. 小心行事，避免冒险")
        advice.append("2. 多听取他人意见，勿独断专行")
        advice.append("3. 事情易有波折，需有心理准备")
    else:
        advice.append("1. 大事不宜，暂缓推进")
        advice.append("2. 保守为上，切勿强出头")
        advice.append("3. 注意防范风险，避免损失")
    
    # 针对不同占问的具体建议
    if question_type == "财运":
        if score > 0:
            advice.append("💡 求财可得，但需见好就收，不可贪心")
        else:
            advice.append("💡 财运不佳，不宜投资借贷，守成为上")
    elif question_type == "事业":
        if score > 0:
            advice.append("💡 事业有晋升之机，可主动争取")
        else:
            advice.append("💡 事业多阻碍，宜埋头做事，勿争名利")
    elif question_type == "感情":
        if score > 0:
            advice.append("💡 感情顺遂，可主动推进关系")
        else:
            advice.append("💡 感情多波折，需多沟通包容")
    
    return advice


# ========== 综合断卦报告 ==========
def full_duangua(ben_gua_name, dong_yao_list, ri_gan, ri_zhi, yue_zhi, question_type="财运", gender="男"):
    """完整断卦流程"""
    lines = []
    lines.append("=" * 60)
    lines.append("🌳 木雷易术引擎 · 详细断卦报告")
    lines.append("=" * 60)
    
    # 1. 基本信息
    info = get_gua_by_name(ben_gua_name)
    lines.append(f"\n📋 【基本信息】")
    lines.append(f"  本卦：{ben_gua_name}（{info['卦宫']}宫{info['宫五行']}）")
    if dong_yao_list:
        bian = bian_gua(ben_gua_name, dong_yao_list)
        lines.append(f"  动爻：第{','.join(map(str, dong_yao_list))}爻动")
        lines.append(f"  变卦：{bian}")
    else:
        lines.append(f"  静卦（无动爻，事体平稳）")
    lines.append(f"  月建：{yue_zhi}  日辰：{ri_gan}{ri_zhi}")
    
    kong1, kong2 = get_xunkong(ri_gan + ri_zhi)
    lines.append(f"  旬空：{kong1}{kong2}")
    
    # 2. 卦辞释义
    gua_ci = GUA_CI.get(ben_gua_name, "")
    if gua_ci:
        lines.append(f"\n📖 【卦意】{ben_gua_name}：{gua_ci}")
    
    # 3. 六爻排盘
    gong_wx = info["宫五行"]
    nei, wai = _LOOKUP_NEI_WAI[ben_gua_name]
    gua = najia_for_gua(nei, wai)
    
    gua_data = []
    lines.append(f"\n🎴 【六爻排盘】")
    lines.append(f"  {'爻位':<6}{'干支':<8}{'六亲':<6}{'月建':<6}{'日辰':<6}{'标记':<8}")
    lines.append(f"  {'-'*50}")
    
    for i, (pos, zhi, gan) in enumerate(gua):
        zhi_wx = DIZHI[zhi]["五行"]
        lq = get_liuqin(gong_wx, zhi_wx)
        yue_s, _ = yao_wang_by_yue(zhi, yue_zhi)
        ri_s, _ = yao_wang_by_ri(zhi, ri_zhi)
        is_kong = zhi in [kong1, kong2]
        is_dong = pos in dong_yao_list
        is_shi = pos == info["世爻"]
        is_ying = pos == info["应爻"]
        
        marker = ""
        if is_dong: marker += "动"
        if is_shi: marker += "世"
        if is_ying: marker += "应"
        
        gua_data.append({
            "位置": pos, "地支": zhi, "天干": gan, "六亲": lq,
            "月建": yue_s, "日辰": ri_s, "空": is_kong,
            "动": is_dong, "世": is_shi, "应": is_ying,
        })
        
        kong_mark = "空" if is_kong else ""
        lines.append(
            f"  {'初二三四五上'[pos-1]+'爻':<6}"
            f"{gan+zhi:<8}"
            f"{lq:<6}"
            f"{yue_s:<6}"
            f"{ri_s:<6}"
            f"{marker+kong_mark:<8}"
        )
    
    # 4. 用神分析
    yong_lq = select_yongshen(question_type, gender)
    shen_rel = get_shen_relations(yong_lq)
    lines.append(f"\n🎯 【用神分析】")
    lines.append(f"  占问：{question_type}（{'男' if gender!='女' else '女'}占）")
    lines.append(f"  用神：{yong_lq}")
    lines.append(f"  原神（生用神）：{shen_rel['原神']}  忌神（克用神）：{shen_rel['忌神']}  仇神（生忌神）：{shen_rel['仇神']}")
    
    yong_yaos = [y for y in gua_data if y["六亲"] == yong_lq]
    if not yong_yaos:
        # 用神不上卦 → 从本宫八纯卦寻伏神（纳甲本宫卦对应爻位）
        lines.append(f"  ⚠️ 用神不上卦，需寻伏神")
        ben_gong = info["卦宫"]
        # 本宫八纯卦的纳甲
        _chun_gua = ben_gong + "为" + {"乾":"天","坤":"地","震":"雷","巽":"风","坎":"水","离":"火","艮":"山","兑":"泽"}[ben_gong]
        _chun_nei = _LOOKUP_NEI_WAI.get(_chun_gua)
        if _chun_nei:
            _chun_yaos = najia_for_gua(_chun_nei[0], _chun_nei[1])
            # 在本宫卦里找用神六亲的爻
            yong_yao = None
            for pos, zhi, gan in _chun_yaos:
                zhi_wx = DIZHI[zhi]["五行"]
                lq = get_liuqin(gong_wx, zhi_wx)
                if lq == yong_lq:
                    yong_yao = {"位置": pos, "地支": zhi, "天干": gan, "六亲": lq, "伏神": True}
                    break
            if yong_yao:
                lines.append(f"  🔍 伏神（{yong_lq}）：伏于本宫卦第{'初二三四五上'[yong_yao['位置']-1]}爻 {yong_yao['天干']}{yong_yao['地支']}，当用神在卦中不出时取此爻断之")
            else:
                yong_yao = {"位置": 2, "地支": gua[2][1], "天干": gua[2][2], "六亲": yong_lq, "伏神": True}
                lines.append(f"  本宫卦亦无{yong_lq}，暂以卦中中爻代参")
        else:
            yong_yao = {"位置": 2, "地支": gua[2][1], "天干": gua[2][2], "六亲": yong_lq, "伏神": True}
            lines.append(f"  本宫卦未定，暂以中爻代参")
        # 补全伏神爻在卦内的旺衰状态字段（用对应位置占位分析）
        _by = gua_data[yong_yao["位置"]-1]
        yong_yao["月建"] = _by["月建"]; yong_yao["日辰"] = _by["日辰"]
        yong_yao["空"] = _by["空"]; yong_yao["动"] = False; yong_yao["世"] = False; yong_yao["应"] = False
    else:
        yong_yao = yong_yaos[0]
        lines.append(f"  用神爻位：第{'初二三四五上'[yong_yao['位置']-1]}爻 {yong_yao['天干']}{yong_yao['地支']}")
    
    # 5. 用神状态
    lines.append(f"\n📊 【用神状态评分】")
    result, confidence, reasons, score = evaluate_yongshen_state(
        yong_yao["地支"], yong_yao["六亲"],
        yue_zhi, ri_zhi,
        yong_yao["动"], yong_yao["空"], yong_yao["世"]
    )
    for r in reasons:
        lines.append(f"  {r}")
    lines.append(f"  总分：{score:+.1f}")
    
    # 6. 原神忌神
    lines.append(f"\n⚖️ 【原神忌神分析】")
    yj_reasons = evaluate_yuanji_shen(
        gua_data, yong_lq,
        shen_rel["原神"], shen_rel["忌神"],
        yue_zhi, ri_zhi
    )
    for r in yj_reasons:
        lines.append(f"  {r}")
    
    # 7. 世应分析
    lines.append(f"\n👥 【世应关系】")
    sy_reasons = evaluate_shiying(gua_data, info["世爻"], info["应爻"], question_type)
    for r in sy_reasons:
        lines.append(f"  {r}")
    
    # 8. 动爻详解
    lines.append(f"\n🔄 【动爻详解】")
    dy_reasons = analyze_dong_yao(gua_data, dong_yao_list)
    for r in dy_reasons:
        lines.append(f"  {r}")
    
    # 9. 结论与建议
    lines.append(f"\n{'='*60}")
    lines.append(f"🏆 【最终结论】{result}（置信度：{confidence}）")
    lines.append(f"📅 【应期推断】{predict_yingqi(yong_yao['地支'], yong_yao['动'], yong_yao['月建'], yong_yao['空'])}")
    
    lines.append(f"\n💡 【行动建议】")
    advice = give_advice(result, yong_lq, question_type, score)
    for a in advice:
        lines.append(f"  {a}")
    
    lines.append(f"\n{'='*60}")
    lines.append(f"⚠️ 本报告由木雷易术引擎生成，仅供参考，事在人为")
    lines.append(f"{'='*60}")

    # 10. 典籍溯源（卦辞/爻辞）
    if gua_trace:
        trace = gua_trace(ben_gua_name, dong_yao_list, nei, wai)
        if trace:
            lines.append(f"\n📜 【典籍溯源】（王弼《周易注》）")
            lines.append(trace)

    # 11. 语料佐证 + 当代白话解读（五段式补全）
    try:
        from analysis_enhance import corpus_evidence, baihua
        lines += corpus_evidence(f"{question_type} 六爻 {ben_gua_name} 用神 {yong_lq}", k=1)
        lines += baihua("六爻", f"{result}。用神{yong_lq}，{advice[0] if advice else ''}")
    except Exception:
        pass

    return "\n".join(lines)


if __name__ == "__main__":
    print(full_duangua("火天大有", [3], "甲", "子", "申", "财运"))
