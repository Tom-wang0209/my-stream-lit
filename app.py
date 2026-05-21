import streamlit as st
import requests
import json
from datetime import datetime
import time
import random

# ==================== API 配置 ====================
DEEPSEEK_API_KEY = "sk-ebed2ac63e5a44d590dbebcb8346f9cd"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# 模型配置
MODELS = {
    'deepseek-chat': {'name': ' 🌐  DeepSeek Chat', 'type': 'api', 'description': '官方旗舰模型'},
    'deepseek-reasoning': {'name': ' 🌐  DeepSeek R1', 'type': 'api', 'description': '官方推理模型'},
    'qwen2.5-coder:7b': {'name': ' 💻  Qwen2.5 Coder', 'type': 'ollama', 'description': '本地代码模型'},
    'deepseek-r1:8b': {'name': ' 💻  DeepSeek R1 8B', 'type': 'ollama', 'description': '本地推理模型'}
}

# ==================== 页面配置 ====================
st.set_page_config(page_title="Code Hub", layout="wide", page_icon=" 💻 ")

# ==================== Session State 初始化 ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'password' not in st.session_state:
    st.session_state.password = '123456'
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = None
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'deepseek-chat'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'black'
if 'chat_tab' not in st.session_state:
    st.session_state.chat_tab = 0
if 'new_chat' not in st.session_state:
    st.session_state.new_chat = 0

# ==================== 主题样式 ====================
BLACK_THEME = """
<style>
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] {
    background: transparent !important;
}
[data-testid="stHeader"] {
    background: rgba(13, 17, 23, 0.8) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #30363d;
}
[data-testid="stSidebar"] {
    background: rgba(22, 27, 34, 0.95) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid #30363d;
}
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
}
.stButton>button {
    background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
}
[data-testid="stChatMessage"] {
    background-color: transparent !important;
}
.chat-bubble {
    background-color: #21262d;
    color: #c9d1d9;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}
.analysis-card {
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
}
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
h1, h2, h3, h4, h5, h6 { color: #c9d1d9; }
p, span, div { color: #c9d1d9; }
</style>
"""

WHITE_THEME = """
<style>
.stApp {
    background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 50%, #f6f8fa 100%);
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] {
    background: transparent !important;
}
[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #e1e4e8;
}
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid #e1e4e8;
}
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select {
    background-color: #ffffff !important;
    color: #24292f !important;
    border: 1px solid #e1e4e8 !important;
}
.stButton>button {
    background: linear-gradient(90deg, #2da44e 0%, #2ea043 100%);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
}
[data-testid="stChatMessage"] {
    background-color: transparent !important;
}
.chat-bubble {
    background-color: #f6f8fa;
    color: #24292f;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}
.analysis-card {
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
}
.highlight { border-color: #2da44e; }
.bug { border-color: #cf222e; }
.suggestion { border-color: #8250df; }
h1, h2, h3, h4, h5, h6 { color: #24292f; }
p, span, div { color: #24292f; }
</style>
"""

STARRY_THEME = """
<style>
.stApp {
    background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
    min-height: 100vh;
    position: relative;
    overflow: hidden;
}
[data-testid="stAppViewContainer"] {
    background: transparent !important;
}
[data-testid="stHeader"] {
    background: rgba(9, 10, 15, 0.8) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #30363d;
}
[data-testid="stSidebar"] {
    background: rgba(9, 10, 15, 0.9) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid #30363d;
}
.stars-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
}
.star {
    position: absolute;
    background: white;
    border-radius: 50%;
    animation: twinkle 3s infinite ease-in-out;
}
@keyframes twinkle {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); }
}
.shooting-star {
    position: absolute;
    width: 100px;
    height: 2px;
    background: linear-gradient(90deg, white, transparent);
    animation: shoot 3s infinite ease-in-out;
    opacity: 0;
}
@keyframes shoot {
    0% { transform: translateX(0) translateY(0); opacity: 0; }
    10% { opacity: 1; }
    100% { transform: translateX(-500px) translateY(500px); opacity: 0; }
}
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select {
    background-color: rgba(33, 38, 45, 0.8) !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
}
.stButton>button {
    background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
}
[data-testid="stChatMessage"] {
    background-color: transparent !important;
}
.chat-bubble {
    background-color: rgba(33, 38, 45, 0.8);
    color: #c9d1d9;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    backdrop-filter: blur(10px);
}
.analysis-card {
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
    background-color: rgba(33, 38, 45, 0.8);
}
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
h1, h2, h3, h4, h5, h6 { color: #c9d1d9; }
p, span, div { color: #c9d1d9; }
</style>
"""

# 应用主题样式与样式包裹保护
if st.session_state.theme == 'black':
    st.markdown(BLACK_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'white':
    st.markdown(WHITE_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'starry':
    st.markdown(STARRY_THEME, unsafe_allow_html=True)
    
    # 生成星空动态背景
    stars_html = '<div class="stars-container">'
    for i in range(100):
        x = f"{random.randint(0, 100)}%"
        y = f"{random.randint(0, 100)}%"
        size = f"{random.randint(1, 3)}px"
        delay = f"{random.randint(0, 3)}s"
        duration = f"{random.randint(2, 5)}s"
        stars_html += f'<div class="star" style="left:{x}; top:{y}; width:{size}; height:{size}; animation-delay:{delay}; animation-duration:{duration};"></div>'
    for i in range(3):
        x = f"{random.randint(50, 100)}%"
        y = f"{random.randint(0, 50)}%"
        delay = f"{random.randint(0, 10)}s"
        stars_html += f'<div class="shooting-star" style="left:{x}; top:{y}; animation-delay:{delay};"></div>'
    stars_html += '</div>'
    st.markdown(stars_html, unsafe_allow_html=True)

# ==================== API 调用函数 ====================
def call_deepseek_api(messages, model='deepseek-chat', temperature=0.7):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
        }
        payload = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': 4000
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return " ⚠️  请求超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        return f" ❌  API 调用失败: {str(e)}"
    except Exception as e:
        return f" ❌  未知错误: {str(e)}"

def call_ollama_api(prompt, model='qwen2.5-coder:7b'):
    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '未获得响应')
    except requests.exceptions.ConnectionError:
        return " ❌  无法连接到本地 Ollama 服务。请确保 Ollama 已运行（运行 `ollama serve`）"
    except requests.exceptions.Timeout:
        return " ⚠️  本地模型响应超时，请稍后重试"
    except Exception as e:
        return f" ❌  本地模型调用失败: {str(e)}"

def get_ai_response(messages, model):
    model_info = MODELS.get(model, MODELS['deepseek-chat'])
    if model_info['type'] == 'api':
        return call_deepseek_api(messages, model)
    else:
        prompt = '\n'.join([f"{m['role']}: {m['content']}" for m in messages])
        return call_ollama_api(prompt, model)

def analyze_code(code, language):
    lines = code.split('\n')
    non_empty = len([l for l in lines if l.strip()])
    highlights = []
    bugs = []
    suggestions = []
    
    if non_empty > 50:
        highlights.append(f" 🚀  代码规模较大 ({len(lines)} 行)，建议拆分为模块化管理")
    highlights.append(f" ✨  支持 {language} 语言特性优化")
    highlights.append(f" 📊  代码复杂度评估: 中等")
    
    if "print" in code.lower():
        bugs.append({
            'line': max(1, code.lower().index("print") // (len(code) // max(1, len(lines)))),
            'issue': '调试语句未清理',
            'reason': 'print 语句可能泄露敏感信息或影响性能'
        })
    if "=" * 3 in code or "TODO" in code:
        bugs.append({
            'line': 1,
            'issue': '遗留标记未处理',
            'reason': '发现 === 或 TODO 标记，需要进一步处理'
        })
        
    suggestions.append(f" 💡  可使用列表推导式简化循环逻辑")
    suggestions.append(f" 💡  建议添加类型注解提升代码可读性")
    suggestions.append(f" 💡  考虑使用上下文管理器优化资源管理")
    
    return {
        'highlights': highlights,
        'bugs': bugs,
        'suggestions': suggestions,
        'stats': {
            'total_lines': len(lines),
            'effective_lines': non_empty,
            'empty_lines': len(lines) - non_empty
        }
    }

# ==================== 右上角高级工具栏工具映射 ====================
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
col_spacer, col_ollama, col_theme, col_login, col_spacer2 = st.columns([3, 1.2, 1.5, 1.5, 3])

with col_ollama:
    with st.popover(" 📖  新手引导", use_container_width=True):
        st.markdown("""
        ###  📥  步骤一：下载安装 Ollama
        1. 访问 [ollama.com](https://ollama.com)
        2. 下载对应系统版本并运行安装
        
        ###  🤖  步骤二：启动本地算力模型
        在你的电脑终端 (CMD / Terminal) 分别输入：
        ```bash
        ollama run qwen2.5-coder:7b
        ```
        ```bash
        ollama run deepseek-r1:8b
        ```
        
        ###  🔧  步骤三：服务健康检查
        - 确保本地运行：浏览器打开 http://localhost:11434 
        - 查看已下载列表：终端输入 `ollama list`
        """)

with col_theme:
    theme_options = {
        'black': ' 🖤  极客黑色',
        'white': ' 🤍  柔和白色',
        'starry': ' 🌌  动态星空'
    }
    selected_theme = st.selectbox(
        "背景主题切换",
        list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(st.session_state.theme),
        label_visibility="collapsed"
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

with col_login:
    if st.session_state.logged_in:
        if st.button(" 🏃‍♂️  Log Out", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        with st.popover(" 🔑  账户登录", use_container_width=True):
            username = st.text_input("账号", placeholder="请输入账号", key="login_username")
            password = st.text_input("密码", type="password", placeholder="请输入密码", key="login_password")
            if st.button("立即安全登录", use_container_width=True, key="login_submit"):
                if username == "admin" and password == st.session_state.password:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("账号或密码错误")

# ==================== 登录拦截检查 ====================
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 120px 20px;">
        <h1 style="color: #58a6ff; font-size: 3.5rem;"> 💻  Code Hub</h1>
        <p style="color: #8b949e; font-size: 1.3rem; margin-top: 20px;">
            私有云端智能代码工作台 · 混合混合动力驱动
        </p>
        <p style="color: #8b949e; margin-top: 15px; font-weight: bold;">
            请点击右上角  🔑  登录开始您的极客之旅
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==================== 后台主界面布局 (2:8 黄金比例) ====================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #58a6ff; font-size: 2rem; margin-bottom:0;"> 💻  Code Hub</h1>
        <p style="color: #8b949e; font-size: 0.85rem;">混合算力极客控制台</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button(" ➕  New Chat", use_container_width=True, key="new_chat_btn"):
        st.session_state.messages = []
        st.session_state.current_conversation = None
        st.session_state.new_chat += 1
        st.rerun()
        
    st.markdown("---")
    search_query = st.text_input(" 🔍  过滤搜索对话历史", placeholder="输入关键词...", key="history_search")
    st.markdown("---")
    
    # 历史记录单条删改管理
    if st.session_state.conversations:
        for idx, conv in enumerate(st.session_state.conversations):
            if search_query.lower() in conv['title'].lower():
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f" 💬  {conv['title'][:15]}...", key=f"conv_{idx}", use_container_width=True):
                        st.session_state.messages = conv['messages'].copy()
                        st.session_state.current_conversation = conv
                        st.session_state.chat_tab = conv.get('tab', 0)
                        st.rerun()
                with col2:
                    if st.button(" 🗑️ ", key=f"del_{idx}"):
                        st.session_state.conversations.pop(idx)
                        if st.session_state.current_conversation == conv:
                            st.session_state.current_conversation = None
                            st.session_state.messages = []
                        st.rerun()
    else:
        st.info("暂无历史会话记录")

# 动态模型驱动选择配置
col_title_space, col_model_div = st.columns([6, 4])
with col_model_div:
    selected_model = st.selectbox(
        "动力引擎模型选择",
        list(MODELS.keys()),
        format_func=lambda x: f"{MODELS[x]['name']} ({MODELS[x]['description']})",
        index=list(MODELS.keys()).index(st.session_state.selected_model),
        key="model_selector"
    )
    st.session_state.selected_model = selected_model

# 核心功能主界面双标签页
tab1, tab2 = st.tabs([" 🔧  代码重构与修复", " 🏗️  跨语言全栈架构设计器"])

# ==================== 标签页 1: 代码重构与修复 ====================
with tab1:
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg.get("tab", 0) == 0:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                
                # 历史剖析面板持久化回调
                if msg.get("analysis") and msg["role"] == "assistant":
                    analysis = msg["analysis"]
                    st.markdown("---")
                    st.markdown("###  🔍  代码性能深度剖析报告")
                    cols = st.columns(3)
                    with cols[0]: st.metric("总行数", analysis['stats']['total_lines'])
                    with cols[1]: st.metric("有效代码行", analysis['stats']['effective_lines'])
                    with cols[2]: st.metric("空行数量", analysis['stats']['empty_lines'])
                    
                    with st.expander(" ✨  重构代码亮点亮点", expanded=True):
                        for h in analysis.get('highlights', []):
                            st.markdown(f'<div class="analysis-card highlight">{h}</div>', unsafe_allow_html=True)
                    with st.expander(" 🪲  潜在 Bug 定位与根因剖析"):
                        if analysis.get('bugs'):
                            for b in analysis['bugs']:
                                st.markdown(f'<div class="analysis-card bug"><strong>第 {b["line"]} 行: {b["issue"]}</strong><br><span style="color:#8b949e">根因: {b["reason"]}</span></div>', unsafe_allow_html=True)
                        else:
                            st.info(" 🎉  未发现明显底层逻辑隐患！")
                    with st.expander(" 💡  架构精简演进建议"):
                        for s in analysis.get('suggestions', []):
                            st.markdown(f'<div class="analysis-card suggestion">{s}</div>', unsafe_allow_html=True)

    # 经典标准流底部对话输入框架
    user_input = st.chat_input("在此处粘贴您的混乱代码或输入追加优化要求...", key="chat_input_tab1")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input, "tab": 0})
        st.rerun()

    # 触发 AI 后端响应渲染机制
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("tab") == 0:
        with chat_container:
            # 渲染当前用户最新输入
            with st.chat_message("user"):
                st.markdown(st.session_state.messages[-1]["content"])
            
            with st.chat_message("assistant"):
                with st.spinner(f" ⚙️  正在调用 {MODELS[st.session_state.selected_model]['name']} 进行代码深度重构..."):
                    system_message = {
                        "role": "system",
                        "content": "你是 Code Hub 的全栈重构专家。优化代码结构与命名，修复 bug 并用特定代码块标注语言输出完整重构代码。"
                    }
                    # 过滤当前 Tab 下的对话消息流作为上下文
                    tab_messages = [m for m in st.session_state.messages if m.get("tab", 0) == 0]
                    api_messages = [{"role": m["role"], "content": m["content"]} for m in tab_messages]
                    
                    response = get_ai_response([system_message] + api_messages, st.session_state.selected_model)
                    st.markdown(response)
                    
                    # 剥离代码块执行静态深度指标剖析
                    analysis_data = None
                    lang_type = "Python"
                    if "```" in response:
                        try:
                            block = response.split("```")[1]
                            if '\n' in block:
                                lang_type = block.split('\n')[0].strip() or "Python"
                                raw_code = '\n'.join(block.split('\n')[1:])
                                if raw_code.strip():
                                    analysis_data = analyze_code(raw_code, lang_type)
                        except Exception:
                            pass
                            
                    # 保存 Assistant 响应至状态机缓存
                    new_msg = {"role": "assistant", "content": response, "tab": 0}
                    if analysis_data:
                        new_msg["analysis"] = analysis_data
                        new_msg["language"] = lang_type
                    st.session_state.messages.append(new_msg)
                    
                    # 刷新并生成持久化会话归档历史
                    if st.session_state.current_conversation is None:
                        t_stamp = datetime.now().strftime('%H:%M')
                        st.session_state.conversations.insert(0, {
                            'title': f"代码重构 {t_stamp}",
                            'messages': st.session_state.messages.copy(),
                            'tab': 0
                        })
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else:
                        st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()

# ==================== 标签页 2: 跨语言全栈架构设计器 ====================
with tab2:
    arch_container = st.container()
    with arch_container:
        for msg in st.session_state.messages:
            if msg.get("tab", 0) == 1:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # 底部对话区下移对齐
    user_arch_input = st.chat_input("请输入您的一句话需求（例如：设计一个 C++ 游戏网关 + Go 业务微服务的分布式框架）", key="chat_input_tab2")
    if user_arch_input:
        st.session_state.messages.append({"role": "user", "content": user_arch_input, "tab": 1})
        st.rerun()

    # 触发全栈架构大师响应流
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("tab") == 1:
        with arch_container:
            with st.chat_message("user"):
                st.markdown(st.session_state.messages[-1]["content"])
                
            with st.chat_message("assistant"):
                with st.spinner(f" 🏗️  {MODELS[st.session_state.selected_model]['name']} 正在进行跨编译语言全栈蓝图规划..."):
                    system_message = {
                        "role": "system",
                        "content": "你是 Code Hub 全栈架构设计专家。请根据需求提供跨语言架构、清晰的项目目录树、模块分工、技术栈选型与部署方案。目录请用标准 Markdown 树状结构展示。"
                    }
                    tab_messages = [m for m in st.session_state.messages if m.get("tab", 0) == 1]
                    api_messages = [{"role": m["role"], "content": m["content"]} for m in tab_messages]
                    
                    response = get_ai_response([system_message] + api_messages, st.session_state.selected_model)
                    st.markdown(response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response, "tab": 1})
                    
                    # 归档持久化历史
                    if st.session_state.current_conversation is None:
                        t_stamp = datetime.now().strftime('%H:%M')
                        st.session_state.conversations.insert(0, {
                            'title': f"架构设计 {t_stamp}",
                            'messages': st.session_state.messages.copy(),
                            'tab': 1
                        })
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else:
                        st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()
