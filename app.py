import streamlit as st
import requests
import json
from datetime import datetime
import time
import random

# ==================== API 核心基础配置 ====================
DEEPSEEK_API_KEY = "sk-ebed2ac63e5a44d590dbebcb8346f9cd"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

MODELS = {
    'deepseek-chat': {'name': 'DeepSeek Chat', 'type': 'api', 'description': 'Official Flagship'},
    'deepseek-reasoning': {'name': 'DeepSeek R1', 'type': 'api', 'description': 'Official Reasoning'},
    'qwen2.5-coder:7b': {'name': 'Qwen2.5 Coder', 'type': 'ollama', 'description': 'Local Code Model'},
    'deepseek-r1:8b': {'name': 'DeepSeek R1 8B', 'type': 'ollama', 'description': 'Local Reasoning'}
}

# ==================== 全局页面配置 ====================
st.set_page_config(page_title="Code Hub", layout="wide", page_icon="C")

# ==================== 核心状态机状态持久化初始化 ====================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = 'admin'
if 'password' not in st.session_state: st.session_state.password = '123456'
if 'conversations' not in st.session_state: st.session_state.conversations = []
if 'current_conversation' not in st.session_state: st.session_state.current_conversation = None
if 'selected_model' not in st.session_state: st.session_state.selected_model = 'deepseek-chat'
if 'messages' not in st.session_state: st.session_state.messages = []
if 'theme' not in st.session_state: st.session_state.theme = 'black'
if 'chat_tab' not in st.session_state: st.session_state.chat_tab = 0
if 'show_guide' not in st.session_state: st.session_state.show_guide = False
if 'show_settings' not in st.session_state: st.session_state.show_settings = False

# ==================== 极客冷淡风三大背景主题 CSS ====================
BLACK_THEME = """
<style>
.stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%); min-height: 100vh; }
[data-testid="stAppViewContainer"] { background: transparent !important; }
[data-testid="stHeader"] { background: rgba(13, 17, 23, 0.9) !important; backdrop-filter: blur(10px); border-bottom: 1px solid #30363d; }
[data-testid="stSidebar"] { background: rgba(22, 27, 34, 0.95) !important; backdrop-filter: blur(10px); border-right: 1px solid #30363d; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select { background-color: #21262d !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; border-radius: 6px; }
.stButton>button { background: linear-gradient(90deg, #21262d 0%, #30363d 100%); color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 0.5rem 1rem; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }
.stButton>button:hover { border-color: #58a6ff; color: #58a6ff; box-shadow: 0 4px 12px rgba(88, 166, 255, 0.1); }
[data-testid="stChatMessage"] { background-color: transparent !important; }
.chat-bubble { background-color: #21262d; color: #c9d1d9; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border: 1px solid #30363d; }
.analysis-card { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid; background-color: rgba(33, 38, 45, 0.5); }
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
h1, h2, h3, h4, h5, h6 { color: #c9d1d9; font-weight: 600; }
p, span, div, label { color: #c9d1d9 !important; }
.stMetric label { color: #8b949e; }
.stMetric[data-testid="stMetricValue"] { color: #c9d1d9; }
</style>
"""

WHITE_THEME = """
<style>
.stApp { background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 50%, #f6f8fa 100%); min-height: 100vh; }
[data-testid="stAppViewContainer"] { background: transparent !important; }
[data-testid="stHeader"] { background: rgba(255, 255, 255, 0.9) !important; backdrop-filter: blur(10px); border-bottom: 1px solid #e1e4e8; }
[data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.95) !important; backdrop-filter: blur(10px); border-right: 1px solid #e1e4e8; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select { background-color: #ffffff !important; color: #24292f !important; border: 1px solid #e1e4e8 !important; border-radius: 6px; }
.stButton>button { background: linear-gradient(90deg, #ffffff 0%, #f6f8fa 100%); color: #24292f; border: 1px solid #e1e4e8; border-radius: 6px; padding: 0.5rem 1rem; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }
.stButton>button:hover { border-color: #0969da; color: #0969da; box-shadow: 0 4px 12px rgba(9, 105, 218, 0.1); }
[data-testid="stChatMessage"] { background-color: transparent !important; }
.chat-bubble { background-color: #f6f8fa; color: #24292f; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border: 1px solid #e1e4e8; }
.analysis-card { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid; background-color: rgba(246, 248, 250, 0.5); }
.highlight { border-color: #2da44e; }
.bug { border-color: #cf222e; }
.suggestion { border-color: #8250df; }
h1, h2, h3, h4, h5, h6 { color: #24292f; font-weight: 600; }
p, span, div, label { color: #24292f !important; }
.stMetric label { color: #656d76; }
.stMetric[data-testid="stMetricValue"] { color: #24292f; }
</style>
"""

STARRY_THEME = """
<style>
.stApp { background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%); min-height: 100vh; position: relative; overflow: hidden; }
[data-testid="stAppViewContainer"] { background: transparent !important; }
[data-testid="stHeader"] { background: rgba(9, 10, 15, 0.9) !important; backdrop-filter: blur(10px); border-bottom: 1px solid #30363d; }
[data-testid="stSidebar"] { background: rgba(9, 10, 15, 0.9) !important; backdrop-filter: blur(10px); border-right: 1px solid #30363d; }
.stars-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }
.star { position: absolute; background: white; border-radius: 50%; animation: twinkle 3s infinite ease-in-out; }
@keyframes twinkle { 0%, 100% { opacity: 0.3; transform: scale(1); } 50% { opacity: 1; transform: scale(1.2); } }
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select { background-color: rgba(33, 38, 45, 0.8) !important; color: #c9d1d9 !important; border: 1px solid #30363d !important; border-radius: 6px; backdrop-filter: blur(10px); }
.stButton>button { background: rgba(33, 38, 45, 0.6); color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 0.5rem 1rem; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }
.stButton>button:hover { border-color: #58a6ff; color: #58a6ff; box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2); }
[data-testid="stChatMessage"] { background-color: transparent !important; }
h1, h2, h3, h4, h5, h6 { color: #c9d1d9; font-weight: 600; }
p, span, div, label { color: #c9d1d9 !important; }
</style>
"""

# 分发渲染全局视觉主题
if st.session_state.theme == 'black':
    st.markdown(BLACK_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'white':
    st.markdown(WHITE_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'starry':
    st.markdown(STARRY_THEME, unsafe_allow_html=True)
    stars_html = '<div class="stars-container">'
    for i in range(60):
        x = f"{random.randint(0, 100)}%"
        y = f"{random.randint(0, 100)}%"
        size = f"{random.randint(1, 3)}px"
        stars_html += f'<div class="star" style="left:{x}; top:{y}; width:{size}; height:{size}; animation-duration:{random.randint(2, 5)}s;"></div>'
    stars_html += '</div>'
    st.markdown(stars_html, unsafe_allow_html=True)

# ==================== 网络请求核心网关 ====================
def call_deepseek_api(messages, model='deepseek-chat'):
    try:
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {DEEPSEEK_API_KEY}'}
        payload = {'model': model, 'messages': messages, 'temperature': 0.7}
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e: return f"API Engine Fault: {str(e)}"

def call_ollama_api(prompt, model='qwen2.5-coder:7b'):
    try:
        payload = {'model': model, 'prompt': prompt, 'stream': False}
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get('response', 'Empty feedback.')
    except Exception as e: return f"Local Runtime Offline: {str(e)}"

def get_ai_response(messages, model):
    model_info = MODELS.get(model, MODELS['deepseek-chat'])
    if model_info['type'] == 'api': return call_deepseek_api(messages, model)
    else:
        prompt = '\n'.join([f"{m['role']}: {m['content']}" for m in messages])
        return call_ollama_api(prompt, model)

def analyze_code(code, language):
    lines = code.split('\n')
    non_empty = len([l for l in lines if l.strip()])
    return {
        'highlights': [f"Supports {language} optimization profiles", "Structure parsed successfully"],
        'bugs': [],
        'suggestions': ["Consider functional refactoring for modular reuse"],
        'stats': {'total_lines': len(lines), 'effective_lines': non_empty, 'empty_lines': len(lines) - non_empty}
    }

# ==================== 顶部控制中心工具栏 (完美水平对齐方案) ====================
st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
# 重新划分配比，留出 4 份给左侧，其余 4 个组件各分 1.5 份，确保空间充裕
col_space_l, col_tb_model, col_tb_guide, col_tb_theme, col_tb_auth = st.columns([4, 1.8, 1.4, 1.4, 1.4])

with col_tb_model:
    # 移除上方默认多余的 label 文本占用，使用容器内联化，防止将后面的按钮顶下去
    st.session_state.selected_model = st.selectbox(
        "Model Selector",
        list(MODELS.keys()),
        format_func=lambda x: MODELS[x]['name'],
        index=list(MODELS.keys()).index(st.session_state.selected_model),
        label_visibility="collapsed",
        key="main_model_dropdown"
    )

with col_tb_guide:
    # 按钮默认无 Label，为了与带有 input/selectbox 的组件在视觉中轴线对齐，对其注入 4px 的微调补偿间距
    st.markdown('<div style="margin-top: 2px;"></div>', unsafe_allow_html=True)
    if st.button("Ollama Guide", use_container_width=True, key="toolbar_guide_trigger"):
        st.session_state.show_guide = True
        st.session_state.show_settings = False
        st.rerun()

with col_tb_theme:
    theme_options = {'black': 'Geek Black', 'white': 'Soft White', 'starry': 'Starry Sky'}
    selected_theme = st.selectbox(
        "Theme Selector",
        list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(st.session_state.theme),
        label_visibility="collapsed",
        key="toolbar_theme_trigger"
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

with col_tb_auth:
    st.markdown('<div style="margin-top: 2px;"></div>', unsafe_allow_html=True)
    if st.session_state.logged_in:
        if st.button("Logout", use_container_width=True, key="toolbar_logout_trigger"):
            st.session_state.logged_in = False
            st.session_state.show_settings = False
            st.rerun()
    else:
        with st.popover("Login", use_container_width=True):
            in_user = st.text_input("Username", placeholder="Identity credential")
            in_pass = st.text_input("Password", type="password", placeholder="Token secret")
            if st.button("Verify Credentials", use_container_width=True):
                if in_user == st.session_state.username and in_pass == st.session_state.password:
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Access denied")

# ==================== 全屏级别子页面路由拦截层 ====================
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 120px 20px;">
        <h1 style="color: #58a6ff; font-size: 3rem; letter-spacing: 1px;">Code Hub Gateway</h1>
        <p style="color: #8b949e; font-size: 1.1rem; margin-top: 15px;">Hybrid Compute Cluster Workspace</p>
        <p style="color: #8b949e; font-size: 0.9rem; margin-top: 5px;">Please unlock the terminal session template via upper right gate node.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if st.session_state.show_guide:
    st.markdown("<h2>Local Architecture Infrastructure Setup</h2>", unsafe_allow_html=True)
    if st.button("← Return to Workspace Panel Core", key="guide_back_action"):
        st.session_state.show_guide = False
        st.rerun()
    st.markdown("---")
    st.markdown("""
    ### Step 1: Initialize Compute Layer Core
    Fetch binaries archive environment layer from [ollama.com](https://ollama.com) and run configuration.
    ### Step 2: Fetch Optimized Models
    ```bash
    ollama run qwen2.5-coder:7b
    ```
    ```bash
    ollama run deepseek-r1:8b
    ```
    ### Step 3: Deployment Monitor Pipeline
    Verify regional port active link: `http://localhost:11434`
    """)
    st.stop()

if st.session_state.show_settings:
    st.markdown("<h2>Security Matrix Settings Center</h2>", unsafe_allow_html=True)
    if st.button("← Return to Workspace Panel Core", key="settings_back_action"):
        st.session_state.show_settings = False
        st.rerun()
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: m_user = st.text_input("Target Username Update", value=st.session_state.username)
    with c2: m_pass = st.text_input("Target Password Update", value=st.session_state.password, type="password")
    if st.button("Commit Credential Mutation Changes", key="save_settings_trigger"):
        if m_user.strip() and m_pass.strip():
            st.session_state.username = m_user
            st.session_state.password = m_pass
            st.session_state.show_settings = False
            st.success("Session signature updated successfully.")
            time.sleep(0.5)
            st.rerun()
    st.stop()

# ==================== 侧边栏扁平化面板设计 (宽度占比 2:8) ====================
with st.sidebar:
    st.markdown("<h3>Code Hub Core</h3>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("New Session Panel", use_container_width=True, key="side_new_chat"):
        st.session_state.messages = []
        st.session_state.current_conversation = None
        st.rerun()
    st.markdown("---")
    sh_query = st.text_input("Search History Cluster", placeholder="Filter identifiers...", label_visibility="collapsed")
    st.markdown("---")
    if st.session_state.conversations:
        for idx, conv in enumerate(st.session_state.conversations):
            if not sh_query or sh_query.lower() in conv['title'].lower():
                col_i, col_d = st.columns([4, 1])
                with col_i:
                    if st.button(f"{conv['title'][:16]}...", key=f"c_trigger_{idx}", use_container_width=True):
                        st.session_state.messages = conv['messages'].copy()
                        st.session_state.current_conversation = conv
                        st.session_state.chat_tab = conv.get('tab', 0)
                        st.rerun()
                with col_d:
                    if st.button("Clear", key=f"c_clear_{idx}"):
                        st.session_state.conversations.pop(idx)
                        if st.session_state.current_conversation == conv:
                            st.session_state.current_conversation = None
                            st.session_state.messages = []
                        st.rerun()
    else: st.info("Empty history cache registry pipeline.")
    st.markdown("---")
    if st.button("Security Settings Centre", use_container_width=True, key="side_security_toggle"):
        st.session_state.show_settings = True
        st.rerun()

# ==================== 主系统工作面板引擎分发 ====================
tab_workbench, tab_framework = st.tabs(["Code Hub Work Bench", "Cross-Language Framework Architect"])

# 标签页 1 流控结构
with tab_workbench:
    st.session_state.chat_tab = 0
    display_wb = st.container()
    with display_wb:
        for msg in st.session_state.messages:
            if msg.get("section", "workbench") == "workbench":
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
                if msg.get("analysis") and msg["role"] == "assistant":
                    an = msg["analysis"]
                    st.markdown("---")
                    cs = st.columns(3)
                    with cs[0]: st.metric("Total Lines", an['stats']['total_lines'])
                    with cs[1]: st.metric("Effective Lines", an['stats']['effective_lines'])
                    with cs[2]: st.metric("Empty Lines", an['stats']['empty_lines'])
                    with st.expander("Analysis Insights Report", expanded=True):
                        for h in an.get('highlights', []): st.markdown(f'<div class="analysis-card highlight">{h}</div>', unsafe_allow_html=True)
                        for s in an.get('suggestions', []): st.markdown(f'<div class="analysis-card suggestion">{s}</div>', unsafe_allow_html=True)

    query_wb = st.chat_input("Paste disorganized source artifacts or assign modification tasks here...", key="chat_input_wb")
    if query_wb:
        st.session_state.messages.append({"role": "user", "content": query_wb, "section": "workbench"})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("section", "workbench") == "workbench":
        with display_wb:
            with st.chat_message("user"): st.markdown(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                with st.spinner("Processing architectural refactoring logic..."):
                    sys_m = {"role": "system", "content": "You are Code Hub Workbench expert. Refactor provided structures and print optimized blocks clearly."}
                    flow = [m for m in st.session_state.messages if m.get("section", "workbench") == "workbench"]
                    res = get_ai_response([sys_m] + [{"role": m["role"], "content": m["content"]} for m in flow], st.session_state.selected_model)
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res, "section": "workbench"})
                    if "```" in res:
                        try:
                            blocks = res.split("```")
                            lang = blocks[1].split('\n')[0].strip() or "python"
                            code_content = '\n'.join(blocks[1].split('\n')[1:])
                            st.session_state.messages[-1]["analysis"] = analyze_code(code_content, lang)
                        except: pass
                    if st.session_state.current_conversation is None:
                        st.session_state.conversations.insert(0, {'title': f"Refactor {datetime.now().strftime('%H:%M')}", 'messages': st.session_state.messages.copy(), 'tab': 0})
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else: st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()

# 标签页 2 流控结构
with tab_framework:
    st.session_state.chat_tab = 1
    display_arch = st.container()
    with display_arch:
        for msg in st.session_state.messages:
            if msg.get("section") == "architect":
                with st.chat_message(msg["role"]): st.markdown(msg["content"])

    query_arch = st.chat_input("Describe your custom high-concurrency cross-platform blueprint systems requirements...", key="chat_input_arch")
    if query_arch:
        st.session_state.messages.append({"role": "user", "content": query_arch, "section": "architect"})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("section") == "architect":
        with display_arch:
            with st.chat_message("user"): st.markdown(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                with st.spinner("Compiling cross-language full-stack component blueprint trees..."):
                    sys_m = {"role": "system", "content": "You are Code Hub Full-Stack Framework Architect. Design comprehensive file systems trees and mark code blocks cleanly."}
                    flow = [m for m in st.session_state.messages if m.get("section") == "architect"]
                    res = get_ai_response([sys_m] + [{"role": m["role"], "content": m["content"]} for m in flow], st.session_state.selected_model)
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res, "section": "architect"})
                    if st.session_state.current_conversation is None:
                        st.session_state.conversations.insert(0, {'title': f"Architecture {datetime.now().strftime('%H:%M')}", 'messages': st.session_state.messages.copy(), 'tab': 1})
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else: st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()
