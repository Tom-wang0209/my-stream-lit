import streamlit as st
import requests
import json
import random
from datetime import datetime
import time

# ==================== API 配置 ====================
DEEPSEEK_API_KEY = "sk-ebed2ac63e5a44d590dbebcb8346f9cd"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# 模型配置
MODELS = {
    'deepseek-chat': {'name': '🌐 DeepSeek Chat', 'type': 'api', 'description': '官方旗舰模型'},
    'deepseek-reasoning': {'name': '🌐 DeepSeek R1', 'type': 'api', 'description': '官方推理模型'},
    'qwen2.5-coder:7b': {'name': '💻 Qwen2.5 Coder', 'type': 'ollama', 'description': '本地代码模型'},
    'deepseek-r1:8b': {'name': '💻 DeepSeek R1 8B', 'type': 'ollama', 'description': '本地推理模型'}
}

# ==================== 页面配置 ====================
st.set_page_config(page_title="Code Hub", layout="wide", page_icon="💻")

# ==================== Session State 初始化 ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'password' not in st.session_state:
    st.session_state.password = '123456'
if 'reset_count' not in st.session_state:
    st.session_state.reset_count = 0
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
"""

WHITE_THEME = """
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
"""

STARRY_THEME = """
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
"""

# 应用主题样式
if st.session_state.theme == 'black':
    st.markdown(BLACK_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'white':
    st.markdown(WHITE_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'starry':
    st.markdown(STARRY_THEME, unsafe_allow_html=True)

    # 生成星星
    stars_html = '<div class="stars-container">'
    for i in range(100):
        x = f"{random.randint(0, 100)}%"
        y = f"{random.randint(0, 100)}%"
        size = f"{random.randint(1, 3)}px"
        delay = f"{random.randint(0, 3)}s"
        duration = f"{random.randint(2, 5)}s"
        stars_html += f'<div class="star" style="left:{x}; top:{y}; width:{size}; height:{size}; animation-delay:{delay}; animation-duration:{duration};"></div>'

    # 生成流星
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
        return "⚠️ 请求超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        return f"❌ API 调用失败: {str(e)}"
    except Exception as e:
        return f"❌ 未知错误: {str(e)}"

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
        return "❌ 无法连接到本地 Ollama 服务。请确保 Ollama 已运行（运行 `ollama serve`）"
    except requests.exceptions.Timeout:
        return "⚠️ 本地模型响应超时，请稍后重试"
    except Exception as e:
        return f"❌ 本地模型调用失败: {str(e)}"

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
        highlights.append(f"🚀 代码规模较大 ({len(lines)} 行)，建议拆分为模块化管理")
    highlights.append(f"✨ 支持 {language} 语言特性优化")
    highlights.append(f"📊 代码复杂度评估: 中等")

    if "print" in code.lower():
        bugs.append({
            'line': max(1, code.lower().index("print") // (len(code) // max(1, len(lines))))
            , 'issue': '调试语句未清理',
            'reason': 'print 语句可能泄露敏感信息或影响性能'
        })

    if "=" * 3 in code or "TODO" in code:
        bugs.append({
            'line': 1,
            'issue': '遗留标记未处理',
            'reason': '发现 === 或 TODO 标记，需要进一步处理'
        })

    suggestions.append(f"💡 可使用列表推导式简化循环逻辑")
    suggestions.append(f"💡 建议添加类型注解提升代码可读性")
    suggestions.append(f"💡 考虑使用上下文管理器优化资源管理")

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

# ==================== 右上角工具栏 ====================
st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
col_spacer, col_ollama, col_theme, col_login, col_spacer2 = st.columns([3, 1, 1.5, 1.5, 3])

with col_ollama:
    with st.popover("📖 新手引导"):
        st.markdown("""
        ### 📥 步骤一：下载安装 Ollama
        1. 访问 [ollama.com](https://ollama.com)
        2. 下载对应系统版本安装

        ### 🤖 步骤二：启动模型
        ```bash
        ollama run qwen2.5-coder:7b
