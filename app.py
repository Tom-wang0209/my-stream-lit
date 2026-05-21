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

# 统一模型元数据驱动字典
MODELS = {
    'deepseek-chat': {'name': 'DeepSeek Chat', 'type': 'api', 'description': '官方旗舰模型'},
    'deepseek-reasoning': {'name': 'DeepSeek R1', 'type': 'api', 'description': '官方推理模型'},
    'qwen2.5-coder:7b': {'name': 'Qwen2.5 Coder', 'type': 'ollama', 'description': '本地代码模型'},
    'deepseek-r1:8b': {'name': 'DeepSeek R1 8B', 'type': 'ollama', 'description': '本地推理模型'}
}

# ==================== 全局页面配置 ====================
st.set_page_config(page_title="Code Hub", layout="wide")

# ==================== 核心状态机状态持久化初始化 ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = 'admin'
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
if 'show_guide' not in st.session_state:
    st.session_state.show_guide = False
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False

# ==================== 纯净极客风三大背景主题 CSS ====================
BLACK_THEME = """
<style>
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] { background: transparent !important; }
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
    background: linear-gradient(90deg, #21262d 0%, #30363d 100%);
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
}
.stButton>button:hover {
    border-color: #58a6ff;
    color: #58a6ff;
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
    background-color: #161b22;
}
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
h1, h2, h3, h4, h5, h6, p, span, div, label { color: #c9d1d9 !important; }
</style>
"""

WHITE_THEME = """
<style>
.stApp {
    background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 50%, #f6f8fa 100%);
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] { background: transparent !important; }
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
    background: linear-gradient(90deg, #ffffff 0%, #f6f8fa 100%);
    color: #24292f;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
}
.stButton>button:hover {
    border-color: #0969da;
    color: #0969da;
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
    background-color: #ffffff;
}
.highlight { border-color: #1a7f37; }
.bug { border-color: #cf222e; }
.suggestion { border-color: #8250df; }
h1, h2, h3, h4, h5, h6, p, span, div, label { color: #24292f !important; }
</style>
"""

STARRY_THEME = """
<style>
.stApp {
    background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] { background: transparent !important; }
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
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select {
    background-color: rgba(33, 38, 45, 0.8) !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
}
.stButton>button {
    background: rgba(33, 38, 45, 0.6);
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
}
.stButton>button:hover {
    border-color: #58a6ff;
    color: #58a6ff;
}
h1, h2, h3, h4, h5, h6, p, span, div, label { color: #c9d1d9 !important; }
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
    for _ in range(60):
        x = f"{random.randint(0, 100)}%"
        y = f"{random.randint(0, 100)}%"
        size = f"{random.randint(1, 3)}px"
        duration = f"{random.randint(2, 5)}s"
        stars_html += f'<div class="star" style="left:{x}; top:{y}; width:{size}; height:{size}; animation-duration:{duration};"></div>'
    stars_html += '</div>'
    st.markdown(stars_html, unsafe_allow_html=True)

# ==================== 云端与本地混合算力请求网关 ====================
def call_deepseek_api(messages, model='deepseek-chat'):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
        }
        payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.7
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"API Endpoint Connection Failed: {str(e)}"

def call_ollama_api(prompt, model='qwen2.5-coder:7b'):
    try:
        payload = {'model': model, 'prompt': prompt, 'stream': False}
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get('response', 'Empty compute feedback.')
    except Exception as e:
        return f"Local Ollama cluster offline. Please check terminal status: {str(e)}"

def get_ai_response(messages, model):
    model_info = MODELS.get(model, MODELS['deepseek-chat'])
    if model_info['type'] == 'api':
        return call_deepseek_api(messages, model)
    else:
        prompt = '\n'.join([f"{m['role']}: {m['content']}" for m in messages])
        return call_ollama_api(prompt, model)

def analyze_code_structure(code):
    lines = code.split('\n')
    return {
        'stats': {
            'total_lines': len(lines), 
            'effective_lines': len([l for l in lines if l.strip()]), 
            'empty_lines': len([l for l in lines if not l.strip()])
        }
    }

# ==================== 顶端极客高级控制工具栏 (对齐右上角官方 Share 组件) ====================
st.markdown('<div style="position: relative; z-index: 999; margin-top: -10px;">', unsafe_allow_html=True)
col_toolbar_spacer, col_btn_guide, col_sel_theme, col_btn_auth = st.columns([5, 1.5, 1.5, 1.5])

with col_btn_guide:
    if st.button("Ollama Guide", use_container_width=True, key="toolbar_guide"):
        st.session_state.show_guide = not st.session_state.show_guide
        st.session_state.show_settings = False
        st.rerun()

with col_sel_theme:
    theme_map = {'black': 'Geek Black', 'white': 'Soft White', 'starry': 'Starry Sky'}
    selected_theme = st.selectbox(
        "Theme Switcher", 
        list(theme_map.keys()), 
        format_func=lambda x: theme_map[x], 
        index=list(theme_map.keys()).index(st.session_state.theme), 
        label_visibility="collapsed",
        key="toolbar_theme"
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

with col_btn_auth:
    if st.session_state.logged_in:
        if st.button("Log Out", use_container_width=True, key="toolbar_logout"):
            st.session_state.logged_in = False
            st.session_state.show_settings = False
            st.rerun()
    else:
        st.markdown("<div style='text-align: center; line-height: 38px; color: #8b949e; font-size: 0.9rem; border: 1px dashed #30363d; border-radius: 6px;'>Session Locked</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==================== 全屏级别子页面路由拦截层 ====================
# 1. 登录会话主拦截
if not st.session_state.logged_in:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    col_login_l, col_login_box, col_login_r = st.columns([1.5, 1, 1.5])
    with col_login_box:
        st.markdown("<h2 style='text-align: center; margin-bottom: 30px; letter-spacing: 1px;'>Code Hub Gateway</h2>", unsafe_allow_html=True)
        in_user = st.text_input("Operator Username", placeholder="Input root identity credential", key="login_field_user")
        in_pass = st.text_input("Access Token Secret", type="password", placeholder="Input token payload", key="login_field_pass")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Verify Credentials", use_container_width=True, key="login_submit_trigger"):
            if in_user == st.session_state.username and in_pass == st.session_state.password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Authentication rejected: Invalid credential hash")
    st.stop()

# 2. 沉浸式全屏 Ollama 指引子框架
if st.session_state.show_guide:
    st.markdown("<div style='padding: 30px 50px;'>", unsafe_allow_html=True)
    if st.button("← Return to Workspace Core", key="guide_back_btn"):
        st.session_state.show_guide = False
        st.rerun()
    
    st.markdown("""
    ## Local Computational Intelligence Runtime Architecture Guide
    
    ---
    
    ### Step 1: Deploy Engine Substrate
    Fetch the corresponding host environment installation binaries package directly from the primary gateway [ollama.com](https://ollama.com) and execute cross-platform provisioning setup.
    
    ### Step 2: Initialize Local Model Shards via Terminal Core
    Open your native shell orchestrator or command matrix and pull down the optimized operational weights using the following operations:
    ```bash
    ollama run qwen2.5-coder:7b
    ```
    ```bash
    ollama run deepseek-r1:8b
    ```
    
    ### Step 3: Daemon Monitoring Check
    Confirm the connection hub adapter pipeline is working under backend address: `http://localhost:11434`. 
    Once active, Code Hub's hardware selector box will automatically ingest and parse requests through your regional compute nodes.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==================== 侧边栏：历史会话结构设计 (宽度比例 2:8) ====================
with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0;'>Code Hub</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e; font-size:0.8rem; margin-top:0;'>Hybrid Compute Matrix</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("New Session Panel", use_container_width=True, key="sidebar_new_chat"):
        st.session_state.messages = []
        st.session_state.current_conversation = None
        st.rerun()
        
    st.markdown("---")
    hist_search = st.text_input("Filter Token Query", placeholder="Search history clusters...", key="sidebar_search_field", label_visibility="collapsed")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # 会话槽扁平化列表管理
    for idx, conv in enumerate(st.session_state.conversations):
        if not hist_search or hist_search.lower() in conv['title'].lower():
            col_sidebar_item, col_sidebar_action = st.columns([4, 1])
            with col_sidebar_item:
                if st.button(conv['title'], key=f"sidebar_item_trigger_{idx}", use_container_width=True):
                    st.session_state.messages = conv['messages'].copy()
                    st.session_state.current_conversation = conv
                    st.rerun()
            with col_sidebar_action:
                if st.button("Clear", key=f"sidebar_item_delete_{idx}", use_container_width=True):
                    st.session_state.conversations.pop(idx)
                    if st.session_state.current_conversation == conv:
                        st.session_state.current_conversation = None
                        st.session_state.messages = []
                    st.rerun()
                    
    st.markdown("---")
    if st.button("Security Credentials Management", use_container_width=True, key="sidebar_security_settings"):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

# ==================== 动态凭证安全修改模块面板 ====================
if st.session_state.show_settings:
    st.markdown("### Profile Security Management Center")
    col_settings_u, col_settings_p = st.columns(2)
    with col_settings_u:
        modified_username = st.text_input("Update Target Username", value=st.session_state.username, key="set_user_input")
    with col_settings_p:
        modified_password = st.text_input("Update Access Token Secret", value=st.session_state.password, type="password", key="set_pass_input")
    
    col_settings_act1, col_settings_act2 = st.columns([1, 4])
    with col_settings_act1:
        if st.button("Save Changes", key="set_save_trigger"):
            st.session_state.username = modified_username
            st.session_state.password = modified_password
            st.session_state.show_settings = False
            st.success("Credentials updated successfully.")
            st.rerun()
    with col_settings_act2:
        if st.button("Cancel Modification", key="set_cancel_trigger"):
            st.session_state.show_settings = False
            st.rerun()
    st.stop()

# ==================== 主系统核心业务区分发控制层 ====================
col_view_lbl, col_view_selector = st.columns([5, 5])
with col_view_selector:
    st.session_state.selected_model = st.selectbox(
        "Hardware Model Compute Infrastructure Driver",
        list(MODELS.keys()),
        format_func=lambda x: f"{MODELS[x]['name']} - {MODELS[x]['description']}",
        index=list(MODELS.keys()).index(st.session_state.selected_model),
        key="main_compute_selector"
    )

# 主运行区切分为双工作面板
tab_workbench, tab_framework = st.tabs(["Code Hub Work Bench", "Cross-Language Framework Architect"])

# ==================== 标签页 1: Code Hub 工作台业务流 ====================
with tab_workbench:
    display_container_workbench = st.container()
    with display_container_workbench:
        for msg in st.session_state.messages:
            if msg.get("section") == "workbench":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                if msg["role"] == "assistant" and "analysis" in msg:
                    an_payload = msg["analysis"]
                    st.markdown(
                        f"<div class='analysis-card highlight'><strong>Code Structure Insights Report:</strong><br>"
                        f"Lines total: {an_payload['stats']['total_lines']} | "
                        f"Effective source count: {an_payload['stats']['effective_lines']} | "
                        f"Empty slots: {an_payload['stats']['empty_lines']}</div>", 
                        unsafe_allow_html=True
                    )

    # ChatGPT 样式底部锚定输入域
    user_query_workbench = st.chat_input("Paste disordered source artifacts or assign modification tasks here...", key="terminal_input_workbench")
    if user_query_workbench:
        st.session_state.messages.append({"role": "user", "content": user_query_workbench, "section": "workbench"})
        st.rerun()

    # 异步触发逻辑回调机制
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("section") == "workbench":
        with display_container_workbench:
            with st.chat_message("user"):
                st.markdown(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                with st.spinner("Processing architectural refactoring logic..."):
                    runtime_system_prompt = {
                        "role": "system", 
                        "content": "You are Code Hub Workbench expert. Refactor provided structures and print optimized blocks clearly."
                    }
                    active_conversation_flow = [m for m in st.session_state.messages if m.get("section") == "workbench"]
                    formatted_api_payload = [{"role": m["role"], "content": m["content"]} for m in active_conversation_flow]
                    
                    ai_feedback_content = get_ai_response([runtime_system_prompt] + formatted_api_payload, st.session_state.selected_model)
                    st.markdown(ai_feedback_content)
                    
                    computed_analysis_metrics = analyze_code_structure(ai_feedback_content)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": ai_feedback_content, 
                        "section": "workbench", 
                        "analysis": computed_analysis_metrics
                    })
                    
                    # 历史会话快照同步归档
                    if st.session_state.current_conversation is None:
                        current_time_stamp = datetime.now().strftime('%H:%M')
                        st.session_state.conversations.insert(0, {
                            'title': f"Code Optimization {current_time_stamp}", 
                            'messages': st.session_state.messages.copy()
                        })
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else:
                        st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()

# ==================== 标签页 2: 跨语言架构设计器业务流 ====================
with tab_framework:
    display_container_architect = st.container()
    with display_container_architect:
        for msg in st.session_state.messages:
            if msg.get("section") == "architect":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # ChatGPT 样式底部锚定输入域
    user_query_architect = st.chat_input("Describe your custom high-concurrency cross-platform blueprint systems requirements...", key="terminal_input_architect")
    if user_query_architect:
        st.session_state.messages.append({"role": "user", "content": user_query_architect, "section": "architect"})
        st.rerun()

    # 异步触发逻辑回调机制
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("section") == "architect":
        with display_container_architect:
            with st.chat_message("user"):
                st.markdown(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                with st.spinner("Compiling cross-language full-stack component blueprint trees..."):
                    runtime_system_prompt = {
                        "role": "system", 
                        "content": "You are Code Hub Full-Stack Framework Architect. Design comprehensive file systems trees and mark code blocks cleanly."
                    }
                    active_conversation_flow = [m for m in st.session_state.messages if m.get("section") == "architect"]
                    formatted_api_payload = [{"role": m["role"], "content": m["content"]} for m in active_conversation_flow]
                    
                    ai_feedback_content = get_ai_response([runtime_system_prompt] + formatted_api_payload, st.session_state.selected_model)
                    st.markdown(ai_feedback_content)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": ai_feedback_content, 
                        "section": "architect"
                    })
                    
                    # 历史会话快照同步归档
                    if st.session_state.current_conversation is None:
                        current_time_stamp = datetime.now().strftime('%H:%M')
                        st.session_state.conversations.insert(0, {
                            'title': f"Architecture Template {current_time_stamp}", 
                            'messages': st.session_state.messages.copy()
                        })
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else:
                        st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()
