#!/usr/bin/env python3
"""
木雷易术引擎 - 个人综合分析模块
望闻问切：先收集个人信息，再综合解读
"""
from bazi_paipan import paipan_bazi
from qigua import number_qigua
from meihua import meihua_duangua
from qimen import qimen_solve_problem
from fengshui import fengshui_advice


_WX_TONE = {
    "木": "生发之运，利学业、文教、医疗、农林，宜生长进取",
    "火": "声名之运，利文化、互联网、能源、品牌，宜张扬声量",
    "土": "积累之运，利地产、基建、实业，宜厚积稳进",
    "金": "变革之运，利金融、金属、机械、权威，宜果决审慎",
    "水": "流动之运，利贸易、物流、智谋，宜蓄势待时",
}
_CUR_YEAR = 2026


def _dayun_timeline(year, month, day, hour):
    """按年份返回真实大运列表 [{gz, gwx, zwx, sy, ey, age}]（含当前/未来大运）"""
    from lunar_python import Solar
    from engine_core import TIANGAN, DIZHI
    s = Solar.fromYmdHms(year, month, day, hour, 0, 0)
    ec = s.getLunar().getEightChar()
    yun = ec.getYun(1)
    out = []
    for d in yun.getDaYun():
        gz = d.getGanZhi()
        if not gz:
            continue
        out.append({"gz": gz,
                    "gwx": TIANGAN[gz[0]]["五行"],
                    "zwx": DIZHI[gz[1]]["五行"],
                    "sy": d.getStartYear(), "ey": d.getEndYear(),
                    "age": d.getStartAge()})
    return out


def _build_past_now_future(year, month, day, hour, day_master_wx="", strength=""):
    """用真实大运+流年生成『过去·现在·未来』三段时间轴文本"""
    L = []
    try:
        days = _dayun_timeline(year, month, day, hour)
        if not days:
            raise ValueError("无大运数据")
        cur = next((d for d in days if d["sy"] <= _CUR_YEAR <= d["ey"]), days[-1])
        past = [d for d in days if d["ey"] < cur["sy"]][-3:]
        future = [d for d in days if d["sy"] > cur["ey"]][:2]
    except Exception as e:
        return ["  （大运推算暂不可用，以下为概览）",
                "  【过去】奠基·积累：过往经历塑造了现在的你，成败皆为经验。",
                "  【现在】机遇与选择：时机正在成熟，宜明确方向、主动行动。",
                "  【未来】上行趋势：把握好当前，未来几年持续向好。"]

    # 当前流年干支
    try:
        from lunar_python import Solar
        ygz = Solar.fromYmd(_CUR_YEAR, 1, 1).getLunar().getYearInGanZhiExact()
    except Exception:
        ygz = "丙午"

    # 过去
    L.append(f"  【过去】已历大运：")
    if past:
        for d in past:
            tone = _WX_TONE.get(d["gwx"], "平稳之运")
            L.append(f"    • {d['gz']}运（{d['sy']}-{d['ey']}，约{d['age']}岁起）：{tone}")
        L.append(f"    • 已走之路已成铺垫，成败皆化为经验与底力")
    else:
        L.append(f"    • 尚在起步，根基未深，宜稳扎稳打")

    # 现在
    L.append(f"\n  【现在】当前大运·{cur['gz']}（{cur['sy']}-{cur['ey']}，约{cur['age']}岁起）：")
    L.append(f"    • 本运主题：{_WX_TONE.get(cur['gwx'], '平稳')}")
    L.append(f"    • 值年流年：{ygz}年（{_CUR_YEAR}），当下正值本运之{'尾声' if cur['ey']==_CUR_YEAR else '中段'}，宜{'收束转承、为下一运布局' if cur['ey']==_CUR_YEAR else '乘势而上'}")
    if day_master_wx:
        if strength in ("身强", "偏强"):
            L.append(f"    • 你身{strength}，本运喜走财官食（克泄耗），{cur['gwx']}于你{'得助力' if cur['gwx'] in ('财','官','食') else '宜顺势取用'}")
        elif strength in ("身弱", "偏弱"):
            L.append(f"    • 你身{strength}，本运喜走印比（生扶），遇{cur['gwx']}之印比则身旺运开")

    # 未来
    L.append(f"\n  【未来】后续大运：")
    if future:
        for d in future:
            L.append(f"    • {d['gz']}运（{d['sy']}-{d['ey']}，约{d['age']}岁起）：{_WX_TONE.get(d['gwx'], '平稳')}")
        L.append(f"    • 提前布局：向本运喜用五行之行业与方位倾斜，事半功倍")
    else:
        L.append(f"    • 后运未可尽推，宜守正待时、修己以应")
    return L


def personal_analysis(bazi_year, bazi_month, bazi_day, bazi_hour, 
                      recent_goal, person_status, problem_type,
                      gender="男", rank="",
                      num1=None, num2=None):
    """
    个人综合分析
    输入：八字 + 性别 + 家中排行 + 近期主求 + 人事状况 + 问题类型 + 起卦数字（可选）
    输出：全方位解读报告（含三元九运·九紫离火位分）
    """
    import random
    
    # 如果没给数字，随机生成两个（代表"心动起卦"）
    if num1 is None:
        num1 = random.randint(1, 99)
    if num2 is None:
        num2 = random.randint(1, 99)
    
    lines = []
    lines.append("=" * 60)
    lines.append("🌳 木雷易术引擎 · 个人综合分析报告")
    lines.append("=" * 60)
    
    # ===== 第一部分：八字命盘 =====
    lines.append(f"\n📋 【第一部分：八字命盘】")
    try:
        bazi_report = paipan_bazi(bazi_year, bazi_month, bazi_day, bazi_hour, gender)
        lines.append(bazi_report)
        
        # 提取日主五行（真正从八字日干取，不再写死）
        from lunar_python import Solar
        from engine_core import TIANGAN
        _s = Solar.fromYmdHms(bazi_year, bazi_month, bazi_day, bazi_hour, 0, 0)
        _day_gan = _s.getLunar().getEightChar().getDay()[0]
        day_master_wx = TIANGAN[_day_gan]["五行"]
    except Exception as e:
        lines.append(f"  八字排盘出错：{e}")
        day_master_wx = ""
    
    personal_info = {"日主五行": day_master_wx}
    
    # ===== 三元九运 · 九紫离火位分 =====
    lines.append(f"\n{'='*60}")
    lines.append(f"🔴 【三元九运 · 九紫离火位分】")
    _wei = rank or "独生"
    _wei_map = {
        "长男": "震卦 · 长男，位东方，主行动开创",
        "中男": "坎卦 · 中男，位北方，主险中求进",
        "少男": "艮卦 · 少男，位东北，主止而蓄势",
        "长女": "巽卦 · 长女，位东南，主顺势柔进",
        "中女": "离卦 · 中女，位南方，主文明发光",
        "少女": "兑卦 · 少女，位西方，主悦而和合",
        "独生": "独子独女，兼诸卦之位，随命盘而定",
        "其他": "位分未明，随命盘而定",
    }
    _wei_desc = _wei_map.get(_wei, _wei_map["其他"])
    if _wei == "中女":
        _heng = ("九紫离火正当运，离为中女，你正处当运之位——运势主升，利于展示才华与光明事业，"
                 "南方、红色、火性行业（文化、美妆、互联网、能源）皆可得力。")
    elif _wei in ("长女", "少女"):
        _heng = ("九紫离火为当运，你属巽/兑之姊妹位，得离火相生而承运，利于学习、表达与和合人际。")
    elif _wei == "长男":
        _heng = ("离火当运，木火相生，你属震木长男，宜借势而动，利于开创与新兴行业。")
    elif _wei == "中男":
        _heng = ("你属坎水中男，水火既济；九运火旺之时，宜以水调火、以静制动，稳健守成反能得利。")
    elif _wei == "少男":
        _heng = ("你属艮土少男，土晦火而火生土；九运中宜深耕厚积、以稳求成，忌冒进。")
    else:
        _heng = ("位分未明，宜以八字日主五行与大运为主，结合当下离火当运，取火土相宜之方。")
    lines.append(f"\n  你的位分：{_wei} —— {_wei_desc}")
    lines.append(f"  当前正值下元九运（2024—2043），九紫离火，主文明、智慧、艺术与网络之象。")
    lines.append(f"  运势研判：{_heng}")
    lines.append(f"  参考方向：南方 / 属火行业 / 红色系，主发光发热、利名而重名；忌心浮气躁、过度扩张。")
    
    # ===== 第二部分：梅花易数起卦看气运 =====
    lines.append(f"\n{'='*60}")
    lines.append(f"🌸 【第二部分：梅花易数看气运】")
    lines.append(f"  起卦数字：{num1}, {num2}")
    try:
        meihua_result = meihua_duangua(num1, num2, bazi_hour, "气运", personal_info)
        # 提取关键结论部分
        lines.append(meihua_result)
    except Exception as e:
        lines.append(f"  梅花起卦出错：{e}")
    
    # ===== 第三部分：近期运势 =====
    lines.append(f"\n{'='*60}")
    lines.append(f"📈 【第三部分：近期运势】")
    lines.append(f"  近期主求：{recent_goal}")
    lines.append(f"  当前人事状况：{person_status}")
    
    lines.append(f"\n  【当前状态判断】")
    if "财运" in problem_type:
        lines.append(f"    • 重点关注：求财机会、收入变化、投资风险")
        lines.append(f"    • 注意：勿贪多，见好就收")
    elif "事业" in problem_type:
        lines.append(f"    • 重点关注：工作变动、晋升机会、人际关系")
        lines.append(f"    • 注意：少说多做，积累实力")
    elif "感情" in problem_type:
        lines.append(f"    • 重点关注：沟通方式、误会化解、双方需求")
        lines.append(f"    • 注意：多包容，少计较")
    
    # ===== 第四部分：过去现在未来（按真实大运+流年具体展开） =====
    lines.append(f"\n{'='*60}")
    lines.append(f"⏳ 【第四部分：过去·现在·未来（按大运流年）】")
    # 身强弱（用于喜用提示）
    _strength = ""
    try:
        from bazi_paipan import analyze_strength_xiyong
        from lunar_python import Solar
        from engine_core import TIANGAN
        _s = Solar.fromYmdHms(bazi_year, bazi_month, bazi_day, bazi_hour, 0, 0)
        _dg = _s.getLunar().getEightChar().getDay()[0]
        _ec = _s.getLunar().getEightChar()
        _strength = analyze_strength_xiyong(_ec, _dg)[0]
    except Exception:
        pass
    for ln in _build_past_now_future(bazi_year, bazi_month, bazi_day, bazi_hour, day_master_wx, _strength):
        lines.append(ln)
    
    # ===== 第五部分：奇门解法 =====
    lines.append(f"\n{'='*60}")
    lines.append(f"🔍 【第五部分：奇门遁甲找解法】")
    try:
        qimen_result = qimen_solve_problem(problem_type, personal_info)
        lines.append(qimen_result)
    except Exception as e:
        lines.append(f"  奇门分析出错：{e}")
    
    # ===== 第六部分：生活建议 =====
    lines.append(f"\n{'='*60}")
    lines.append(f"💡 【第六部分：全方位生活建议】")
    
    lines.append(f"\n  【待人处事】")
    lines.append(f"    • 多听少说，了解对方真实需求")
    lines.append(f"    • 对贵人要主动感恩，对小人要敬而远之")
    
    lines.append(f"\n  【理财】")
    lines.append(f"    • 三分法：日常开销 / 储蓄 / 投资")
    lines.append(f"    • 勿投机，慢就是快")
    
    lines.append(f"\n  【买卖交易】")
    lines.append(f"    • 谈判选在生门方位（东北方）")
    lines.append(f"    • 签约选在上午，避开下午")
    
    lines.append(f"\n  【合作伙伴】")
    lines.append(f"    • 选八字五行互补的人合作")
    lines.append(f"    • 三观一致比能力强更重要")
    
    # ===== 第七部分：风水布局 =====
    lines.append(f"\n{'='*60}")
    lines.append(f"🏠 【第七部分：风水布局建议】")
    try:
        fs_result = fengshui_advice("办公室")
        lines.append(fs_result)
    except Exception as e:
        lines.append(f"  风水分析出错：{e}")
    
    # ===== 第八部分：时代大运（M：结合皇极经世·个人在午会大运中的位置）=====
    lines.append(f"\n{'='*60}")
    lines.append(f"🌍 【第八部分：时代大运与个人】")
    lines.append(f"  2026年（丙午年）整体运势：")
    lines.append(f"    • 火旺之年，互联网、能源、文化行业较旺")
    lines.append(f"    • 经济转型期，稳字当头")
    try:
        from huangji import huangji_analysis
        hg = huangji_analysis(2026, day_master_wx, "大运").split("\n")
        lines.append(f"\n  ── 皇极经世·个人与时代大运 ──")
        for ln in hg:
            s = ln.strip()
            if s.startswith(("📜","🧭","📅","🏆","🧑","💡")):
                lines.append("   " + s)
    except Exception as e:
        lines.append(f"  （国运联动计算：{e}）")
    
    lines.append(f"\n  【如何把握时代机遇】")
    lines.append(f"    1. 顺时而为：大环境向上时积极进取")
    lines.append(f"    2. 借势而起：站在行业风口上")
    lines.append(f"    3. 修己安人：提升自己永远是最稳的投资")
    
    lines.append(f"\n{'='*60}")
    lines.append(f"⚠️ 以上为综合分析报告，仅供参考，事在人为")
    lines.append(f"{'='*60}")
    
    return "\n".join(lines)


def help_others_analysis(my_year, my_month, my_day, my_hour,
                        other_year, other_month, other_day, other_hour,
                        look_type="姻缘"):
    """
    帮他人看：输入两人八字，看姻缘/健康/财运
    look_type: 姻缘 / 健康 / 财运
    """
    lines = []
    lines.append("=" * 60)
    lines.append("🌳 木雷易术引擎 · 帮他人看分析")
    lines.append("=" * 60)
    
    # ===== 两人八字 =====
    lines.append(f"\n📋 【两人八字】")
    lines.append(f"\n  【你的八字】")
    try:
        my_bazi = paipan_bazi(my_year, my_month, my_day, my_hour, "男")
        lines.append(my_bazi)
    except Exception as e:
        lines.append(f"  排盘出错：{e}")
    
    lines.append(f"\n  【对方八字】")
    try:
        other_bazi = paipan_bazi(other_year, other_month, other_day, other_hour, "女")
        lines.append(other_bazi)
    except Exception as e:
        lines.append(f"  排盘出错：{e}")
    
    # ===== 姻缘分析 =====
    if look_type == "姻缘":
        lines.append(f"\n{'='*60}")
        lines.append(f"💕 【姻缘合盘分析】")
        lines.append(f"\n  【五行互补】")
        lines.append(f"    • 两人五行互补则长久，相克则易吵架")
        lines.append(f"    • 你的日主五行与对方日主五行相生相合最佳")
        
        lines.append(f"\n  【性格匹配】")
        lines.append(f"    • 一个外向一个内向，互补型最好")
        lines.append(f"    • 两个都强势则易冲突")
        
        lines.append(f"\n  【建议】")
        lines.append(f"    1. 多沟通，勿猜心思")
        lines.append(f"    2. 吵架别过夜，床头吵床尾和")
        lines.append(f"    3. 互相包容，多看对方优点")
    
    # ===== 健康分析 =====
    elif look_type == "健康":
        lines.append(f"\n{'='*60}")
        lines.append(f"🏥 【健康分析】")
        lines.append(f"\n  【五行对应身体】")
        lines.append(f"    • 木：肝胆、筋骨、眼睛")
        lines.append(f"    • 火：心脏、小肠、血压、视力")
        lines.append(f"    • 土：脾胃、消化系统、皮肤")
        lines.append(f"    • 金：肺、呼吸道、大肠、皮肤")
        lines.append(f"    • 水：肾、膀胱、耳朵、泌尿")
        
        lines.append(f"\n  【健康建议】")
        lines.append(f"    1. 五行弱的那个脏腑要重点保养")
        lines.append(f"    2. 少熬夜，早睡早起")
        lines.append(f"    3. 饮食清淡，多运动")
        lines.append(f"    4. 定期体检，早发现早治疗")
    
    # ===== 财运分析 =====
    elif look_type == "财运":
        lines.append(f"\n{'='*60}")
        lines.append(f"💰 【财运分析】")
        lines.append(f"\n  【财运格局】")
        lines.append(f"    • 八字财星旺：天生会赚钱")
        lines.append(f"    • 八字比劫旺：花钱大手大脚")
        lines.append(f"    • 八字官杀旺：靠工作赚钱，稳但不快")
        
        lines.append(f"\n  【理财建议】")
        lines.append(f"    1. 三分法：开销/储蓄/投资")
        lines.append(f"    2. 勿投机，慢就是快")
        lines.append(f"    3. 中年后财运更稳")
    
    lines.append(f"\n{'='*60}")
    lines.append(f"⚠️ 以上为分析报告，仅供参考")
    lines.append(f"{'='*60}")
    
    return "\n".join(lines)
    print(personal_analysis(
        1990, 5, 15, 10,
        "想换工作",
        "当前工作压力大，和同事关系一般",
        "事业工作",
        num1=3, num2=8
    ))
