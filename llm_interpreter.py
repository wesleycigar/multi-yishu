#!/usr/bin/env python3
"""
木雷易术引擎 - LLM自然语言解读层
把规则引擎的结构化结果，转成大师级的自然语言解读
"""
from duangua_rules import full_duangua


def _enhance_refs(structured, k=3):
    """按占问类别+卦名 检索相关典籍原文作佐证（可选，无索引时静默跳过）"""
    try:
        from vector_library import enhance
    except Exception:
        return []
    try:
        query = f"{structured['question_type']} {structured['ben_gua']} {structured['yongshen']}"
        return enhance(query, k=k)
    except Exception:
        return []


def get_structured_result(ben_gua, dong_list, ri_gan, ri_zhi, yue_zhi, question_type):
    """
    运行规则引擎，获取结构化结果（字典形式）
    """
    # 先跑完整断卦，提取关键数据
    report = full_duangua(ben_gua, dong_list, ri_gan, ri_zhi, yue_zhi, question_type)
    
    # 从报告里提取关键信息（或者直接重新计算一遍）
    from liuyao_engine import (
        get_xunkong, bian_gua, select_yongshen, get_shen_relations
    )
    from liuyao_paipan import get_gua_by_name, najia_for_gua, _LOOKUP_NEI_WAI
    from engine_core import DIZHI
    
    info = get_gua_by_name(ben_gua)
    bian = bian_gua(ben_gua, dong_list) if dong_list else None
    kong1, kong2 = get_xunkong(ri_gan + ri_zhi)
    yongshen_lq = select_yongshen(question_type)
    shen_rel = get_shen_relations(yongshen_lq)
    
    nei, wai = _LOOKUP_NEI_WAI[ben_gua]
    gua = najia_for_gua(nei, wai)
    
    # 找用神爻
    gong_wx = info["宫五行"]
    from engine_core import get_liuqin
    yongshen_yao = None
    for pos, zhi, gan in gua:
        zhi_wx = DIZHI[zhi]["五行"]
        lq = get_liuqin(gong_wx, zhi_wx)
        if lq == yongshen_lq:
            yongshen_yao = {"pos": pos, "zhi": zhi, "gan": gan, "liuqin": lq}
            break
    
    return {
        "question_type": question_type,
        "ben_gua": ben_gua,
        "ben_gua_gong": info["卦宫"],
        "bian_gua": bian,
        "dong_yao": dong_list,
        "yue_zhi": yue_zhi,
        "ri_ganzhi": ri_gan + ri_zhi,
        "xunkong": f"{kong1}{kong2}",
        "yongshen": yongshen_lq,
        "yongshen_yao": yongshen_yao,
        "shen_rel": shen_rel,
        "shi_yao_pos": info["世爻"],
        "ying_yao_pos": info["应爻"],
    }


def build_llm_prompt(structured):
    """
    构造给LLM的Prompt，让它像顶级易术大师一样解读
    """
    prompt = f"""你是一位精通周易六爻的资深大师，深谙《增删卜易》《卜筮正宗》的断卦精髓。
请根据以下卦象信息，给出专业、深刻、有指导意义的断卦解读。

【卦象基本信息】
- 占问事项：{structured['question_type']}
- 本卦：{structured['ben_gua']}（{structured['ben_gua_gong']}宫）
- 动爻：第{','.join(map(str, structured['dong_yao']))}爻动
- 变卦：{structured['bian_gua']}
- 月建：{structured['yue_zhi']}
- 日辰：{structured['ri_ganzhi']}
- 旬空：{structured['xunkong']}

【用神信息】
- 用神：{structured['yongshen']}
- 原神：{structured['shen_rel']['原神']}
- 忌神：{structured['shen_rel']['忌神']}
- 仇神：{structured['shen_rel']['仇神']}
"""
    
    if structured['yongshen_yao']:
        y = structured['yongshen_yao']
        prompt += f"- 用神爻位置：第{'初二三四五上'[y['pos']-1]}爻（{y['gan']}{y['zhi']}）\n"
    
    prompt += f"""
【世应】
- 世爻：第{structured['shi_yao_pos']}爻（代表求测人自己）
- 应爻：第{structured['ying_yao_pos']}爻（代表对方/所占之事）
"""

    # 语料增强：检索相关典籍原文佐证
    refs = _enhance_refs(structured)
    if refs:
        prompt += "\n【典籍佐证（供你引据的原文片段）】\n"
        for ref in refs:
            prompt += f"- 《{ref['book']}》：{ref['text']}\n"

    prompt += f"""
请你按以下结构输出解读：
1. 【卦象总断】：用两三句话概括这个卦的整体吉凶和核心趋势
2. 【用神分析】：用神的旺衰、动静、生源情况，对占问事项意味着什么
3. 【世应关系】：世爻和应爻的关系，对求测人有什么启示
4. 【关键提醒】：1-3条具体的行动建议或注意事项
5. 【应期判断】：大概什么时候会有结果

要求：
- 语言要像大师面对面聊天，不要太学术
- 要客观，不要只说好听的，凶的地方要直说
- 要有实操性的建议，不要空泛
"""
    return prompt


def get_api_key():
    """读取 DeepSeek API Key：环境变量 DEEPSEEK_API_KEY 或本地文件 .deepseek_key"""
    import os
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key.strip()
    kf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".deepseek_key")
    if os.path.exists(kf):
        with open(kf, encoding="utf-8") as f:
            k = f.read().strip()
            if k:
                return k
    return ""


def deepseek_interpret(prompt, temperature=0.6, max_tokens=800):
    """调用 DeepSeek Chat API 返回大师级白话解读（OpenAI 兼容端点）"""
    import urllib.request, json
    key = get_api_key()
    if not key:
        return {"ok": False, "error": "未配置 DeepSeek Key"}
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是精通周易六爻、深谙《增删卜易》《卜筮正宗》的资深易术大师。解读要专业、客观、可实操，像面对面聊天，凶处直说。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    try:
        # macOS 框架版 Python 默认 CA 为 None，用 certifi 的证书链做 SSL 验证
        _ctx = None
        try:
            import ssl, certifi
            _ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            _ctx = None
        with urllib.request.urlopen(req, timeout=60, context=_ctx) as resp:
            data = json.loads(resp.read().decode())
        text = data["choices"][0]["message"]["content"]
        return {"ok": True, "text": text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def duangua_with_llm(ben_gua, dong_list, ri_gan, ri_zhi, yue_zhi, question_type):
    """
    完整流程：规则引擎出数据 → 构造LLM Prompt
    （实际调用LLM由外部完成，这里只返回Prompt和结构化数据）
    """
    structured = get_structured_result(ben_gua, dong_list, ri_gan, ri_zhi, yue_zhi, question_type)
    prompt = build_llm_prompt(structured)
    
    return {
        "structured": structured,
        "llm_prompt": prompt,
    }


if __name__ == "__main__":
    # 测试
    result = duangua_with_llm(
        ben_gua="火天大有",
        dong_list=[3],
        ri_gan="甲",
        ri_zhi="子",
        yue_zhi="卯",
        question_type="财运"
    )
    
    print("=" * 60)
    print("结构化数据：")
    print("=" * 60)
    for k, v in result["structured"].items():
        print(f"  {k}: {v}")
    
    print("\n" + "=" * 60)
    print("给LLM的Prompt：")
    print("=" * 60)
    print(result["llm_prompt"])


def deepseek_chat(messages, temperature=0.7, max_tokens=1200):
    """多轮对话：messages = [{role:'system'|'user'|'assistant', content}, ...]
    让 DeepSeek 像易学大师一样连续解答。返回 {"ok":True,"text":...}"""
    import urllib.request, json
    key = get_api_key()
    if not key:
        return {"ok": False, "error": "未配置 DeepSeek Key"}
    url = "https://api.deepseek.com/chat/completions"
    payload = {"model": "deepseek-chat", "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    try:
        _ctx = None
        try:
            import ssl, certifi
            _ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            _ctx = None
        with urllib.request.urlopen(req, timeout=90, context=_ctx) as resp:
            data = json.loads(resp.read().decode())
        return {"ok": True, "text": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


_FACE_OPTIONS = (
    "【上停(额头)·shang】天庭开阔/天庭平满/天庭低窄；"
    "【中停(眉鼻)·zhong】鼻丰印明/中停平正/中停塌陷；"
    "【下停(颏颌)·xia】地阁圆润/下停中平/下停尖削；"
    "【气色·qise】红润/黄明/青黑/苍白；"
    "【眉相·wg_mei】眉清目秀/眉浓眉扬/眉疏而淡；"
    "【眼相·wg_yan】眼神明亮/眼形细长/眼小神浊；"
    "【鼻相·wg_bi】鼻隆有肉/鼻梁中正/鼻小尖削；"
    "【嘴相·wg_zui】嘴形方正/唇红齿白/嘴角下垂；"
    "【耳相·wg_er】耳大有轮/耳垂厚实/耳薄无垂"
)


def deepseek_vision(image_b64, note=""):
    """DeepSeek 视觉识脸：输入照片base64，返回结构化面相特征。
    返回 {"ok":True, "face":{...}, "desc":...} 或 {"ok":False,"error":...}"""
    import urllib.request, json, re
    key = get_api_key()
    if not key:
        return {"ok": False, "error": "未配置 DeepSeek Key"}
    prompt = (
        "你是精通中国传统相学（《麻衣相法》《神相全编》）的资深相师。"
        "请仔细观察这张人像照片，根据三停、五官、气色判断其面相特征。\n"
        f"附加信息：{note or '无'}\n"
        f"请从下列选项中为每一项选一个最贴切的值：\n{_FACE_OPTIONS}\n\n"
        "只输出一个 JSON 对象，不要任何其他文字，形如：\n"
        '{"shang":"...","zhong":"...","xia":"...","qise":"...",'
        '"wg_mei":"...","wg_yan":"...","wg_bi":"...","wg_zui":"...","wg_er":"...",'
        '"desc":"用2-3句白话概括此人面相气质与气运基调。"}'
    )
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]}],
        "temperature": 0.2,
        "max_tokens": 900,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    try:
        _ctx = None
        try:
            import ssl, certifi
            _ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            _ctx = None
        with urllib.request.urlopen(req, timeout=90, context=_ctx) as resp:
            data = json.loads(resp.read().decode())
        raw = data["choices"][0]["message"]["content"]
        # 提取 JSON（模型可能带 markdown 代码块）
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return {"ok": False, "error": "识脸返回非JSON: " + raw[:120]}
        face = json.loads(m.group(0))
        return {"ok": True, "face": face,
                "desc": face.get("desc", ""),
                "raw": raw}
    except Exception as e:
        return {"ok": False, "error": str(e)}
