#!/usr/bin/env python3
"""
木雷易术引擎 - 本地Web界面
运行后浏览器打开 http://localhost:5001
"""
from flask import Flask, request, render_template_string
from qigua import qigua_and_duangua
from meihua import meihua_duangua
from qimen import qimen_solve_problem
from fengshui import fengshui_advice
from personal_analysis import personal_analysis, help_others_analysis

app = Flask(__name__)

_MODULE_BY_PATH = {
    '/api/liuyao': '卜术', '/api/meihua': '气运', '/api/qimen': '奇门',
    '/api/fengshui': '风水', '/api/guoyun': '国运', '/api/personal': '八字',
    '/api/help': '相术', '/api/mianxiang': '相术', '/api/mianxiang_vision': '相术',
    '/api/chat': '问大师', '/api/search': '古籍',
}

@app.before_request
def _log_visit():
    try:
        import db
        # 隧道模式下优先取 X-Forwarded-For 里的真实访客公网 IP
        _xff = request.headers.get('X-Forwarded-For', '')
        ip = _xff.split(',')[0].strip() if _xff else (request.remote_addr or '')
        p = request.path
        db.record_visit(ip, request.headers.get('User-Agent', '')[:120], p,
                        _MODULE_BY_PATH.get(p, ''))
    except Exception:
        pass


def _i(v, d=0):
    """安全整数解析：None/空串/非法输入回退到默认值，杜绝 ValueError"""
    try:
        if v is None or str(v).strip() == '':
            return d
        return int(float(str(v)))
    except Exception:
        return d


def _s(data, key, default=''):
    """安全取字符串字段"""
    v = data.get(key)
    return default if v is None else str(v)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>木雷易术引擎</title>
    <style>
    * { box-sizing:border-box; margin:0; padding:0; }
        :root{ --gold:#e8c170; --gold-deep:#b8853a; --ink:#0f0c1e; --txt:#e6dfc8; --txt-dim:#9a8fc0; }
        body{
          font-family:"Songti SC","STSong","KaiTi","PingFang SC","Microsoft YaHei",serif;
          background-color:#0f0c1e;
          background-image:
            radial-gradient(ellipse 80% 50% at 15% 0%, rgba(60,42,95,.6), transparent 60%),
            radial-gradient(ellipse 70% 45% at 90% 100%, rgba(26,46,78,.65), transparent 60%),
            linear-gradient(165deg,#0f0c1e 0%,#191436 48%,#0d1226 100%);
          background-repeat:no-repeat;
          background-size:cover;
          min-height:100vh; padding:16px; color:var(--txt);
        }
        body::after{ content:"☯"; position:fixed; right:-40px; bottom:-60px; font-size:16rem;
          color:rgba(200,170,80,.045); pointer-events:none; z-index:0; }
        .container{ max-width:540px; margin:0 auto; }
        #profile-sidebar{ display:none; background:rgba(22,18,40,.85); border-right:1px solid rgba(200,170,80,.16); }
        .ml-header{ text-align:center; padding:6px 0 6px; position:relative; }
        .ml-taiji{ width:58px; height:58px; margin:0 auto 8px; display:block;
          animation:taijiSpin 22s linear infinite; filter:drop-shadow(0 0 12px rgba(232,193,112,.4)); }
        @keyframes taijiSpin{ to{ transform:rotate(360deg);} }
        .ml-title{ font-size:1.8rem; color:var(--gold); letter-spacing:.18em; font-weight:700;
          text-shadow:0 0 20px rgba(232,193,112,.4); }
        .ml-sub{ font-size:.74rem; color:var(--txt-dim); letter-spacing:.5em; margin-top:5px; }
        .ml-line{ height:1px; background:linear-gradient(90deg,transparent,rgba(232,193,112,.55),transparent);
          margin:14px auto 20px; width:78%; }
        .card{
          background:linear-gradient(160deg, rgba(45,30,66,.55), rgba(20,24,48,.5));
          border:1px solid rgba(200,170,80,.22); border-radius:16px; padding:20px;
          margin-bottom:16px; box-shadow:0 8px 26px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.05);
          backdrop-filter:blur(6px);
        }
        h1{ font-size:1.9rem; color:var(--gold); }
        .main-tabs{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-bottom:18px; }
        .main-tab{ padding:12px 2px; text-align:center; background:rgba(18,14,38,.6);
          border-radius:12px; cursor:pointer; border:1px solid rgba(200,170,80,.16);
          color:#cfc6a8; font-size:.85rem; transition:.2s; }
        .main-tab:hover{ border-color:rgba(200,170,80,.5); }
        .main-tab.active{ background:linear-gradient(160deg,#3a2a5a,#241a3d); border-color:var(--gold);
          color:#ffe9b0; box-shadow:0 0 16px rgba(232,193,112,.28); }
        .form-group{ margin-bottom:13px; }
        label{ display:block; margin-bottom:5px; color:var(--gold); font-size:.86rem; letter-spacing:.03em; }
        input,select,textarea{ width:100%; padding:12px; border-radius:10px; font-size:1rem;
          border:1px solid rgba(200,170,80,.28); background:rgba(8,6,18,.55); color:#efe6c8;
          font-family:inherit; }
        input:focus,select:focus,textarea:focus{ outline:none; border-color:var(--gold);
          box-shadow:0 0 0 2px rgba(232,193,112,.15); }
        button{ width:100%; padding:14px; background:linear-gradient(135deg,var(--gold) 0%,var(--gold-deep) 100%);
          color:#1a1208; border:none; border-radius:10px; font-size:1.05rem; font-weight:600;
          cursor:pointer; margin-top:8px; letter-spacing:.06em; box-shadow:0 4px 14px rgba(0,0,0,.3); }
        button:hover{ filter:brightness(1.08); }
        .result{ white-space:pre-wrap; font-family:"Songti SC","KaiTi",serif; font-size:.9rem;
          line-height:1.7; color:var(--txt); }
        .tab-content{ display:none; } .tab-content.active{ display:block; }
        .yao{ width:64px; height:10px; margin:5px auto; border-radius:3px; }
        .yao.yang{ background:var(--gold); border:1px solid #c9a24a; }
        .yao.yin{ background:transparent; border:2px solid var(--gold); box-sizing:border-box; height:9px; }
        @media (min-width:901px){ #profile-sidebar{ display:block; } }
        @media (max-width:900px){ #profile-sidebar{ display:none; } .container{ margin-left:0 !important; } }
        @media (max-width:480px){ body{ padding:10px; } .main-tabs{ gap:6px; }
          .main-tab{ padding:11px 2px; font-size:.8rem; } button{ padding:15px; font-size:1.08rem; }
          .card{ padding:16px; } }
            .ml-bagua{ display:flex; justify-content:center; gap:10px; font-size:1.15rem;
          color:rgba(232,193,112,.6); margin:2px 0 2px; letter-spacing:.18em; }
        .card{ position:relative; }
        .card::before{ content:""; position:absolute; inset:0; border-radius:16px;
          background:linear-gradient(135deg, rgba(232,193,112,.16), transparent 42%, transparent 58%, rgba(232,193,112,.06));
          pointer-events:none; }
        .main-tab.active{ background:linear-gradient(160deg,#d8b05c,#8a6a2a); color:#1a1208; font-weight:600;
          border-color:#e8c170; box-shadow:0 4px 18px rgba(232,193,112,.4); }
        .ml-taiji{ filter:drop-shadow(0 0 16px rgba(232,193,112,.55)); }
    </style>
</head>
<body>
    <div id="profile-sidebar" style="position:fixed;left:0;top:0;width:190px;height:100vh;background:#16162e;border-right:1px solid #2a2a45;padding:14px 10px;overflow-y:auto;z-index:50;">
        <div style="color:#e8c170;font-weight:600;margin-bottom:10px;">🧭 我的命盘</div>
        <div id="sidebar-content" style="color:#bbb;font-size:0.8rem;line-height:1.7;">
            未保存档案<br>在"八字"页点保存
        </div>
    </div>
    <div class="container">
        <div class="ml-header">
            <svg class="ml-taiji" viewBox="0 0 100 100" aria-hidden="true">
                <circle cx="50" cy="50" r="47" fill="#14102a" stroke="#e8c170" stroke-width="2"/>
                <path d="M50 3 a47 47 0 0 1 0 94 a23.5 23.5 0 0 1 0 -47 a23.5 23.5 0 0 1 0 -47z" fill="#e8c170"/>
                <path d="M50 97 a47 47 0 0 1 0 -94 a23.5 23.5 0 0 1 0 47 a23.5 23.5 0 0 1 0 47z" fill="#14102a"/>
                <circle cx="50" cy="26.5" r="8.5" fill="#14102a"/>
                <circle cx="50" cy="73.5" r="8.5" fill="#e8c170"/>
            </svg>
            <div class="ml-title">木雷易术</div>
            <div class="ml-sub">震木生发 · 占断天机</div>
            <div class="ml-bagua">☰ ☱ ☲ ☳ ☴ ☵ ☶ ☷</div>
            <div class="ml-line"></div>
            <button onclick="toggleHelp()" style="width:auto;background:#2a2a6a;border:1px solid #4a4a8a;padding:7px 14px;border-radius:8px;cursor:pointer;font-size:14px;color:#e8c170;">❓ 使用说明</button>
        </div>
        <div id="today-banner" style="background:linear-gradient(135deg,#2a1f3d,#1d2f3d);border:1px solid #4a3a5a;border-radius:10px;padding:12px 16px;margin-bottom:14px;color:#ddd;font-size:0.9rem;">
            今日宜忌加载中...
        </div>
        <div class="main-tabs">
            <div class="main-tab active" onclick="switchMainTab('consult')">八字</div>
            <div class="main-tab" onclick="switchMainTab('help')">相术</div>
            <div class="main-tab" onclick="switchMainTab('liuyao')">卜术</div>
            <div class="main-tab" onclick="switchMainTab('meihua')">气运</div>
            <div class="main-tab" onclick="switchMainTab('qimen')">奇门</div>
            <div class="main-tab" onclick="switchMainTab('fengshui')">风水</div>
            <div class="main-tab" onclick="switchMainTab('guoyun')">国运</div>
            <div class="main-tab" onclick="switchMainTab('guas')">卦例</div>
            <div class="main-tab" onclick="switchMainTab('guwen')">古籍</div>
            <div class="main-tab" onclick="switchMainTab('wengua')" style="background:#2a2a6a;">问卦</div>
            <div class="main-tab" onclick="switchMainTab('visits')" style="color:#e8a0a0;">访客</div>
        </div>
        
        <!-- 综合问诊 -->
        <div id="tab-consult" class="tab-content active">
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:15px;">📝 八字·个人问诊</h3>
                <div class="form-group">
                    <label>出生年（公历）</label>
                    <input type="number" id="pa-year" value="1990">
                </div>
                <div class="form-group">
                    <label>出生月</label>
                    <input type="number" id="pa-month" value="1">
                </div>
                <div class="form-group">
                    <label>出生日</label>
                    <input type="number" id="pa-day" value="1">
                </div>
                <div class="form-group">
                    <label>出生时辰（1-12，子1丑2...亥12）</label>
                    <input type="number" id="pa-hour" value="6">
                </div>
                <div class="form-group">
                    <label>性别</label>
                    <select id="pa-gender">
                        <option value="男" selected>男</option>
                        <option value="女">女</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>家中排行（用于九紫离火·中女运等位分分析）</label>
                    <select id="pa-rank">
                        <option value="独生" selected>独生</option>
                        <option value="长男">长男（长子）</option>
                        <option value="中男">中男（次子）</option>
                        <option value="少男">少男（三子/幼子）</option>
                        <option value="长女">长女</option>
                        <option value="中女">中女</option>
                        <option value="少女">少女</option>
                        <option value="其他">其他</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>近期主求（你现在最想解决什么？）</label>
                    <input type="text" id="pa-goal" value="投资/炒股赚钱">
                </div>
                <div class="form-group">
                    <label>当前人事状况（人际关系/工作/感情现状）</label>
                    <input type="text" id="pa-status" value="工作压力大，和领导关系一般">
                </div>
                <div class="form-group">
                    <label>主要问题类型</label>
                    <select id="pa-problem">
                        <option value="事业工作">事业工作</option>
                        <option value="财运生意" selected>财运生意</option>
                        <option value="感情婚姻">感情婚姻</option>
                        <option value="疾病健康">疾病健康</option>
                        <option value="官司是非">官司是非</option>
                    </select>
                </div>
                <button onclick="doPersonalAnalysis()">开始推算</button>
                <button onclick="saveProfile()" style="background:#2a2a6a;">💾 保存我的档案</button>
                <div style="color:#9aa; font-size:12px; margin-top:6px;">保存命盘后，相术/国运等会调用你的档案日主</div>
            </div>
        </div>
        
        <!-- 帮他人看 -->
        <div id="tab-help" class="tab-content">
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:15px;">👤 相术·面相×八字气运</h3>
                <div class="form-group">
                    <label>你的出生年</label>
                    <input type="number" id="mx-year" value="1979" style="width:120px;">
                </div>
                <div class="form-group">
                    <label>月</label><input type="number" id="mx-month" value="5" style="width:120px;">
                    <label>日</label><input type="number" id="mx-day" value="15" style="width:120px;">
                    <label>时辰(1-12)</label><input type="number" id="mx-hour" value="14" style="width:120px;">
                </div>
                <div class="form-group">
                    <label>上停·额头（主少运0-15）</label>
                    <select id="mx-shang">
                        <option value="天庭开阔">天庭开阔</option>
                        <option value="天庭平满" selected>天庭平满</option>
                        <option value="天庭低窄">天庭低窄</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>中停·眉鼻（主中运15-50）</label>
                    <select id="mx-zhong">
                        <option value="鼻丰印明">鼻丰印明</option>
                        <option value="中停平正" selected>中停平正</option>
                        <option value="中停塌陷">中停塌陷</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>下停·颏颌（主晚运50后）</label>
                    <select id="mx-xia">
                        <option value="地阁圆润">地阁圆润</option>
                        <option value="下停中平" selected>下停中平</option>
                        <option value="下停尖削">下停尖削</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>当下气色</label>
                    <select id="mx-qise">
                        <option value="红润">红润（运开）</option>
                        <option value="黄明" selected>黄明（吉）</option>
                        <option value="青黑">青黑（滞）</option>
                        <option value="苍白">苍白（弱）</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>上传面相照（本地预览，对照选择五官特征）</label>
                    <input type="file" id="mx-photo" accept="image/*" onchange="previewMxPhoto()">
                    <img id="mx-preview" style="max-height:140px; border-radius:8px; margin-top:6px; display:none;">
                </div>
                <div class="form-group">
                    <label>眉相</label>
                    <select id="mx-mei">
                        <option value="眉清目秀" selected>眉清目秀</option>
                        <option value="眉浓眉扬">眉浓眉扬</option>
                        <option value="眉疏而淡">眉疏而淡</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>眼相</label>
                    <select id="mx-yan">
                        <option value="眼神明亮" selected>眼神明亮</option>
                        <option value="眼形细长">眼形细长</option>
                        <option value="眼小神浊">眼小神浊</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>鼻相</label>
                    <select id="mx-bi">
                        <option value="鼻隆有肉" selected>鼻隆有肉</option>
                        <option value="鼻梁中正">鼻梁中正</option>
                        <option value="鼻小尖削">鼻小尖削</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>嘴相</label>
                    <select id="mx-zui">
                        <option value="嘴形方正" selected>嘴形方正</option>
                        <option value="唇红齿白">唇红齿白</option>
                        <option value="嘴角下垂">嘴角下垂</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>耳相</label>
                    <select id="mx-er">
                        <option value="耳大有轮" selected>耳大有轮</option>
                        <option value="耳垂厚实">耳垂厚实</option>
                        <option value="耳薄无垂">耳薄无垂</option>
                    </select>
                </div>
                <button onclick="doMianxiang()">看面相·气运</button>
                <button onclick="aiMianxiang()" style="background:#3a2a5a;">🤖 AI识脸·自动断相</button>
            </div>
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:15px;">👥 相术·帮人看</h3>
                <div class="form-group">
                    <label>看什么？</label>
                    <select id="ho-type">
                        <option value="姻缘">姻缘合盘</option>
                        <option value="健康">对方健康</option>
                        <option value="财运">对方财运</option>
                    </select>
                </div>
                
                <h4 style="color:#e8c170; margin:15px 0 10px;">你的八字</h4>
                <div class="form-group">
                    <label>出生年</label>
                    <input type="number" id="ho-my-year" value="1990">
                </div>
                <div class="form-group">
                    <label>月</label>
                    <input type="number" id="ho-my-month" value="5">
                </div>
                <div class="form-group">
                    <label>日</label>
                    <input type="number" id="ho-my-day" value="15">
                </div>
                <div class="form-group">
                    <label>时辰（1-12）</label>
                    <input type="number" id="ho-my-hour" value="6">
                </div>
                
                <h4 style="color:#e8c170; margin:15px 0 10px;">对方八字</h4>
                <div class="form-group">
                    <label>出生年</label>
                    <input type="number" id="ho-other-year" value="1992">
                </div>
                <div class="form-group">
                    <label>月</label>
                    <input type="number" id="ho-other-month" value="8">
                </div>
                <div class="form-group">
                    <label>日</label>
                    <input type="number" id="ho-other-day" value="20">
                </div>
                <div class="form-group">
                    <label>时辰（1-12）</label>
                    <input type="number" id="ho-other-hour" value="8">
                </div>
                
                <button onclick="doHelpOthers()">开始分析</button>
            </div>
        </div>
        
        <!-- 六爻断卦 -->
        <div id="tab-liuyao" class="tab-content">
            <div class="card">
                <div class="form-group">
                    <label>起卦方式</label>
                    <select id="ly-method" onchange="toggleQigua()">
                        <option value="number">报数起卦</option>
                        <option value="time">时间起卦</option>
                        <option value="coin">铜钱起卦</option>
                    </select>
                </div>
                <div id="qigua-number">
                    <div class="form-group">
                        <label>第一个数字</label>
                        <input type="number" id="ly-num1" value="3">
                    </div>
                    <div class="form-group">
                        <label>第二个数字</label>
                        <input type="number" id="ly-num2" value="8">
                    </div>
                </div>
                <div id="qigua-time" style="display:none;">
                    <div class="form-group">
                        <label>公历年</label><input type="number" id="ly-y" value="2026">
                        <label>月</label><input type="number" id="ly-m" value="9">
                        <label>日</label><input type="number" id="ly-d" value="30">
                        <label>时(0-23)</label><input type="number" id="ly-h" value="20">
                    </div>
                    <div style="color:#9aa; font-size:12px;">用当下时刻起卦，可手动改时间</div>
                </div>
                <div id="qigua-coin" style="display:none;">
                    <div class="form-group">
                        <label>六次摇卦（初爻→上爻），每爻选：3=少阳(三正) 2=少阴(二正一背) 9=老阳(三正动) 6=老阴(三背动)</label>
                    </div>
                    <div class="form-group" style="display:flex; gap:8px; flex-wrap:wrap;">
                        <select id="ly-coin1" style="width:64px;"><option value="3">少阳</option><option value="2">少阴</option><option value="9">老阳</option><option value="6">老阴</option></select>
                        <select id="ly-coin2" style="width:64px;"><option value="3">少阳</option><option value="2" selected>少阴</option><option value="9">老阳</option><option value="6">老阴</option></select>
                        <select id="ly-coin3" style="width:64px;"><option value="3">少阳</option><option value="2">少阴</option><option value="9">老阳</option><option value="6">老阴</option></select>
                        <select id="ly-coin4" style="width:64px;"><option value="3">少阳</option><option value="2">少阴</option><option value="9">老阳</option><option value="6">老阴</option></select>
                        <select id="ly-coin5" style="width:64px;"><option value="3">少阳</option><option value="2">少阴</option><option value="9">老阳</option><option value="6">老阴</option></select>
                        <select id="ly-coin6" style="width:64px;"><option value="3" selected>少阳</option><option value="2">少阴</option><option value="9">老阳</option><option value="6">老阴</option></select>
                    </div>
                </div>
                <div class="form-group">
                    <label>占问事项</label>
                    <select id="ly-qt">
                        <option value="财运">财运</option>
                        <option value="事业">事业</option>
                        <option value="考试">考试</option>
                        <option value="感情">感情</option>
                        <option value="疾病">疾病</option>
                        <option value="出行">出行</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>占卦人性别（婚姻/感情用神由此定）</label>
                    <select id="ly-gender">
                        <option value="男" selected>男</option>
                        <option value="女">女</option>
                    </select>
                </div>
                <button onclick="doLiuyao()">开始断卦</button>
                <button onclick="llmInterpret()" id="llm-btn" style="background:#2a2a6a;">🧠 DeepSeek大师解读</button>
                <div id="llm-status" style="color:#9aa; font-size:12px; margin-top:4px;"></div>
            </div>
        </div>
        
        <!-- 梅花易数 -->
        <div id="tab-meihua" class="tab-content">
            <div class="card">
                <div class="form-group">
                    <label>第一个数字（上卦）</label>
                    <input type="number" id="mh-num1" value="3">
                </div>
                <div class="form-group">
                    <label>第二个数字（下卦）</label>
                    <input type="number" id="mh-num2" value="8">
                </div>
                <div class="form-group">
                    <label>当前时辰（1-12，子1丑2...亥12）</label>
                    <input type="number" id="mh-hour" value="6">
                </div>
                <div class="form-group">
                    <label>占问事项</label>
                    <select id="mh-qt">
                        <option value="气运">看气运</option>
                        <option value="财运">财运</option>
                        <option value="感情">感情</option>
                        <option value="事业">事业</option>
                    </select>
                </div>
                <button onclick="doMeihua()">起卦断测</button>
            </div>
        </div>
        
        <!-- 奇门遁甲 -->
        <div id="tab-qimen" class="tab-content">
            <div class="card">
                <div class="form-group">
                    <label>你遇到什么问题？</label>
                    <select id="qm-problem">
                        <option value="财运生意">财运生意</option>
                        <option value="事业工作">事业工作</option>
                        <option value="感情婚姻">感情婚姻</option>
                        <option value="疾病健康">疾病健康</option>
                        <option value="官司是非">官司是非</option>
                    </select>
                </div>
                <button onclick="doQimen()">找解法</button>
            </div>
        </div>
        
        <!-- 风水布局 -->
        <div id="tab-fengshui" class="tab-content">
            <div class="card">
                <div class="form-group">
                    <label>看什么空间？</label>
                    <select id="fs-room">
                        <option value="客厅">客厅</option>
                        <option value="卧室">卧室</option>
                        <option value="厨房">厨房</option>
                        <option value="办公室">办公室</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>屋主出生年（定命卦，必填）</label>
                    <input type="number" id="fs-birth" value="1979" placeholder="如1979">
                </div>
                <div class="form-group">
                    <label>性别</label>
                    <select id="fs-gender">
                        <option value="男" selected>男</option>
                        <option value="女">女</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>宅之坐向（如：北=坐北朝南，可选）</label>
                    <select id="fs-seat">
                        <option value="">未提供</option>
                        <option value="北">坐北朝南（北）</option>
                        <option value="南">坐南朝北（南）</option>
                        <option value="东">坐东朝西（东）</option>
                        <option value="西">坐西朝东（西）</option>
                        <option value="东北">坐东北朝西南</option>
                        <option value="西北">坐西北朝东南</option>
                        <option value="东南">坐东南朝西北</option>
                        <option value="西南">坐西南朝东北</option>
                    </select>
                </div>
                <button onclick="doFengshui()">看风水</button>
            </div>
        </div>

        <div id="tab-guoyun" class="tab-content">
            <div class="card">
                <div class="form-group">
                    <label>分析年份</label>
                    <input type="number" id="gy-year" value="2026" style="width:120px;">
                </div>                <div class="form-group">
                    <label>分析对象</label>
                    <select id="gy-type">
                        <option value="国运">国运</option>
                        <option value="事态">事态</option>
                        <option value="大运">个人大运</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>你的日主五行（选填）</label>
                    <select id="gy-wx">
                        <option value="">--</option>
                        <option>木</option><option>火</option><option>土</option>
                        <option>金</option><option>水</option>
                    </select>
                </div>
                <button onclick="doGuoyun()">观世运</button>
            </div>
        </div>

        <div id="tab-guas" class="tab-content">
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:15px;">📒 卦例库（我的断卦记录）</h3>
                <button onclick="loadGuas()">加载卦例</button>
                <div style="color:#9aa; font-size:12px; margin:8px 0;">每断必记录 · 应验后回来标记复盘</div>
                <div class="result" id="guas-result" style="font-size:0.78rem;"></div>
            </div>
        </div>

        <div id="tab-guwen" class="tab-content">
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:15px;">📚 古籍知识库检索</h3>
                <div class="form-group">
                    <label>搜索关键词</label>
                    <input type="text" id="sw-q" placeholder="如：官鬼持世 / 妻财旺相 / 梅花体用 / 奇门生门" style="width:70%;">
                    <button onclick="doSearch()">检索</button>
                </div>
                <div style="color:#9aa; font-size:12px; margin:6px 0;">覆盖 42 部典籍正文 + 26.9万行卦例语料，返回原文可溯源</div>
                <div class="result" id="sw-result" style="font-size:0.78rem;"></div>
            </div>
        </div>

        <div id="tab-wengua" class="tab-content">
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:10px;">🧙 问大师 · 易学对谈</h3>
                <div style="color:#9aa; font-size:12px; margin-bottom:10px;">把心里的事说出来，与木雷易术大师对谈。事业、财运、感情、决策、时运皆可问，可连续追问。</div>
                <div id="chat-log" style="background:#14142a;border:1px solid #2e2e4a;border-radius:8px;min-height:220px;max-height:380px;overflow-y:auto;padding:10px;font-size:0.82rem;line-height:1.6;"></div>
                <textarea id="chat-input" rows="3" placeholder="把心里的事说出来…例如：我最近想换工作，但又担心风险，大师怎么看？"
                          style="width:100%; box-sizing:border-box; background:#0f0f22; color:#f0f0fa; border:1px solid #3a3a5a; border-radius:8px; padding:11px; font-size:15px; line-height:1.5; font-family:inherit; resize:vertical; min-height:78px;"
                          onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat();}"></textarea>
                <div style="display:flex; gap:8px; margin-top:8px; align-items:center;">
                    <button onclick="sendChat()" style="background:#2a2a6a; padding:8px 16px; border-radius:8px; cursor:pointer; font-size:14px; color:#e8c170; border:1px solid #4a4a8a;">🔮 问大师</button>
                    <button onclick="clearChat()" style="background:#33335a; font-size:12px;">清空对话</button>
                    <span style="color:#777; font-size:11px; margin-left:auto;">Enter 发送 · Shift+Enter 换行</span>
                </div>
                <div style="color:#777; font-size:11px; margin-top:8px;">多轮追问会自动带上之前对话；点"清空"可开启新话题。</div>
                <button onclick="clearChat()" style="margin-top:4px; background:#33335a; font-size:12px;">清空对话</button>
            </div>
        </div>

        <div id="tab-visits" class="tab-content">
            <div class="card">
                <h3 style="color:#e8c170; margin-bottom:12px;">👁 访客留档</h3>
                <div style="color:#9aa; font-size:12px; margin-bottom:10px;">记录所有访问（IP/时间/用的模块）。标红的为非家人 IP —— 若非家人使用，可据此决定是否收费。家人 IP 请点「标记家人」。</div>
                <div id="visit-stats" style="color:#ddd;font-size:0.9rem;margin-bottom:10px;">加载中...</div>
                <div id="visit-list" style="font-size:0.85rem;"></div>
            </div>
        </div>
        <div class="card" id="gua-card" style="display:none">
            <h3 style="color:#e8c170; margin-bottom:15px;">🀄 卦象演变</h3>
            <div id="gua-visual"></div>
        </div>

        <div class="card" id="sym-card" style="display:none">
            <h3 style="color:#e8c170; margin-bottom:6px;">☯ 对称性面板 · 本 / 错 / 综 / 互</h3>
            <div style="color:#9aa; font-size:12px; margin-bottom:10px;">错卦＝六爻全反；综卦＝上下颠倒；互卦＝取 2·3·4 与 3·4·5 爻重组成卦。下方标注与本卦的汉明距离（0 最近，6 最远）。</div>
            <div id="sym-body"></div>
        </div>

        <div class="card" id="cal-card" style="display:none">
            <h3 style="color:#e8c170; margin-bottom:6px;">🌗 历法面板 · 节气 / 真太阳时 / 月相 / 岁星</h3>
            <div style="display:flex; gap:10px; align-items:flex-end; flex-wrap:wrap; margin-bottom:10px;">
                <div><label style="font-size:12px;color:#9aa;">经度</label><br><input type="number" id="cal-lng" value="116.4" step="0.1" style="width:88px;"></div>
                <div><label style="font-size:12px;color:#9aa;">纬度</label><br><input type="number" id="cal-lat" value="39.9" step="0.1" style="width:88px;"></div>
                <button onclick="renderCalPanel()" style="width:auto;margin:0;padding:8px 14px;">按此刻重算</button>
            </div>
            <div id="cal-body"></div>
        </div>

        <div class="card" id="result-card" style="display:none">
            <h3 style="color:#e8c170; margin-bottom:15px;">结果</h3>
            <div class="result" id="result"></div>
        </div>
    </div>
    
    <script>
        function switchMainTab(tab) {
            document.querySelectorAll('.main-tab').forEach((t, i) => {
                t.classList.toggle('active', 
                    (i === 0 && tab === 'consult') || 
                    (i === 1 && tab === 'help') || 
                    (i === 2 && tab === 'liuyao') || 
                    (i === 3 && tab === 'meihua') || 
                    (i === 4 && tab === 'qimen') || 
                    (i === 5 && tab === 'fengshui') || 
                    (i === 6 && tab === 'guoyun') || 
                    (i === 7 && tab === 'guas') || 
                    (i === 8 && tab === 'guwen') || 
                    (i === 9 && tab === 'wengua') || 
                    (i === 10 && tab === 'visits'));
            });
            document.getElementById('tab-consult').classList.toggle('active', tab === 'consult');
            document.getElementById('tab-help').classList.toggle('active', tab === 'help');
            document.getElementById('tab-liuyao').classList.toggle('active', tab === 'liuyao');
            document.getElementById('tab-meihua').classList.toggle('active', tab === 'meihua');
            document.getElementById('tab-qimen').classList.toggle('active', tab === 'qimen');
            document.getElementById('tab-fengshui').classList.toggle('active', tab === 'fengshui');
            document.getElementById('tab-guoyun').classList.toggle('active', tab === 'guoyun');
            document.getElementById('tab-guas').classList.toggle('active', tab === 'guas');
            document.getElementById('tab-guwen').classList.toggle('active', tab === 'guwen');
            document.getElementById('tab-wengua').classList.toggle('active', tab === 'wengua');
            document.getElementById('tab-visits').classList.toggle('active', tab === 'visits');
            if (tab === 'visits') loadVisits();
        }
        
        async function renderSymPanel(guaName, dong) {
            const card = document.getElementById("sym-card");
            const body = document.getElementById("sym-body");
            if (!guaName) { card.style.display = "none"; return; }
            try {
                let url = "/api/symmetry?gua=" + encodeURIComponent(guaName);
                if (dong && dong.length) url += "&dong=" + encodeURIComponent(dong.join(","));
                const r = await (await fetch(url)).json();
                if (!r.ok) throw new Error(r.error || "无返回");
                const dist = r.distances || {};
                let h = '<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px;">';
                (r.views || []).forEach(function(v) {
                    const isBase = (v.view === "本卦");
                    const dd = dist[v.view];
                    const tag = dd ? ('<div style="color:#8fd0ff;font-size:0.75rem;margin-top:4px;">距本卦 ' + dd.hamming + ' 爻 · 相似 ' + Number(dd.similarity).toFixed(2) + '</div>') : '';
                    h += '<div style="border:1px solid ' + (isBase ? "#e8c170" : "#33334f") + ';border-radius:10px;padding:10px 12px;background:' + (isBase ? "rgba(232,193,112,0.08)" : "rgba(255,255,255,0.02)") + ';">'
                       + '<div style="color:#9aa;font-size:0.75rem;">' + v.view + '</div>'
                       + '<div style="color:' + (isBase ? "#e8c170" : "#dddddd") + ';font-size:1.05rem;font-weight:600;margin:2px 0;">' + esc(v.name) + '</div>'
                       + '<div style="color:#9aa;font-size:0.78rem;">上' + esc(v.upper) + '（' + esc(v.upper_nature) + '）· 下' + esc(v.lower) + '（' + esc(v.lower_nature) + '）</div>'
                       + '<div style="color:#8fd0ff;font-family:monospace;font-size:0.8rem;">' + v.binary + ' · #' + v.code + '</div>'
                       + tag + '</div>';
                });
                h += '</div>';
                const ss = r.self_symmetric || {};
                if (ss["错卦自同"] || ss["综卦自同"]) {
                    h += '<div style="color:#e8c170;font-size:0.78rem;margin-top:8px;">自同标记：'
                       + (ss["错卦自同"] ? "错卦自同（六爻两两对称） " : "")
                       + (ss["综卦自同"] ? "综卦自同（上下颠倒不变）" : "") + '</div>';
                }
                body.innerHTML = h;
                card.style.display = "block";
            } catch (e) {
                card.style.display = "none";
            }
        }

        async function renderCalPanel() {
            const card = document.getElementById("cal-card");
            const body = document.getElementById("cal-body");
            if (!card || !body) return;
            const pad = n => String(n).padStart(2, "0");
            const now = new Date();
            const ds = now.getFullYear() + "-" + pad(now.getMonth() + 1) + "-" + pad(now.getDate());
            const ts = pad(now.getHours()) + ":" + pad(now.getMinutes());
            const lngEl = document.getElementById("cal-lng");
            const latEl = document.getElementById("cal-lat");
            const lng = parseFloat(lngEl && lngEl.value ? lngEl.value : 116.4);
            const lat = parseFloat(latEl && latEl.value ? latEl.value : 39.9);
            card.style.display = "block";
            body.innerHTML = '<div style="color:#9aa;font-size:0.85rem;">计算中…</div>';
            try {
                const r = await (await fetch("/api/calendar?date=" + ds + "&time=" + ts + "&lng=" + lng + "&lat=" + lat)).json();
                if (!r.ok) throw new Error(r.error || "无返回");
                const term = r.solar_term || {};
                const sun = r.sun || {};
                const moon = r.moon || {};
                const jup = r.jupiter || {};
                const items = [
                    ["当前节气", (term.prev ? term.prev.name : "—") + " → " + (term.next ? term.next.name : "—"), term.next ? ("下个节气 " + term.next.time_bj) : ""],
                    ["太阳黄经", sun.longitude_deg + "°", "二十四节气＝黄经每 15° 一刀"],
                    ["真太阳时", r.true_solar_time, "均时差 " + sun.equation_of_time_min + " 分 · 经度修正 " + sun.longitude_correction_min + " 分"],
                    ["月相", moon.phase, "月龄 " + moon.age_days + " 天 · 照亮 " + Math.round((moon.illum_frac || 0) * 100) + "%"],
                    ["岁星", jup.zhi + "（" + jup.xi + "）", "木星周期 " + jup.period_years + " 年"]
                ];
                let h = '<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:10px;">';
                items.forEach(function(it) {
                    h += '<div style="border:1px solid #33334f;border-radius:10px;padding:10px 12px;background:rgba(255,255,255,0.02);">'
                       + '<div style="color:#9aa;font-size:0.75rem;">' + it[0] + '</div>'
                       + '<div style="color:#e8c170;font-size:1.02rem;font-weight:600;margin:2px 0;word-break:break-all;">' + esc(String(it[1])) + '</div>'
                       + '<div style="color:#9aa;font-size:0.74rem;">' + esc(String(it[2])) + '</div></div>';
                });
                h += '</div>';
                body.innerHTML = h;
            } catch (e) {
                body.innerHTML = '<div style="color:#e8a0a0;font-size:0.85rem;">历法计算失败：' + esc(e.message) + '</div>';
            }
        }

        function showResult(text) {
            document.getElementById('result').textContent = text;
            document.getElementById('result-card').style.display = 'block';
        }
        
        async function loadVisits() {
            const st = document.getElementById('visit-stats');
            const li = document.getElementById('visit-list');
            st.textContent = '加载中...';
            try {
                const r = await (await fetch('/api/visits')).json();
                if (!r) throw new Error('无返回');
                const s = r.stats || {};
                st.innerHTML = '总访问 <b>' + (s.total||0) + '</b> 次 · 去重IP <b>' + (s.ips||0) + '</b> · <span style="color:#e8a0a0;">非家人IP <b>' + (s.stranger_ips||0) + '</b></span>';
                const rows = r.rows || [];
                if (!rows.length) { li.innerHTML = '<div style="color:#777">暂无访问记录。</div>'; return; }
                let h = '';
                rows.forEach(function(x) {
                    const fam = (x.is_family === 1);
                    const mods = (x.modules||'').split(',').filter(Boolean).join(' / ') || '浏览页面';
                    h += '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 6px;border-bottom:1px solid rgba(255,255,255,0.06);' + (fam?'':'background:rgba(200,60,60,0.10);border-left:3px solid #c0392b;') + '">'
                       + '<div style="flex:1;min-width:0;">'
                       +   '<div style="color:' + (fam?'#8fd0ff':'#e8a0a0') + ';font-family:monospace;font-size:0.9rem;">' + esc(x.ip) + (fam?' <span style="font-size:0.72rem;color:#7ad;">·家人</span>':' <span style="font-size:0.72rem;color:#e8a0a0;">·非家人</span>') + '</div>'
                       +   '<div style="color:#9aa;font-size:0.75rem;word-break:break-all;">' + esc(String(x.cnt||0)) + ' 次 · 最近 ' + esc(x.last_ts||'') + ' · 用: ' + esc(mods) + '</div>'
                       + '</div>'
                       + '<button onclick="trustIp(\\'' + x.ip + '\\',' + (fam?'false':'true') + ')" style="width:auto;margin:0;padding:6px 12px;font-size:0.78rem;flex:none;background:' + (fam?'#33335a':'#c0392b') + ';color:' + (fam?'#ddd':'#fff') + ';">' + (fam?'取消家人':'标记家人') + '</button>'
                       + '</div>';
                });
                li.innerHTML = h;
            } catch(e) { st.textContent = '出错了: ' + e.message; }
        }
        async function trustIp(ip, on) {
            try { const r = await postData('/api/visits/trust', {ip: ip, is_family: on}); if (r && r.ok) loadVisits(); }
            catch(e) { alert('操作失败: ' + e.message); }
        }

        // 卦象可视化：本卦→互卦→变卦 六爻图（动爻高亮）
        function renderGua(g) {
            const card = document.getElementById('gua-card');
            if (!g || !g.ben) { card.style.display = 'none'; return; }
            card.style.display = 'block';
            const dongSet = new Set((g.dong||[]).map(Number));
            const order = ['ben','hu','bian'];
            const label = { 'ben':'本卦', 'hu':'互卦', 'bian':'变卦' };
            let html = '<div style="display:flex; gap:28px; flex-wrap:wrap; justify-content:center;">';
            for (const key of order) {
                const c = g[key];
                if (!c) continue;
                const lines = c.lines.slice().reverse(); // 上爻→初爻
                let inner = '';
                lines.forEach((v, i) => {
                    const pos = 6 - i;              // 爻位（上行是上爻）
                    const dong = dongSet.has(pos);
                    const cls = 'yao ' + (v===1 ? 'yang' : 'yin');
                    const mark = dong ? ' style="box-shadow:0 0 10px #ffd166;border-color:#ffd166;"' : '';
                    inner += `<div class="${cls}"${mark}></div>`;
                });
                const nm = (key==='ben') ? (g.ben.name||'') : ((key==='hu')?'互卦':(g.bian.name||'变卦'));
                html += `<div style="text-align:center;"><div style="color:#e8c170;margin-bottom:6px;font-weight:600;">${label[key]}${nm?' · '+nm:''}</div><div style="display:inline-block;border:1px solid #3a3a5a;border-radius:6px;padding:6px;background:#23233c;">${inner}</div></div>`;
            }
            html += '</div>';
            html += '<div style="text-align:center;color:#9aa;font-size:12px;margin-top:8px;">⚡ 高亮爻 = 动爻（本卦变此）</div>';
            document.getElementById('gua-visual').innerHTML = html;
        }

        async function postData(url, data) {
            const resp = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return resp.json();
        }
        
        function fillNow() {
            const n = new Date();
            const id = (x) => document.getElementById(x);
            if (id('ly-y')) id('ly-y').value = n.getFullYear();
            if (id('ly-m')) id('ly-m').value = n.getMonth() + 1;
            if (id('ly-d')) id('ly-d').value = n.getDate();
            if (id('ly-h')) id('ly-h').value = n.getHours();
        }

        async function loadToday() {
            try {
                const resp = await fetch('/api/today');
                const t = await resp.json();
                if (t.error) { document.getElementById('today-banner').textContent = '今日宜忌暂不可用'; return; }
                const a = t.advice || {};
                const wx = t.day_wx ? ` · 你的日主${t.day_wx}${a.wx_tip||''}` : '';
                window._today = t;
                document.getElementById('today-banner').innerHTML =
                    `☀️ <b style="color:#e8c170;">${t.date} 今日卦</b>：${t.hexagram}（${t.order}卦，第${(t.dong||[]).join('、')||'-'}爻动）` +
                    `<div style="color:#c9a24a;margin-top:4px;">卦辞：${t.guaci||''}</div>` +
                    `<div style="margin-top:4px;">✅ ${a.宜||''} · ⛔ ${a.忌||''}${wx}</div>` +
                    `<div style="margin-top:8px;"><a href="/share/today" target="_blank" style="background:#1f4d8f;color:#fff;padding:5px 12px;border-radius:6px;text-decoration:none;font-size:13px;">🔗 分享今日卦链接</a></div>`;
            } catch (e) { document.getElementById('today-banner').textContent = '今日宜忌暂不可用'; }
        }

        async function pushText(text) {
            const hint = document.getElementById('push-hint');
            if (hint) hint.textContent = '推送中...';
            const r = await postData('/api/push', { text: text });
            if (hint) hint.textContent = r.ok ? '✅ 已推送' : ('⚠️ ' + (r.error||'失败'));
            if (r.ok) showResult('✅ 已推送到飞书群。');
        }
        (async () => { try { const s = await (await fetch('/api/push_status')).json(); window._pushCfg = s; } catch(e){} })();

        async function loadProfile() {
            try {
                const resp = await fetch('/api/profile');
                const d = await resp.json();
                const p = d.profile;
                const sb = document.getElementById('sidebar-content');
                if (p && p.birth_year) {
                    const id = (x) => document.getElementById(x);
                    if (id('pa-year')) id('pa-year').value = p.birth_year;
                    if (id('pa-month')) id('pa-month').value = p.birth_month;
                    if (id('pa-day')) id('pa-day').value = p.birth_day;
                    if (id('pa-hour')) id('pa-hour').value = p.birth_hour;
                    if (id('pa-gender') && p.gender) id('pa-gender').value = p.gender;
                    if (id('pa-rank') && p.rank) id('pa-rank').value = p.rank;
                    if (id('mx-year')) id('mx-year').value = p.birth_year;
                    if (id('mx-month')) id('mx-month').value = p.birth_month;
                    if (id('mx-day')) id('mx-day').value = p.birth_day;
                    if (id('mx-hour')) id('mx-hour').value = p.birth_hour;
                    const wx = p.day_wx || '—';
                    const wxColor = {木:'#7ee2a8',火:'#ff9b6a',土:'#e8c170',金:'#d9b8ff',水:'#8fd0ff'}[wx] || '#bbb';
                    sb.innerHTML = `
                        <div style="color:#e8c170;font-size:1rem;margin-bottom:4px;">${wx}</div>
                        <div>出生：${p.birth_year}-${p.birth_month}-${p.birth_day} ${p.birth_hour}时</div>
                        <div>性别：${p.gender||'男'} · 排行：${p.rank||'—'}</div>
                        <div style="margin-top:8px;color:#9aa;">全局分析均带此日主五行</div>`;
                } else {
                    sb.innerHTML = '未保存档案<br>在"八字"页点"保存我的档案"';
                }
            } catch (e) {}
        }

        async function saveProfile() {
            const id = (x) => document.getElementById(x);
            const data = {
                year: parseInt(id('pa-year').value), month: parseInt(id('pa-month').value),
                day: parseInt(id('pa-day').value), hour: parseInt(id('pa-hour').value),
                gender: id('pa-gender') ? id('pa-gender').value : '男',
                rank: id('pa-rank') ? id('pa-rank').value : '', name: '我'
            };
            const resp = await fetch('/api/profile', {
                method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)
            });
            const d = await resp.json();
            if (d.ok) {
                showResult('💾 档案已保存。日主五行：' + d.day_wx);
                await loadProfile();   // 保存后立即刷新左侧命盘
            } else {
                showResult('保存失败: ' + (d.error||''));
            }
        }
        loadToday();
        loadProfile();
        renderCalPanel();
        fillNow();

        function toggleQigua() {
            const m = document.getElementById('ly-method').value;
            document.getElementById('qigua-number').style.display = (m==='number') ? 'block' : 'none';
            document.getElementById('qigua-time').style.display = (m==='time') ? 'block' : 'none';
            document.getElementById('qigua-coin').style.display = (m==='coin') ? 'block' : 'none';
            if (m === 'time') fillNow();
        }
        fillNow();

        async function doLiuyao() {
            showResult('断卦中...');
            try {
                const method = document.getElementById('ly-method').value;
                const data = { method: method, question_type: document.getElementById('ly-qt').value, gender: document.getElementById('ly-gender').value };
                if (method === 'number') {
                    data.num1 = parseInt(document.getElementById('ly-num1').value);
                    data.num2 = parseInt(document.getElementById('ly-num2').value);
                } else if (method === 'time') {
                    data.year = parseInt(document.getElementById('ly-y').value);
                    data.month = parseInt(document.getElementById('ly-m').value);
                    data.day = parseInt(document.getElementById('ly-d').value);
                    data.hour = parseInt(document.getElementById('ly-h').value);
                } else if (method === 'coin') {
                    data.results = [1,2,3,4,5,6].map(i =>
                        parseInt(document.getElementById('ly-coin'+i).value));
                }
                const result = await postData('/api/liuyao', data);
                renderGua(result.gua_visual);
                window._lastGua = result.gua_visual;
                showResult(result.report);
                if (result.gua_visual && result.gua_visual.ben) {
                    renderSymPanel(result.gua_visual.ben.name, result.gua_visual.dong);
                }
                renderCalPanel();
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }

        async function checkLlm() {
            try {
                const r = await (await fetch('/api/llm_status')).json();
                const el = document.getElementById('llm-status');
                el.innerHTML = r.configured
                    ? '✅ DeepSeek 已配置，可一键大师解读'
                    : '⚠️ 未配置 Key：将 <code>.deepseek_key</code> 文件放到知识库目录，或设环境变量 DEEPSEEK_API_KEY';
            } catch (e) {}
        }
        checkLlm();

        async function llmInterpret() {
            const g = window._lastGua;
            if (!g || !g.ben) { showResult('请先断一卦，再点大师解读。'); return; }
            showResult('DeepSeek 大师解读中（约15秒）...');
            try {
                const data = {
                    ben_gua: g.ben.name, dong: g.dong,
                    question_type: document.getElementById('ly-qt').value
                };
                const r = await postData('/api/llm_interpret', data);
                showResult(r.ok ? ('🧠 【DeepSeek大师解读】\\n\\n' + r.text) : ('解读失败: ' + r.error));
            } catch (e) { showResult('出错了: ' + e.message); }
        }
        
        async function doMeihua() {
            showResult('起卦中...');
            try {
                const data = {
                    num1: parseInt(document.getElementById('mh-num1').value),
                    num2: parseInt(document.getElementById('mh-num2').value),
                    hour: parseInt(document.getElementById('mh-hour').value),
                    question_type: document.getElementById('mh-qt').value
                };
                const result = await postData('/api/meihua', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }
        
        async function doQimen() {
            showResult('推演中...');
            try {
                const data = { problem: document.getElementById('qm-problem').value };
                const result = await postData('/api/qimen', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }
        
        async function doFengshui() {
            showResult('分析中...');
            try {
                const data = { room: document.getElementById('fs-room').value,
                               birth_year: parseInt(document.getElementById('fs-birth').value),
                               gender: document.getElementById('fs-gender').value,
                               seat: document.getElementById('fs-seat').value };
                const result = await postData('/api/fengshui', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }

        async function doGuoyun() {
            showResult('观世运中...');
            try {
                const data = {
                    year: document.getElementById('gy-year').value,
                    type: document.getElementById('gy-type').value,
                    wx: document.getElementById('gy-wx').value
                };
                const result = await postData('/api/guoyun', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }

        function previewMxPhoto() {
            const f = document.getElementById('mx-photo').files[0];
            if (!f) return;
            const img = document.getElementById('mx-preview');
            img.src = URL.createObjectURL(f);
            img.style.display = 'block';
        }

        async function aiMianxiang() {
            const f = document.getElementById('mx-photo').files[0];
            if (!f) { showResult('请先上传一张面相照片'); return; }
            showResult('🤖 AI识脸中，请稍候…');
            try {
                const b64 = await new Promise((res, rej) => {
                    const r = new FileReader();
                    r.onload = () => res(String(r.result).split(',')[1]);
                    r.onerror = () => rej(new Error('读取图片失败'));
                    r.readAsDataURL(f);
                });
                const year = document.getElementById('mx-year').value;
                const result = await postData('/api/mianxiang_vision', { image: b64, note: '约' + year + '年出生' });
                if (!result.ok) { showResult('识脸失败: ' + (result.error || '')); return; }
                const fc = result.face;
                const map = { 'mx-shang':'shang','mx-zhong':'zhong','mx-xia':'xia','mx-qise':'qise',
                              'mx-mei':'wg_mei','mx-yan':'wg_yan','mx-bi':'wg_bi','mx-zui':'wg_zui','mx-er':'wg_er' };
                for (const id in map) {
                    const el = document.getElementById(id);
                    const v = fc[map[id]];
                    if (v && Array.from(el.options).some(o => o.value === v)) el.value = v;
                }
                doMianxiang();
            } catch (e) {
                showResult('识脸出错: ' + e.message);
            }
        }

        async function doMianxiang() {
            showResult('看相中...');
            try {
                const data = {
                    year: parseInt(document.getElementById('mx-year').value),
                    month: parseInt(document.getElementById('mx-month').value),
                    day: parseInt(document.getElementById('mx-day').value),
                    hour: parseInt(document.getElementById('mx-hour').value),
                    shang: document.getElementById('mx-shang').value,
                    zhong: document.getElementById('mx-zhong').value,
                    xia: document.getElementById('mx-xia').value,
                    qise: document.getElementById('mx-qise').value,
                    wg_mei: document.getElementById('mx-mei').value,
                    wg_yan: document.getElementById('mx-yan').value,
                    wg_bi: document.getElementById('mx-bi').value,
                    wg_zui: document.getElementById('mx-zui').value,
                    wg_er: document.getElementById('mx-er').value
                };
                const result = await postData('/api/mianxiang', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }

        async function loadGuas() {
            const box = document.getElementById('guas-result');
            box.textContent = '加载中...';
            try {
                const resp = await fetch('/api/guas');
                const data = await resp.json();
                const rows = data.records || [];
                const st = data.stats || {};
                let h = '';
                if (st.total > 0) {
                    const mods = Object.entries(st.by_module||{}).map(([k,v])=>`${k} ${v}`).join(' · ');
                    h += `<div style="background:#1d1d36;border:1px solid #3a3a5a;border-radius:8px;padding:10px;margin-bottom:12px;">`;
                    h += `<b style="color:#e8c170;">📊 复盘统计</b><br>`;
                    h += `<span style="margin-right:18px;">总卦例 <b>${st.total}</b></span>`;
                    h += `<span style="margin-right:18px;">已复盘 <b>${st.reviewed}</b></span>`;
                    h += `<span style="margin-right:18px;">应验 <b style="color:#7ee2a8;">${st.accurate}</b></span>`;
                    h += `<span>准确率 <b style="color:#7ee2a8;">${st.accuracy}%</b></span>`;
                    if (mods) h += `<div style="color:#9aa;font-size:12px;margin-top:6px;">分模块：${mods}</div>`;
                    h += '</div>';
                }
                if (!rows.length) { box.innerHTML = h + '暂无卦例记录，先去断一卦吧。'; return; }
                const f = (v) => (v || '—');
                h += '<table style="width:100%;border-collapse:collapse;text-align:left;">';
                h += '<tr style="background:#2a2a45;color:#e8c170;">';
                h += '<th>编号</th><th>日期</th><th>占问</th><th>本卦</th><th>变卦</th><th>动爻</th><th>结论</th><th>置信</th><th>是否准确</th><th>复盘</th></tr>';
                rows.slice().reverse().forEach(r => {
                    h += '<tr style="border-bottom:1px solid #33335a;">';
                    h += `<td>${f(r['案例编号'])}</td><td>${f(r['起卦日期'])}</td><td>${f(r['占问类别'])}</td>`;
                    h += `<td>${f(r['本卦'])}</td><td>${f(r['变卦'])}</td><td>${f(r['动爻位置'])}</td>`;
                    h += `<td>${f(r['断卦结论'])}</td><td>${f(r['置信度(高/中/低)'])}</td>`;
                    h += `<td>${f(r['是否准确'])}</td>`;
                    h += `<td><button onclick="markGua('${f(r['案例编号'])}','应验')">✓应验</button> `;
                    h += `<button onclick="markGua('${f(r['案例编号'])}','未验')">✗未验</button> `;
                    h += `<a href="/share/${f(r['案例编号'])}" target="_blank" style="color:#8fd0ff;font-size:12px;text-decoration:none;">🔗分享</a></td>`;
                    h += '</tr>';
                });
                h += '</table>';
                box.innerHTML = h;
            } catch (e) { box.textContent = '出错了: ' + e.message; }
        }

        async function sendChat() {
            const inp = document.getElementById('chat-input');
            const q = inp.value.trim();
            if (!q) return;
            const log = document.getElementById('chat-log');
            window._chatMsgs = window._chatMsgs || [];
            // 显示用户气泡
            log.innerHTML += `<div style="color:#8fd0ff;margin-bottom:6px;"><b>🙋 你：</b><br>${esc(q)}</div>`;
            window._chatMsgs.push({role:'user', content:q});
            inp.value = '';
            const t = document.createElement('div');
            t.innerHTML = `<div style="color:#e8c170;margin:6px 0;">🧙 大师思考中...</div>`;
            log.appendChild(t); log.scrollTop = log.scrollHeight;
            try {
                const r = await postData('/api/chat', {messages: window._chatMsgs});
                if (r.ok) {
                    t.innerHTML = `<div style="color:#e8c170;margin:6px 0;"><b>🧙 大师：</b></div><div style="color:#ddd;white-space:pre-wrap;background:#1d1d36;border-left:3px solid #e8c170;padding:8px 10px;border-radius:6px;margin-bottom:8px;">${esc(r.text)}</div>`;
                    window._chatMsgs.push({role:'assistant', content:r.text});
                } else {
                    t.innerHTML = `<div style="color:#e8a0a0;margin:6px 0;">⚠ ${esc(r.error||'大师暂时没回应')}</div>`;
                }
            } catch(e) {
                t.innerHTML = `<div style="color:#e8a0a0;margin:6px 0;">出错了: ${esc(e.message)}</div>`;
            }
            log.scrollTop = log.scrollHeight;
        }

        function clearChat() {
            window._chatMsgs = [];
            document.getElementById('chat-log').innerHTML =
                `<div style="color:#777;font-size:12px;">（新话题已开启，请问大师吧）</div>`;
        }

        function esc(s) {
            return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }

        async function doSearch() {
            const q = document.getElementById('sw-q').value.trim();
            const box = document.getElementById('sw-result');
            if (!q) { box.textContent = '请输入关键词。'; return; }
            box.textContent = '检索中...';
            try {
                const resp = await fetch('/api/search?q=' + encodeURIComponent(q));
                const d = await resp.json();
                const res = d.results || [];
                if (!res.length) { box.textContent = '未检索到相关原文。'; return; }
                let h = `<div style="color:#e8c170;margin-bottom:8px;">命中 ${res.length} 条（关键词：${q}）</div>`;
                res.forEach(r => {
                    const tag = r.type === '典籍正文' ? `📖 ${r.book||''}` : '🗂 卦例语料';
                    h += `<div style="background:#1d1d36;border:1px solid #33335a;border-radius:6px;padding:8px 10px;margin-bottom:6px;">`;
                    h += `<div style="color:#e8c170;font-size:12px;">${tag}${r.score ? ' · 相关度'+r.score : ''}</div>`;
                    h += `<div style="color:#ccc;margin-top:4px;white-space:pre-wrap;">${r.text||''}</div></div>`;
                });
                box.innerHTML = h;
            } catch (e) { box.textContent = '出错了: ' + e.message; }
        }

        async function markGua(rid, correct) {
            const resp = await fetch('/api/guas/outcome', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({rid: rid, correct: correct})
            });
            await resp.json();
            loadGuas();
        }
        
        async function doPersonalAnalysis() {
            showResult('综合分析中，请稍候...');
            try {
                const id = (x) => document.getElementById(x);
                const data = {
                    year: parseInt(document.getElementById('pa-year').value),
                    month: parseInt(document.getElementById('pa-month').value),
                    day: parseInt(document.getElementById('pa-day').value),
                    hour: parseInt(document.getElementById('pa-hour').value),
                    goal: document.getElementById('pa-goal').value,
                    status: document.getElementById('pa-status').value,
                    problem: document.getElementById('pa-problem').value,
                    gender: id('pa-gender') ? id('pa-gender').value : '男',
                    rank: id('pa-rank') ? id('pa-rank').value : ''
                };
                const result = await postData('/api/personal', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }
        
        async function doHelpOthers() {
            showResult('分析中，请稍候...');
            try {
                const data = {
                    type: document.getElementById('ho-type').value,
                    my_year: parseInt(document.getElementById('ho-my-year').value),
                    my_month: parseInt(document.getElementById('ho-my-month').value),
                    my_day: parseInt(document.getElementById('ho-my-day').value),
                    my_hour: parseInt(document.getElementById('ho-my-hour').value),
                    other_year: parseInt(document.getElementById('ho-other-year').value),
                    other_month: parseInt(document.getElementById('ho-other-month').value),
                    other_day: parseInt(document.getElementById('ho-other-day').value),
                    other_hour: parseInt(document.getElementById('ho-other-hour').value),
                };
                const result = await postData('/api/help', data);
                showResult(result.report);
            } catch (e) {
                showResult('出错了: ' + e.message);
            }
        }
        function toggleHelp() {
            const m = document.getElementById('help-modal');
            m.style.display = (m.style.display === 'flex') ? 'none' : 'flex';
        }
    </script>

    <div id="help-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.75);z-index:999;align-items:center;justify-content:center;">
        <div style="background:#17172e;border:1px solid #3a3a5a;border-radius:14px;max-width:760px;width:92%;max-height:86vh;overflow-y:auto;padding:24px 28px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2 style="margin:0;color:#e8c170;">📖 木雷易术引擎 · 使用说明</h2>
                <button onclick="toggleHelp()" style="background:#3a3a5a;border:none;color:#fff;padding:6px 12px;border-radius:6px;cursor:pointer;">✕ 关闭</button>
            </div>
            <div style="line-height:1.7;font-size:0.86rem;color:#d8d8e8;">
                <p><b style="color:#e8c170;">一句话：</b>把心里的事交给「木雷易术」——可以<u>直接对话问大师</u>，也可以<u>起卦断卦出报告</u>，还能查八字、看风水、问国运。</p>

                <div style="background:#20203c;border-left:3px solid #e8c170;padding:10px 14px;border-radius:6px;margin:12px 0;">
                    <b style="color:#e8c170;">🧙 问卦（推荐先试这个）</b><br>
                    顶部第10个标签。想什么直接打字问，例如"今年财运怎么样""和合伙人闹矛盾怎么办"。回车或点"问大师"，AI结合易理作答，可<u>连续追问</u>。点"清空"开新话题。
                </div>

                <div style="background:#20203c;border-left:3px solid #8fd0ff;padding:10px 14px;border-radius:6px;margin:12px 0;">
                    <b style="color:#8fd0ff;">☯ 八大断卦模块怎么用</b><br>
                    每点一个标签，先填左边的输入区，再点下面的"开始/起卦/分析"按钮，右边出报告。具体：
                </div>

                <table style="width:100%;border-collapse:collapse;font-size:0.8rem;">
                    <tr style="background:#2a2a4a;"><th style="padding:6px 8px;text-align:left;">模块</th><th style="padding:6px 8px;text-align:left;">输入什么</th><th style="padding:6px 8px;text-align:left;">看什么结果</th></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>八字</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">出生年月日时、性别</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">四柱命盘、十神、大运流年、人生气运</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>相术</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">出生信息 + 面相照片</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">结合八字看气运走势、当下运势、改善建议</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>卜术</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">选起卦方式（报数/时间/铜钱）+ 问的事</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">六爻排盘、旺衰用神、吉凶断卦、应期，可一键DeepSeek大师解读</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>气运</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">梅花起卦（时间/报数）+ 问的事</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">体用生克、当前气运、吉凶应期、化解建议</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>奇门</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">时间、问的事（求财/事业/婚姻等）</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">奇门局象、用神落宫、吉凶格局、行动方向与解法</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>风水</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">住宅/办公方位、布局描述</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">宅卦分析、方位吉凶、布局诊断与调整建议</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>国运</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">（选年份）</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">皇极经世·国家世运与大事周期分析</td></tr>
                    <tr><td style="padding:6px 8px;border-bottom:1px solid #33334f;"><b>卦例</b></td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">（自动）</td><td style="padding:6px 8px;border-bottom:1px solid #33334f;">你所有起卦的历史记录与复盘统计</td></tr>
                    <tr><td style="padding:6px 8px;"><b>古籍</b></td><td style="padding:6px 8px;">搜索关键词，如"官鬼持世"</td><td style="padding:6px 8px;">在42部典籍与26.9万行卦例语料里检索原文，可溯源</td></tr>
                </table>

                <div style="background:#33281a;border-left:3px solid #e8c170;padding:10px 14px;border-radius:6px;margin:14px 0;">
                    <b style="color:#e8c170;">🔑 小技巧</b><br>
                    · 每个"开始/起卦"旁都有 <b>🧠 DeepSeek大师解读</b>，点它出白话解读。<br>
                    · 起完卦想分享给家人，用页面的 <b>分享链接</b>。<br>
                    · 断卦报告分五段：排盘 → 断卦 → 溯源（古籍原文）→ 语料佐证 → 白话解读。<br>
                    · 一切仅供参考、事在人为，术数为洞察之镜，非宿命。
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/liuyao', methods=['POST'])
def api_liuyao():
    data = request.json
    method = data.get('method', 'number')
    try:
        kwargs = dict(
            method=method,
            question_type=_s(data, 'question_type', '综合'),
            gender=_s(data, 'gender', '男')
        )
        if method == 'time':
            kwargs.update(year=_i(data.get('year')), month=_i(data.get('month')),
                          day=_i(data.get('day')), hour=_i(data.get('hour')))
        elif method == 'coin':
            kwargs['results'] = [_i(x) for x in (data.get('results') or [])]
        else:
            kwargs.update(num1=_i(data.get('num1')), num2=_i(data.get('num2')))
        # 月建日辰不再硬编码，由 qigua_and_duangua 按实际问卦时间自动取
        report = qigua_and_duangua(**kwargs)

        gua_visual = None
        try:
            from qigua import number_qigua, time_qigua, solar_to_lunar_time, qian_qian_method
            from liuyao_paipan import _LOOKUP_NEI_WAI
            from gua_trace import build_gua_visual
            if method == 'time':
                y_num, m_num, d_num, h_num = solar_to_lunar_time(
                    _i(data.get('year')), _i(data.get('month')), _i(data.get('day')), _i(data.get('hour')))
                ben, dong = time_qigua(y_num, m_num, d_num, h_num)
                desc = f"时间起卦{data.get('year')}-{data.get('month')}-{data.get('day')}"
            elif method == 'coin':
                ben, dong = qian_qian_method([_i(x) for x in (data.get('results') or [])])
                desc = "铜钱起卦"
            else:
                ben, dong = number_qigua(_i(data.get('num1')), _i(data.get('num2')))
                desc = f"报数起卦{data.get('num1')},{data.get('num2')}"
            nei, wai = _LOOKUP_NEI_WAI.get(ben, ("离", "乾"))
            gua_visual = build_gua_visual(ben, dong, nei, wai)
            # L：卦例自动记录（任意起卦方式）
            try:
                import db as _db, gua_record as _gr
                concl, conf = _gr.parse_report_meta(report)
                bian = _gr.lines_to_name(gua_visual['bian']['lines'])
                case_id = _db.record_gua_sql("六爻", _s(data,'question_type','综合'), ben, dong, bian,
                           concl, conf, desc)
                _db.log_consult("六爻", _s(data,'question_type','综合'), method, case_id, f"{ben}→{bian} {concl}")
            except Exception:
                pass
        except Exception:
            gua_visual = None
        return {"report": report, "gua_visual": gua_visual}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/meihua', methods=['POST'])
def api_meihua():
    data = request.json
    try:
        report = meihua_duangua(
            data.get('num1'), data.get('num2'), data.get('hour'), _s(data, 'question_type', '综合')
        )
        # N：梅花卦例记录
        try:
            from meihua import meihua_qigua
            from gua_record import parse_report_meta
            gua, _, _, dong = meihua_qigua(_i(data.get('num1')), _i(data.get('num2')), _i(data.get('hour')))
            concl, conf = parse_report_meta(report)
            import db as _db
            _db.record_gua_sql("梅花", _s(data, 'question_type'), gua, [dong] if dong else [], "", concl, conf,
                               f"梅花起卦{data.get('num1')},{data.get('num2')}")
            _db.log_consult("梅花", _s(data, 'question_type'), "报数", "", f"{gua} {concl}")
        except Exception:
            pass
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/qimen', methods=['POST'])
def api_qimen():
    data = request.json
    try:
        report = qimen_solve_problem(_s(data,'problem'))
        # N：奇门求测记录（无本卦，记结论）
        try:
            from gua_record import parse_report_meta
            import db as _db
            concl, conf = parse_report_meta(report)
            _db.record_gua_sql("奇门", _s(data,'problem'), "", [], "", concl, conf, "奇门遁甲求测")
            _db.log_consult("奇门", _s(data,'problem'), "式盘", "", concl)
        except Exception:
            pass
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/fengshui', methods=['POST'])
def api_fengshui():
    data = request.json
    try:
        report = fengshui_advice(_i(data.get('birth_year')), _s(data,'gender','男'), _s(data,'seat') or None, _s(data,'room'))
        # N：风水勘测记录
        try:
            from gua_record import parse_report_meta
            import db as _db
            concl, conf = parse_report_meta(report)
            _db.record_gua_sql("风水", f"{_s(data,'room')}布局", "", [], "", concl, conf, "风水布局建议")
            _db.log_consult("风水", f"{_s(data,'room')}布局", "堪舆", "", concl)
        except Exception:
            pass
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/guoyun', methods=['POST'])
def api_guoyun():
    data = request.json
    try:
        from huangji import huangji_analysis
        year = int(data.get('year', 2026))
        qtype = data.get('type', '国运')
        wx = data.get('wx') or None
        report = huangji_analysis(year, wx, qtype)
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/personal', methods=['POST'])
def api_personal():
    data = request.json
    try:
        report = personal_analysis(
            _i(data.get('year')), _i(data.get('month')), _i(data.get('day')), _i(data.get('hour')),
            _s(data, 'goal'), _s(data, 'status'), _s(data, 'problem'),
            _s(data, 'gender', '男'), _s(data, 'rank', '')
        )
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/help', methods=['POST'])
def api_help():
    data = request.json
    try:
        report = help_others_analysis(
            _i(data.get('my_year')), _i(data.get('my_month')), _i(data.get('my_day')), _i(data.get('my_hour')),
            _i(data.get('other_year')), _i(data.get('other_month')), _i(data.get('other_day')), _i(data.get('other_hour')),
            _s(data, 'type')
        )
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/mianxiang', methods=['POST'])
def api_mianxiang():
    data = request.json
    try:
        from mianxiang import mianxiang_analysis
        report = mianxiang_analysis(
            _i(data.get('year')), _i(data.get('month')), _i(data.get('day')), _i(data.get('hour')),
            data.get('shang', '天庭平满'), data.get('zhong', '中停平正'),
            data.get('xia', '下停中平'), data.get('qise', '黄明'),
            data.get('wg_mei', '眉清目秀'), data.get('wg_yan', '眼神明亮'),
            data.get('wg_bi', '鼻隆有肉'), data.get('wg_zui', '嘴形方正'),
            data.get('wg_er', '耳大有轮')
        )
        return {"report": report}
    except Exception as e:
        return {"report": f"出错了: {str(e)}"}


@app.route('/api/mianxiang_vision', methods=['POST'])
def api_mianxiang_vision():
    """AI识脸：上传照片，用视觉模型自动判面相特征"""
    data = request.json or {}
    b64 = _s(data, 'image')
    if not b64:
        return {"ok": False, "error": "未收到图片"}
    try:
        from llm_interpreter import deepseek_vision
        note = _s(data, 'note', '')
        r = deepseek_vision(b64, note)
        if not r.get('ok'):
            return {"ok": False, "error": r.get('error', '识脸失败')}
        face = r.get('face', {})
        _ALLOW = {
            'shang': {'天庭开阔', '天庭平满', '天庭低窄'},
            'zhong': {'鼻丰印明', '中停平正', '中停塌陷'},
            'xia': {'地阁圆润', '下停中平', '下停尖削'},
            'qise': {'红润', '黄明', '青黑', '苍白'},
            'wg_mei': {'眉清目秀', '眉浓眉扬', '眉疏而淡'},
            'wg_yan': {'眼神明亮', '眼形细长', '眼小神浊'},
            'wg_bi': {'鼻隆有肉', '鼻梁中正', '鼻小尖削'},
            'wg_zui': {'嘴形方正', '唇红齿白', '嘴角下垂'},
            'wg_er': {'耳大有轮', '耳垂厚实', '耳薄无垂'},
        }
        clean = {}
        for k, allowed in _ALLOW.items():
            v = face.get(k)
            clean[k] = v if v in allowed else next(iter(allowed))
        return {"ok": True, "face": clean, "desc": _s(face, 'desc', '')}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_feishu_webhook():
    import os
    w = os.environ.get("FEISHU_WEBHOOK")
    if w:
        return w.strip()
    wf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".feishu_webhook")
    if os.path.exists(wf):
        with open(wf, encoding="utf-8") as f:
            w = f.read().strip()
            if w:
                return w
    return ""


@app.route('/api/push', methods=['POST'])
def api_push():
    """把文本推送到飞书群机器人（webhook）。微信暂不支持。"""
    data = request.json
    text = data.get('text', '')
    webhook = get_feishu_webhook()
    if not webhook:
        return {"ok": False, "error": "未配置飞书webhook（.feishu_webhook 或环境变量 FEISHU_WEBHOOK）"}
    import urllib.request, json
    payload = {"msg_type": "text", "content": {"text": text[:2000]}}
    req = urllib.request.Request(webhook, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
        return {"ok": True, "resp": body}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.route('/api/push_status', methods=['GET'])
def api_push_status():
    return {"feishu": bool(get_feishu_webhook())}


def _share_html(title, date, body_lines):
    """生成移动端友好的分享页 HTML"""
    body = "".join(f"<div class='l'>{l}</div>" for l in body_lines)
    return f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
 body{{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#12121f;color:#ddd;}}
 .card{{max-width:520px;margin:24px auto;background:#1c1c33;border:1px solid #2e2e4a;border-radius:14px;padding:22px 20px;}}
 .hd{{text-align:center;font-size:22px;color:#e8c170;font-weight:600;}}
 .sub{{text-align:center;color:#9aa;font-size:12px;margin:6px 0 16px;}}
 .l{{background:#262640;border-left:3px solid #e8c170;border-radius:6px;padding:10px 12px;margin:8px 0;font-size:14px;line-height:1.6;}}
 .ft{{text-align:center;color:#777;font-size:11px;margin-top:18px;}}
 .ft2{{text-align:center;color:#e8c170;font-size:12px;margin-top:6px;font-weight:600;}}
</style></head><body>
<div class="card">
  <div class="hd">🌳 木雷易术</div>
  <div class="sub">{date}</div>
  {body}
  <div class="ft">由木雷易术引擎生成 · 仅供参考 · 事在人为</div>
  <div class="ft2">震为动，巽为入，动而入之，事乃可成</div>
</div></body></html>"""


@app.route('/share/<case_id>')
def share(case_id):
    try:
        import db
        recs = db.list_records_sql()
        r = next((x for x in recs if x.get('case_id') == case_id), None)
        if not r:
            return _share_html("未找到", "", ["该卦例不存在或已删除。"])
        from yijing_yaoci import YIJING_GUACI
        from gua_trace import FULL_NAME_TO_ORDER
        order = FULL_NAME_TO_ORDER.get(r.get('ben_gua', ''))
        guaci = YIJING_GUACI.get(order, {}).get('guaci', '') if order else ''
        lines = [
            f"📌 占问：{r.get('q_type','') or '—'}",
            f"🀄 本卦：{r.get('ben_gua','') or '—'}　→　变卦：{r.get('bian_gua','') or '—'}",
            f"⚡ 动爻：第{r.get('dong','') or '—'}爻动",
        ]
        if guaci:
            lines.append(f"📜 卦辞：{guaci}")
        lines += [
            f"🏆 断卦结论：{r.get('conclusion','') or '—'}（置信度：{r.get('confidence','') or '—'}）",
            f"📅 断于：{r.get('date','') or '—'}",
        ]
        return _share_html(f"卦例 {case_id}", r.get('date', ''), lines)
    except Exception as e:
        return _share_html("出错了", "", [str(e)])


@app.route('/share/today')
def share_today():
    try:
        import today
        t = today.today_hexagram()
        adv = today.today_advice(t['hexagram'])
        lines = [
            f"🀄 今日卦：{t['hexagram']}（第{t['order']}卦，第{(t['dong'] or ['-'])[0]}爻动）",
            f"📜 卦辞：{t.get('guaci','')}",
            f"✅ 今日宜：{adv.get('宜','')}",
            f"⛔ 今日忌：{adv.get('忌','')}",
        ]
        return _share_html("今日卦", t['date'], lines)
    except Exception as e:
        return _share_html("出错了", "", [str(e)])


@app.route('/api/today', methods=['GET'])
def api_today():
    try:
        import today
        t = today.today_hexagram()
        import db
        prof = db.get_profile_sql()
        day_wx = prof.get('day_wx') if prof else None
        adv = today.today_advice(t['hexagram'], day_wx)
        t.update({"advice": adv, "day_wx": day_wx})
        return t
    except Exception as e:
        return {"error": str(e)}


@app.route('/api/search', methods=['GET'])
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return {"results": []}
    try:
        k = min(int(request.args.get('k', 5)), 10)
    except Exception:
        k = 5
    # 云端精简版：本地无有效古籍索引时给出友好提示（不影响核心功能）
    import os as _os
    _idx = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "vector_index.pkl")
    _valid = _os.path.exists(_idx) and _os.path.getsize(_idx) > 1024 * 1024
    if not _valid:
        return {"q": q, "results": [{"type": "提示",
                "text": "云端精简版暂未内置古籍全文索引。完整古籍检索请使用本机版（木雷易术.app）。核心八字/相术/卜术/奇门/风水/国运功能均正常。"}]}
    results = []
    try:
        from vector_library import enhance
        for r in enhance(q, k=k):
            results.append({"type": "典籍正文", "book": r.get('book', ''),
                            "text": r.get('text', ''), "score": round(r.get('score', 0), 2)})
    except Exception:
        pass
    try:
        from text_corpus_lib import search_corpus
        for r in search_corpus(q, k=3):
            results.append({"type": "卦例语料", "text": r.get('text', ''), "score": None})
    except Exception:
        pass
    return {"q": q, "results": results}


@app.route('/api/visits', methods=['GET'])
def api_visits():
    try:
        import db
        return {"stats": db.visit_stats(), "rows": db.list_visits_grouped()}
    except Exception:
        return {"stats": {}, "rows": []}

@app.route('/api/visits/trust', methods=['POST'])
def api_visits_trust():
    d = request.get_json(silent=True) or {}
    ip = d.get('ip', ''); on = bool(d.get('is_family', True))
    try:
        import db
        return {"ok": db.set_family_ip(ip, on, d.get('note', ''))}
    except Exception:
        return {"ok": False}


@app.route('/api/llm_status', methods=['GET'])
def api_llm_status():
    try:
        from llm_interpreter import get_api_key
        return {"configured": bool(get_api_key())}
    except Exception:
        return {"configured": False}


MASTER_SYSTEM = """你是「木雷易术」的易学大师，深谙周易六爻、梅花易数、奇门遁甲、命理相法等传统术数。
用户会向你倾诉现实中的困惑：事业、财运、感情婚姻、健康、家庭、人际、决策、时运等。
请你：
1. 结合易理与术数智慧，给出有启发、有见地的分析和切实可行的建议；
2. 语言通俗、有温度、像与一位智慧长者对谈，不堆砌术语；
3. 始终强调「事在人为」，把术数当作洞察与启发的参考，而非宿命；
4. 不作绝对化、蛊惑性、恐吓性或过度承诺式的断言；
5. 若问及健康、法律、投资等专业问题，提醒寻求专业意见。
回答简洁有力，一般150~300字；用户追问时保持对话连贯，可结合前文继续深化。"""


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """问大师：多轮对话。入参 {messages:[{role,content},...]}，返回大师回复"""
    data = request.json
    msgs = data.get('messages') or []
    if not msgs:
        return {"ok": False, "error": "没有可问的内容"}
    # 控制长度：只保留最近 10 轮，避免超长
    history = msgs[-10:]
    payload = [{"role": "system", "content": MASTER_SYSTEM}] + history
    try:
        from llm_interpreter import deepseek_chat
        r = deepseek_chat(payload)
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.route('/api/llm_interpret', methods=['POST'])
def api_llm_interpret():
    data = request.json
    try:
        from llm_interpreter import duangua_with_llm, deepseek_interpret
        res = duangua_with_llm(
            data['ben_gua'], [int(x) for x in data.get('dong', [])],
            data.get('ri_gan', '甲'), data.get('ri_zhi', '子'),
            data.get('yue_zhi', '卯'), _s(data,'question_type','综合'))
        out = deepseek_interpret(res['llm_prompt'])
        if out['ok']:
            return {"ok": True, "text": out['text']}
        return {"ok": False, "error": out['error']}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.route('/api/guas', methods=['GET'])
def api_guas():
    try:
        import db
        recs = db.list_records_sql()
        stats = db.stats_sql()
        return {"records": recs, "stats": stats, "db": "sqlite"}
    except Exception as e:
        return {"records": [], "stats": {}, "error": str(e)}


@app.route('/api/guas/outcome', methods=['POST'])
def api_guas_outcome():
    data = request.json
    try:
        import db
        ok = db.update_outcome_sql(data['rid'], data.get('correct', '应验'))
        return {"ok": ok}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.route('/api/profile', methods=['GET', 'POST'])
def api_profile():
    import db
    if request.method == 'POST':
        d = request.json
        try:
            day_wx = db.save_profile_sql(
                int(d['year']), int(d['month']), int(d['day']), int(d['hour']),
                d.get('name', '我'), d.get('gender', '男'), d.get('rank', ''))
            return {"ok": True, "day_wx": day_wx}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"profile": db.get_profile_sql()}


@app.route('/api/consults', methods=['GET'])
def api_consults():
    try:
        import db
        return {"records": db.list_consults_sql(50)}
    except Exception as e:
        return {"records": [], "error": str(e)}


# ========== 象数重构 V2：对称性 / 历法（只读接口） ==========
@app.route('/api/symmetry', methods=['GET', 'POST'])
def api_symmetry():
    """卦象四视图：本/错/综/互（有动爻附变卦）。入参 gua / code / upper+lower，可选 dong"""
    try:
        import hex_codec as hc
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
        else:
            data = {k: request.args.get(k) for k in ('gua', 'code', 'upper', 'lower', 'dong')}
        dong = data.get('dong') or []
        if isinstance(dong, str):
            dong = [x.strip() for x in dong.replace('，', ',').split(',') if x.strip()]
        code = hc.encode_gua(gua=data.get('gua'), upper=data.get('upper'),
                             lower=data.get('lower'), code=data.get('code'))
        if code is None:
            return {"ok": False, "error": "请提供 gua / code / upper+lower 之一"}, 400
        return hc.four_views(code, dong)
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


@app.route('/api/calendar', methods=['GET', 'POST'])
def api_calendar():
    """天文历法：节气、太阳黄经、真太阳时、月相、岁星"""
    try:
        import calendar_astro as ca
        from datetime import datetime
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
        else:
            data = {k: request.args.get(k) for k in ('date', 'time', 'lng', 'lat')}
        now = datetime.now()
        date_str = data.get('date') or now.strftime('%Y-%m-%d')
        time_str = data.get('time') or now.strftime('%H:%M')
        lng = float(data.get('lng') or data.get('longitude') or 116.4)
        lat = float(data.get('lat') or data.get('latitude') or 39.9)
        return ca.compute(date_str, time_str, lng, lat)
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


if __name__ == '__main__':
    print("=" * 50)
    print("木雷易术引擎 - 本地Web服务")
    print("浏览器打开: http://localhost:5001")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)
