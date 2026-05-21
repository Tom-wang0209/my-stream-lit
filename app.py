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
    'deepseek-chat': {'name': '🌐 DeepSeek Chat', 'type': 'api'},
    'deepseek-reasoning': {'name': '🌐 DeepSeek R1', 'type': 'api'},
    'qwen2.5-coder:7b': {'name': '💻 Qwen2.5 Coder', 'type': 'ollama'},
    'deepseek-r1:8b': {'name': '💻 DeepSeek R1 8B', 'type': 'ollama'}
}

# ==================== 页面配置 ====================
st.set_page_config(page_title="Code Hub", layout="wide", page_icon="💻")

# ==================== Session State 初始化 ====================
for key in ['logged_in', 'password', 'reset_count', 'conversations',
            'current_conversation', 'selected_model', 'messages',
            'theme', 'chat_tab', 'new_chat']:
    if key not in st.session_state:
        if key == 'logged_in':
            st.session_state[key] = False
        elif key == 'password':
            st.session_state[key] = '123456'
        elif key in ['reset_count', 'chat_tab', 'new_chat']:
            st.session_state[key] = 0
        elif key in ['conversations', 'messages']:
            st.session_state[key] = []
        elif key == 'current_conversation':
            st.session_state[key] = None
        elif key == 'selected_model':
            st.session_state[key] = 'deepseek-chat'
        elif key == 'theme':
            st.session_state[key] = 'black'

# ==================== 主题样式 ====================
THEME_STYLES = {
    'black': '''
    .stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%); }
    .main-bg { background-color: #0d1117 !important; }
    .chat-bubble { background-color: #21262d; color: #c9d1d9; }
    .sidebar-bg { background-color: #161b22 !important; }
    .text-primary { color: #58a6ff; }
    .text-secondary { color: #8b949e; }
    ''',
    'white': '''
    .stApp { background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 50%, #f6f8fa 100%); }
    .main-bg { background-color: #ffffff !important; }
    .chat-bubble { background-color: #f6f8fa; color: #24292f; }
    .sidebar-bg { background-color: #f6f8fa !important; }
    .text-primary { color: #0969da; }
    .text-secondary { color: #656d76; }
    ''',
    'starry': '''
    .stApp {
        background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
        overflow-x: hidden;
    }
    .stars, .stars2, .stars3 {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none;
    }
    .stars {
        background: transparent;
        animation: animStar 50s linear infinite;
    }
    .stars2 {
        background: transparent;
        animation: animStar 100s linear infinite;
    }
    .stars3 {
        background: transparent;
        animation: animStar 150s linear infinite;
    }
    @keyframes animStar {
        from { transform: translateY(0px); }
        to { transform: translateY(-2000px); }
    }
    .star {
        position: absolute;
        background: white;
        border-radius: 50%;
        animation: twinkle 2s infinite ease-in-out;
    }
    @keyframes twinkle {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }
    .main-bg { background-color: transparent !important; }
    .chat-bubble { background-color: rgba(33, 38, 45, 0.9); color: #c9d1d9; backdrop-filter: blur(10px); }
    .sidebar-bg { background-color: rgba(22, 27, 34, 0.95) !important; backdrop-filter: blur(10px); }
    .text-primary { color: #58a6ff; }
    .text-secondary { color: #8b949e; }
    '''
}

# 应用主题
st.markdown(f"""
<style>
{THEME_STYLES[st.session_state.theme]}
.sidebar-bg [data-testid="stSidebar"] {{ background-color: transparent !important; }}
[data-testid="stHeader"] {{ background: transparent; padding: 0.5rem 1rem; }}
.toolbar-container {{ display: flex; gap: 0.5rem; align-items: center; }}
.toolbar-btn {{ padding: 0.4rem 0.8rem; border-radius: 6px; border: none; cursor: pointer; font-size: 0.9rem; }}
.history-card {{ padding: 0.8rem; margin: 0.5rem 0; border-radius: 8px; cursor: pointer; transition: all 0.2s; }}
.history-card:hover {{ transform: translateX(5px); }}
.code-block {{ background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; overflow-x: auto; }}
.analysis-card {{ padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid; }}
.highlight {{ border-color: #238636; }}
.bug {{ border-color: #da3633; }}
.suggestion {{ border-color: #a371f7; }}
.chat-container {{ height: calc(100vh - 200px); overflow-y: auto; }}
</style>
""", unsafe_allow_html=True)

# 星空背景星星生成
if st.session_state.theme == 'starry':
    stars_html = '<div class="stars">'
    for i in range(100):
        x, y = f"{random.randint(0, 100)}%", f"{random.randint(0, 100)}%"
        size = f"{random.randint(1, 3)}px"
        delay = f"{random.randint(0, 2)}s"
        stars_html += f'<div class="star" style="left:{x}; top:{y}; width:{size}; height:{size}; animation-delay:{delay};"></div>'
    stars_html += '</div>'
    st.markdown(stars_html, unsafe_allow_html=True)

# ==================== API 函数 ====================
def call_deepseek_api(messages, model='deepseek-chat', temperature=0.7):
    try:
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {DEEPSEEK_API_KEY}'}
        payload = {'model': model, 'messages': messages, 'temperature': temperature, 'max_tokens': 4000}
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ API调用失败: {str(e)}"

def call_ollama_api(prompt, model='qwen2.5-coder:7b'):
    try:
        response = requests.post(OLLAMA_API_URL, json={'model': model, 'prompt': prompt, 'stream': False}, timeout=120)
        response.raise_for_status()
        return response.json().get('response', '未获得响应')
    except Exception as e:
        return f"❌ 本地模型调用失败: {str(e)}"

def get_ai_response(messages, model):
    if MODELS[model]['type'] == 'api':
        return call_deepseek_api(messages, model)
    else:
        prompt = '\n'.join([f"{m['role']}: {m['content']}" for m in messages])
        return call_ollama_api(prompt, model)

def analyze_code(code, language):
    prompt = f'''分析以下{language}代码，输出JSON：{{"highlights":[], "bugs":[{{"line":1,"issue":"","reason":""}}],
"suggestions": [], "stats":{{"total_lines":0,"effective_lines":0,"empty_lines":0}}}}

代码：{code}'''
    try:
        result = call_ollama_api(prompt, 'qwen2.5-coder:7b')
        import re
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            return json.loads(match.group())
        lines = code.split('\n')
        return {
            'highlights': [f"✨ {language}特性优化"],
            'bugs': [],
            'suggestions': ['💡 添加类型注解'],
            'stats': {'total_lines': len(lines), 'effective_lines': len([l for l in lines if l.strip()]), 'empty_lines': 0}
        }
    except:
        return {'highlights': [], 'bugs': [], 'suggestions': [], 'stats': {'total_lines': 0, 'effective_lines': 0, 'empty_lines': 0}}

# ==================== 右上角工具栏 ====================
col1, col2, col3, col4 = st.columns([6, 1, 2, 2])

with col2:
    if st.button("📖", help="Ollama 新手引导", key="ollama_help"):
        with st.popover("📖 Ollama 新手引导"):
            st.markdown("""
            ### 下载安装
            1. 访问 [ollama.com](https://ollama.com)
            2. 下载对应系统安装包

            ### 启动模型
            ```bash
            ollama run qwen2.5-coder:7b
            ollama run deepseek-r1:8b
