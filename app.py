import streamlit as st
import time
from datetime import datetime
import requests
import json
import subprocess
import sys

# ==================== API 配置 ====================
DEEPSEEK_API_KEY = "sk-2e47bcfcac594ab58a3da77600210914"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# 模型配置
MODELS = {
    'deepseek-chat': {
        'name': '🌐 DeepSeek Chat V4',
        'type': 'api',
        'description': '官方旗舰模型，日常对话、代码修改与深度剖析'
    },
    'deepseek-reasoning': {
        'name': '🌐 DeepSeek Reasoning R1',
        'type': 'api',
        'description': '官方推理模型，深度重构与架构设计'
    },
    'qwen2.5-coder:7b': {
        'name': '💻 Qwen2.5 Coder 7B',
        'type': 'ollama',
        'description': '本地 Ollama 运行，零成本代码模型'
    },
    'deepseek-r1:8b': {
        'name': '💻 DeepSeek R1 8B',
        'type': 'ollama',
        'description': '本地 Ollama 运行，零成本推理模型'
    }
}

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="代码重构助手 - DeepSeek 驱动",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 自定义CSS - 极客暗黑风 ====================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
}
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select,
.stNumberInput>div>div>input {
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
    transition: all 0.3s;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
}
.stButton>button:disabled {
    background: #30363d !important;
    color: #8b949e !important;
    cursor: not-allowed;
}
.sidebar-title {
    color: #58a6ff;
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 1rem;
}
.code-highlight {
    background: #161b22;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #30363d;
}
.analysis-card {
    background: #21262d;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
}
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
.architecture-tree {
    background: #0d1117;
    padding: 1rem;
    border-radius: 8px;
    font-family: 'Courier New', monospace;
    border: 1px solid #30363d;
}
.guide-step {
    background: #161b22;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    border-left: 4px solid #58a6ff;
}
.tab-content {
    background: #161b22;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #30363d;
    margin-top: 1rem;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 2rem;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 50px;
    padding: 0 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==================== Session State 初始化 ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'password' not in st.session_state:
    st.session_state.password = '123456'
if 'reset_count' not in st.session_state:
    st.session_state.reset_count = 0
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = None
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'Python'
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'deepseek-chat'
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# ==================== API 调用函数 ====================
def call_deepseek_api(messages, model='deepseek-chat', temperature=0.7):
    """调用 DeepSeek API"""
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
    """调用本地 Ollama API"""
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

def generate_refactored_code(code, language, model):
    """生成重构后的代码"""
    model_info = MODELS.get(model, MODELS['deepseek-chat'])
    
    if model_info['type'] == 'api':
        messages = [
            {
                'role': 'system',
                'content': f'''你是一个专业的{language}代码重构专家。请对用户输入的代码进行深度优化重构。

要求：
1. 保持代码功能完全一致
2. 优化代码结构、命名和注释
3. 提升代码可读性和可维护性
4. 修复潜在的 bug
5. 只输出重构后的完整代码，不要任何解释说明
6. 代码格式要规范，符合{language}最佳实践'''
            },
            {
                'role': 'user',
                'content': f'请重构以下{language}代码：\n\n{code}'
            }
        ]
        return call_deepseek_api(messages, model)
    else:
        prompt = f'''你是一个专业的{language}代码重构专家。请对以下代码进行深度优化重构。

要求：
1. 保持代码功能完全一致
2. 优化代码结构、命名和注释
3. 提升代码可读性和可维护性
4. 修复潜在的 bug
5. 只输出重构后的完整代码，不要任何解释说明

代码：
{code}'''
        return call_ollama_api(prompt, model)

def analyze_code(code, language, model):
    """深度剖析代码"""
    model_info = MODELS.get(model, MODELS['deepseek-chat'])
    
    prompt = f'''请对以下{language}代码进行深度剖析，输出 JSON 格式结果，包含：

1. highlights: 代码亮点（性能优势、语法糖等）
2. bugs: Bug定位（行号、问题、根因）
3. suggestions: 简化建议
4. stats: 统计信息（总行数、有效行数、空行数）

代码：
{code}

输出严格的 JSON 格式，不要其他文字：'''

    if model_info['type'] == 'api':
        messages = [
            {'role': 'system', 'content': '你是一个代码分析专家，只输出严格的 JSON 格式结果。'},
            {'role': 'user', 'content': prompt}
        ]
        result = call_deepseek_api(messages, model, temperature=0.3)
    else:
        result = call_ollama_api(prompt, model)
    
    try:
        # 提取 JSON 部分
        if '```json' in result:
            json_str = result.split('```json')[1].split('```')[0].strip()
        elif '```' in result:
            json_str = result.split('```')[1].split('```')[0].strip()
        else:
            json_str = result
        return json.loads(json_str)
    except:
        # 解析失败返回默认结构
        lines = code.split('\n')
        return {
            'highlights': [f"✨ 支持 {language} 语言特性优化"],
            'bugs': [],
            'suggestions': ['💡 建议添加类型注解', '💡 考虑使用上下文管理器'],
            'stats': {
                'total_lines': len(lines),
                'effective_lines': len([l for l in lines if l.strip()]),
                'empty_lines': len(lines) - len([l for l in lines if l.strip()])
            }
        }

def generate_architecture(requirement, model='deepseek-reasoning'):
    """生成交叉语言全栈架构设计"""
    model_info = MODELS.get(model, MODELS['deepseek-reasoning'])
    
    prompt = f'''你是一个全栈架构设计专家。请根据以下需求，设计一套完整的跨语言全栈架构方案。

需求：{requirement}

输出要求：
1. 项目目录树（使用 tree 格式）
2. 各语言模块说明（Python/JavaScript/C++ 等）
3. 模块间通信方式
4. 技术栈推荐
5. 部署建议

请使用 Markdown 格式输出，代码块标注具体语言：'''

    if model_info['type'] == 'api':
        messages = [
            {
                'role': 'system',
                'content': '你是一个全栈架构设计专家，擅长跨语言技术栈设计。'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
        return call_deepseek_api(messages, model)
    else:
        return call_ollama_api(prompt, model)

# ==================== GitHub 下载链接 ====================
def get_github_url(language):
    urls = {
        'Python': 'https://www.python.org/downloads/',
        'C++': 'https://visualstudio.microsoft.com/visual-cpp-build-tools/',
        'JavaScript': 'https://nodejs.org/',
        'Java': 'https://www.oracle.com/java/technologies/downloads/',
        'Go': 'https://go.dev/dl/',
        'Rust': 'https://www.rust-lang.org/tools/install'
    }
    return urls.get(language, 'https://github.com')

# ==================== 登录页面 ====================
if not st.session_state.logged_in:
    st.markdown('<h1 style="color: #58a6ff; text-align: center;">🔐 代码重构助手</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #8b949e; text-align: center;">DeepSeek 驱动 · 混合算力池 · 本地零成本</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 用户登录")
        username = st.text_input("账号", placeholder="请输入账号")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        login_col, reset_col = st.columns(2)
        
        with login_col:
            if st.button("登录", use_container_width=True):
                if username == "admin" and password == st.session_state.password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                elif username != "admin":
                    st.error("账号不存在！")
                else:
                    st.error("密码错误！")
        
        with reset_col:
            if st.button("忘记密码", use_container_width=True):
                if st.session_state.reset_count == 0:
                    new_password = st.text_input("新密码", type="password", key="new_pwd_first")
                    if st.button("确认重置", key="confirm_first"):
                        if new_password:
                            st.session_state.password = new_password
                            st.session_state.reset_count += 1
                            st.success("密码重置成功！")
                            time.sleep(1)
                            st.rerun()
                else:
                    old_password = st.text_input("旧密码", type="password", key="old_pwd")
                    new_password = st.text_input("新密码", type="password", key="new_pwd_sub")
                    if st.button("确认重置", key="confirm_sub"):
                        if old_password == st.session_state.password and new_password:
                            st.session_state.password = new_password
                            st.session_state.reset_count += 1
                            st.success("密码重置成功！")
                            time.sleep(1)
                            st.rerun()
                        elif old_password != st.session_state.password:
                            st.error("旧密码错误！")
                        else:
                            st.warning("请输入新密码")

# ==================== 主界面 ====================
else:
    # 顶部模型选择栏
    st.markdown('<div style="display: flex; justify-content: space-between; align-items: center;">', unsafe_allow_html=True)
    st.markdown('<h1 style="color: #58a6ff; margin: 0;">🔧 代码重构助手</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        selected_model = st.selectbox(
            "选择模型",
            list(MODELS.keys()),
            format_func=lambda x: MODELS[x]['name'],
            index=list(MODELS.keys()).index(st.session_state.selected_model)
        )
        st.session_state.selected_model = selected_model
        st.markdown(f'<p style="color: #8b949e; font-size: 0.8rem;">{MODELS[selected_model]["description"]}</p>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.markdown('<div class="sidebar-title">📁 历史记录</div>', unsafe_allow_html=True)
        
        if st.button("➕ 新建对话", use_container_width=True):
            st.session_state.current_conversation = None
            st.rerun()
        
        search_query = st.text_input("🔍 搜索历史", placeholder="输入关键词过滤...")
        st.markdown("---")
        
        if st.session_state.conversations:
            filtered = [c for c in st.session_state.conversations if search_query.lower() in c['title'].lower()]
            for idx, conv in enumerate(filtered):
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"💬 {conv['title'][:18]}...", key=f"conv_{idx}", use_container_width=True):
                        st.session_state.current_conversation = conv
                        if 'tab' in conv:
                            st.session_state.active_tab = conv['tab']
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.conversations.remove(conv)
                        st.rerun()
        else:
            st.info("暂无历史记录")
        
        st.markdown("---")
        st.markdown('<div class="sidebar-title">⚙️ 设置</div>', unsafe_allow_html=True)
        
        language = st.selectbox(
            "编程语言",
            ["Python", "C++", "JavaScript", "Java", "Go", "Rust"],
            index=["Python", "C++", "JavaScript", "Java", "Go", "Rust"].index(st.session_state.selected_language)
        )
        st.session_state.selected_language = language
        
        st.markdown("---")
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    # 主标签页
    tab1, tab2, tab3 = st.tabs(["🔧 代码优化修复", "🏗️ 跨语言架构设计", "📖 Ollama 新手指引"])
    
    # ==================== 标签页1: 代码优化修复 ====================
    with tab1:
        st.markdown("### 📝 输入代码")
        code_input = st.text_area(
            "请粘贴需要重构的代码...",
            height=300,
            value=st.session_state.current_conversation.get('input', '')
            if st.session_state.current_conversation and st.session_state.current_conversation.get('type') == 'code'
            else "",
            key="code_area"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚀 优化重构", use_container_width=True, key="refactor_btn"):
                if code_input.strip():
                    with st.spinner(f"正在使用 {MODELS[st.session_state.selected_model]['name']} 分析代码..."):
                        refactored = generate_refactored_code(code_input, st.session_state.selected_language, st.session_state.selected_model)
                        analysis = analyze_code(code_input, st.session_state.selected_language, st.session_state.selected_model)
                        timestamp = datetime.now().strftime('%H:%M')
                        title = f"代码重构 {timestamp}"
                        st.session_state.conversations.insert(0, {
                            'title': title,
                            'type': 'code',
                            'tab': 0,
                            'input': code_input,
                            'output': refactored,
                            'analysis': analysis,
                            'language': st.session_state.selected_language,
                            'model': st.session_state.selected_model,
                            'time': datetime.now()
                        })
                        st.session_state.current_conversation = st.session_state.conversations[0]
                        st.success("重构完成！")
                        st.rerun()
                else:
                    st.warning("请输入代码！")
        
        with col2:
            if st.button("🗑️ 清空", use_container_width=True, key="clear_code_btn"):
                st.session_state.current_conversation = None
                st.rerun()
        
        # 显示结果
        if st.session_state.current_conversation and st.session_state.current_conversation.get('type') == 'code':
            st.markdown("---")
            st.markdown("### ✨ 重构结果")
            refactored = st.session_state.current_conversation['output']
            st.code(refactored, language=st.session_state.selected_language.lower(), line_numbers=True)
            
            st.markdown("---")
            st.markdown("### 🔍 代码深度剖析")
            analysis = st.session_state.current_conversation['analysis']
            
            cols = st.columns(3)
            with cols[0]:
                st.metric("总行数", analysis.get('stats', {}).get('total_lines', 0))
            with cols[1]:
                st.metric("有效行数", analysis.get('stats', {}).get('effective_lines', 0))
            with cols[2]:
                st.metric("空行数", analysis.get('stats', {}).get('empty_lines', 0))
            
            with st.expander("✨ 代码亮点", expanded=True):
                for highlight in analysis.get('highlights', []):
                    st.markdown(f'<div class="analysis-card highlight">{highlight}</div>', unsafe_allow_html=True)
            
            with st.expander("🪲 Bug定位与根因"):
                if analysis.get('bugs'):
                    for bug in analysis['bugs']:
                        st.markdown(f'''
                        <div class="analysis-card bug">
                        <strong>第 {bug.get("line", "?")} 行: {bug.get("issue", "未知问题")}</strong><br>
                        <span style="color: #8b949e;">根因: {bug.get("reason", "未知")}</span>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.info("🎉 未发现明显问题！")
            
            with st.expander("💡 可简化建议"):
                for suggestion in analysis.get('suggestions', []):
                    st.markdown(f'<div class="analysis-card suggestion">{suggestion}</div>', unsafe_allow_html=True)
            
            if analysis.get('stats', {}).get('total_lines', 0) > 30:
                st.markdown("---")
                url = get_github_url(st.session_state.selected_language)
                st.info(f"💾 代码较长，建议在 [{st.session_state.selected_language} 官网]({url}) 下载开发环境")
    
    # ==================== 标签页2: 跨语言架构设计 ====================
    with tab2:
        st.markdown("### 🏗️ 跨语言全栈架构设计器")
        st.markdown('<p style="color: #8b949e;">输入一句话需求，AI 将为您设计完整的跨语言全栈架构方案</p>', unsafe_allow_html=True)
        
        requirement = st.text_area(
            "请描述您的全栈需求...",
            height=100,
            placeholder="例如：我要做一个实时聊天应用，支持消息推送、文件分享、用户认证...",
            value=st.session_state.current_conversation.get('input', '')
            if st.session_state.current_conversation and st.session_state.current_conversation.get('type') == 'arch'
            else "",
            key="arch_input"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 生成架构设计", use_container_width=True, key="gen_arch_btn"):
                if requirement.strip():
                    with st.spinner("正在设计全栈架构..."):
                        architecture = generate_architecture(requirement, st.session_state.selected_model)
                        timestamp = datetime.now().strftime('%H:%M')
                        title = f"架构设计 {timestamp}"
                        st.session_state.conversations.insert(0, {
                            'title': title,
                            'type': 'arch',
                            'tab': 1,
                            'input': requirement,
                            'output': architecture,
                            'model': st.session_state.selected_model,
                            'time': datetime.now()
                        })
                        st.session_state.current_conversation = st.session_state.conversations[0]
                        st.success("架构设计完成！")
                        st.rerun()
                else:
                    st.warning("请输入需求描述！")
        
        with col2:
            if st.button("🗑️ 清空", use_container_width=True, key="clear_arch_btn"):
                st.session_state.current_conversation = None
                st.rerun()
        
        # 显示架构设计结果
        if st.session_state.current_conversation and st.session_state.current_conversation.get('type') == 'arch':
            st.markdown("---")
            st.markdown("### 📐 架构设计方案")
            st.markdown(f'<div class="architecture-tree">{st.session_state.current_conversation["output"]}</div>', unsafe_allow_html=True)
    
    # ==================== 标签页3: Ollama 新手指引 ====================
    with tab3:
        st.markdown("### 📖 本地 Ollama 新手指引")
        st.markdown('<p style="color: #8b949e;">在本地运行零成本 AI 模型，保护隐私，无需联网</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown('''
        <div class="guide-step">
        <h3 style="color: #58a6ff;">📥 步骤一：下载并安装 Ollama</h3>
        <p>1. 访问 Ollama 官网：<a href="https://ollama.com" target="_blank" style="color: #58a6ff;">ollama.com</a></p>
        <p>2. 根据您的操作系统选择对应版本下载：</p>
        <ul>
        <li><strong>Windows</strong>：下载 .exe 安装包，双击运行安装</li>
        <li><strong>macOS</strong>：下载 .dmg 文件，拖拽到 Applications 文件夹</li>
        <li><strong>Linux</strong>：运行官方提供的安装脚本</li>
        </ul>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="guide-step">
        <h3 style="color: #58a6ff;">🤖 步骤二：下载并启动本地模型</h3>
        <p>打开终端（Terminal/CMD），运行以下命令下载模型：</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.code("ollama run qwen2.5-coder:7b", language="bash")
        st.markdown('<p style="color: #8b949e; font-size: 0.9rem;">📝 这将自动下载约 4.7GB 的模型文件，首次运行需要一些时间</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.code("ollama run deepseek-r1:8b", language="bash")
        st.markdown('<p style="color: #8b949e; font-size: 0.9rem;">📝 这将自动下载约 4.9GB 的模型文件</p>', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="guide-step">
        <h3 style="color: #58a6ff;">🔧 步骤三：确保 Ollama 服务运行</h3>
        <p>默认情况下，安装 Ollama 后服务会自动启动。如果需要手动启动：</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.code("ollama serve", language="bash")
        st.markdown('<p style="color: #8b949e; font-size: 0.9rem;">📝 服务默认运行在 http://localhost:11434</p>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('''
        <div class="guide-step">
        <h3 style="color: #58a6ff;">❓ 常见问题</h3>
        <p><strong>Q: 如何检查 Ollama 是否正常运行？</strong></p>
        <p>在浏览器访问：<a href="http://localhost:11434" target="_blank" style="color: #58a6ff;">http://localhost:11434</a></p>
        <p>如果看到 "Ollama is running" 提示，说明服务正常。</p>
        <p><strong>Q: 如何查看已安装的模型？</strong></p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.code("ollama list", language="bash")
        
        st.markdown('''
        <div class="guide-step">
        <p><strong>Q: 模型下载太慢怎么办？</strong></p>
        <p>可以设置镜像源加速下载：</p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.code("set OLLAMA_HOST=mirrors.ollama.com", language="bash")
        st.markdown("---")
        st.info('💡 提示：本地模型虽然响应速度较慢，但完全免费且保护数据隐私，适合代码审查和学习用途！')
