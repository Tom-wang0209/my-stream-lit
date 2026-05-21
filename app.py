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
    'deepseek-chat': {'name': 'DeepSeek Chat', 'type': 'api', 'description': '官方旗舰模型'},
    'deepseek-reasoning': {'name': 'DeepSeek R1', 'type': 'api', 'description': '官方推理模型'},
    'qwen2.5-coder:7b': {'name': 'Qwen2.5 Coder', 'type': 'ollama', 'description': '本地代码模型'},
    'deepseek-r1:8b': {'name': 'DeepSeek R1 8B', 'type': 'ollama', 'description': '本地推理模型'}
}

# ==================== 全局页面配置 ====================
st.set_page_config(page_title="Code Hub", layout="wide")

# ==================== 核心状态机初始化 ====================
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

# ==================== 防截断：动态样式加载引擎 ====================
# 将复杂的 CSS 扁平化整合为单行注入，彻底杜绝多行三引号截断 Bug
theme_bg = "#0d1117" if st.session_state.theme in ['black', 'starry'] else "#f6f8fa"
theme_text = "#c9d1d9" if st.session_state.theme in ['black', 'starry'] else "#24292f"
theme_box = "#21262d" if st.session_state.theme in ['black', 'starry'] else "#ffffff"

st.markdown(f"""<style>
.stApp {{ background: {theme_bg} !important; }}
h1, h2, h3, h4, h5, h6, p, span, div, label {{ color: {theme_text} !important; }}
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {{ background-color: {theme_box} !important; color: {theme_text} !important; }}
.stButton>button {{ background: {theme_box}; color: {theme_text}; border-radius: 6px; }}
.stButton>button:hover {{ border-color: #58a6ff; color: #58a6ff; }}
.stars-container {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }}
.star {{ position: absolute; background: white; border-radius: 50%; animation: twinkle 3s infinite ease-in-out; }}
@keyframes twinkle {{ 0%, 100% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} }}
</style>""", unsafe_allow_html=True)

if st.session_state.theme == 'starry':
    stars_html = '<div class="stars-container">' + ''.join([f'<div class="star" style="left:{random.randint(0,100)}%; top:{random.randint(0,100)}%; width:{random.randint(1,3)}px; height:{random.randint(1,3)}px; animation-duration:{random.randint(2,5)}s;"></div>' for _ in range(30)]) + '</div>'
    st.markdown(stars_html, unsafe_allow_html=True)

# ==================== 算力请求网关 ====================
def get_ai_response(messages, model):
    if MODELS[model]['type'] == 'api':
        try:
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {DEEPSEEK_API_KEY}'}
            payload = {'model': model, 'messages': messages, 'temperature': 0.7}
            return requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60).json()['choices'][0]['message']['content']
        except Exception as e: return f"API Pipeline Error: {str(e)}"
    else:
        try:
            prompt = '\n'.join([f"{m['role']}: {m['content']}" for m in messages])
            return requests.post(OLLAMA_API_URL, json={'model': model, 'prompt': prompt, 'stream': False}, timeout=60).json().get('response', 'Compute Error')
        except Exception as e: return f"Local Runtime Offline: {str(e)}"

# ==================== 右上角高级工具栏 (Deploy 同排下方) ====================
st.markdown('<div style="position: relative; z-index: 999; margin-top: -10px;">', unsafe_allow_html=True)
col_tb_space, col_tb_guide, col_tb_theme, col_tb_auth = st.columns([5, 1.5, 1.5, 1.5])

with col_tb_guide:
    if st.button("Ollama Guide", use_container_width=True):
        st.session_state.show_guide = not st.session_state.show_guide
        st.session_state.show_settings = False
        st.rerun()

with col_tb_theme:
    theme_map = {'black': 'Geek Black', 'white': 'Soft White', 'starry': 'Starry Sky'}
    selected_theme = st.selectbox("Theme", list(theme_map.keys()), format_func=lambda x: theme_map[x], index=list(theme_map.keys()).index(st.session_state.theme), label_visibility="collapsed")
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

with col_tb_auth:
    if st.session_state.logged_in:
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.show_settings = False
            st.rerun()
    else:
        st.markdown("<div style='text-align: center; line-height: 38px; color: #8b949e; border: 1px dashed #30363d; border-radius: 6px; font-size: 0.9rem;'>Locked</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==================== 独立页面路由拦截 ====================
if not st.session_state.logged_in:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    _, login_box, _ = st.columns([1.5, 1, 1.5])
    with login_box:
        st.markdown("<h2 style='text-align: center;'>Code Hub Gateway</h2>", unsafe_allow_html=True)
        in_user = st.text_input("Username", placeholder="Identity identity credential")
        in_pass = st.text_input("Password", type="password", placeholder="Access token secret")
        if st.button("Verify Credentials", use_container_width=True):
            if in_user == st.session_state.username and in_pass == st.session_state.password:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Access rejected")
    st.stop()

if st.session_state.show_guide:
    if st.button("← Return to Workspace Core"):
        st.session_state.show_guide = False
        st.rerun()
    st.markdown("""
    ## Local Architecture Infrastructure Setup Guide
    ---
    1. **Download Local Runtime Core**: Install the client core tool directly from [ollama.com](https://ollama.com).
    2. **Deploy Computational Models**: Open your native terminal and pull down the optimized models layer:
    ```bash
    ollama run qwen2.5-coder:7b
    ```
    3. **Connection Listener**: Ensure background engine mapping adapter is alive at port `http://localhost:11434`.
    """)
    st.stop()

# ==================== 侧边栏及设置 ====================
with st.sidebar:
    st.markdown("## Code Hub Workspace")
    if st.button("New Session Panel", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_conversation = None
        st.rerun()
    st.markdown("---")
    hist_search = st.text_input("Filter History", placeholder="Search...", label_visibility="collapsed")
    for idx, conv in enumerate(st.session_state.conversations):
        if not hist_search or hist_search.lower() in conv['title'].lower():
            c_card, c_del = st.columns([4, 1])
            with c_card:
                if st.button(conv['title'], key=f"hist_{idx}", use_container_width=True):
                    st.session_state.messages = conv['messages'].copy()
                    st.session_state.current_conversation = conv
                    st.rerun()
            with c_del:
                if st.button("Clear", key=f"del_{idx}", use_container_width=True):
                    st.session_state.conversations.pop(idx)
                    st.rerun()
    st.markdown("---")
    if st.button("Security Settings", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

if st.session_state.show_settings:
    st.markdown("### Configuration Management Center")
    m_user = st.text_input("Update Username", value=st.session_state.username)
    m_pass = st.text_input("Update Password", value=st.session_state.password, type="password")
    if st.button("Save Profile Changes"):
        st.session_state.username = m_user
        st.session_state.password = m_pass
        st.session_state.show_settings = False
        st.success("Credentials updated.")
        st.rerun()
    st.stop()

# ==================== 主工作台引擎分发 ====================
_, col_engine = st.columns([5, 5])
with col_engine:
    st.session_state.selected_model = st.selectbox("Compute Engine", list(MODELS.keys()), format_func=lambda x: f"{MODELS[x]['name']} - {MODELS[x]['description']}")

tab_workbench, tab_framework = st.tabs(["Code Hub Work Bench", "Framework Architect"])

# 标签页 1 流控
with tab_workbench:
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg.get("section") == "workbench":
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
    user_query = st.chat_input("Paste disorganized source artifacts here...", key="input_wb")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query, "section": "workbench"})
        st.rerun()
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("section") == "workbench":
        with chat_container:
            with st.chat_message("user"): st.markdown(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                with st.spinner("Refactoring..."):
                    sys_p = {"role": "system", "content": "You are Code Hub Workbench expert. Refactor code and print modified blocks."}
                    flow = [m for m in st.session_state.messages if m.get("section") == "workbench"]
                    res = get_ai_response([sys_p] + [{"role": m["role"], "content": m["content"]} for m in flow], st.session_state.selected_model)
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res, "section": "workbench"})
                    if st.session_state.current_conversation is None:
                        st.session_state.conversations.insert(0, {'title': f"Optimization {datetime.now().strftime('%H:%M')}", 'messages': st.session_state.messages.copy()})
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else: st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()

# 标签页 2 流控
with tab_framework:
    arch_container = st.container()
    with arch_container:
        for msg in st.session_state.messages:
            if msg.get("section") == "architect":
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
    user_arch = st.chat_input("Describe blueprints system requirements...", key="input_arch")
    if user_arch:
        st.session_state.messages.append({"role": "user", "content": user_arch, "section": "architect"})
        st.rerun()
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1].get("section") == "architect":
        with arch_container:
            with st.chat_message("user"): st.markdown(st.session_state.messages[-1]["content"])
            with st.chat_message("assistant"):
                with st.spinner("Architecting..."):
                    sys_p = {"role": "system", "content": "You are Code Hub Architect. Design folder structure trees and mark modules."}
                    flow = [m for m in st.session_state.messages if m.get("section") == "architect"]
                    res = get_ai_response([sys_p] + [{"role": m["role"], "content": m["content"]} for m in flow], st.session_state.selected_model)
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res, "section": "architect"})
                    if st.session_state.current_conversation is None:
                        st.session_state.conversations.insert(0, {'title': f"Architecture {datetime.now().strftime('%H:%M')}", 'messages': st.session_state.messages.copy()})
                        st.session_state.current_conversation = st.session_state.conversations[0]
                    else: st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
                    st.rerun()
