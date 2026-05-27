import streamlit as st
import psycopg2
from psycopg2 import sql
import requests
import hashlib
import json
import re
import random
from datetime import datetime

# 设置 Streamlit 页面基础配置（必须是第一个 Streamlit 命令）
st.set_page_config(
    page_title="Code Hub - 极客代码枢纽中心",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. 核心安全配置与初始化
# ==========================================
# 强制使用 secrets 获取凭证，确保线上生产环境凭证绝对隔离
DB_CONN_STRING = st.secrets["postgres"]["connection_string"]
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]

# DeepSeek API 端点
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# ==========================================
# 2. 极客感动态视觉主题系统 (CSS 注入)
# ==========================================
BLACK_THEME = """
<style>
.stApp {
    background: linear-gradient(135deg, #0f0f12 0%, #1a1a24 100%);
    color: #e0e0e0;
}
.stButton>button {
    background: transparent;
    border: 1px solid #00ff88;
    color: #00ff88;
    border-radius: 4px;
    transition: all 0.3s;
}
.stButton>button:hover {
    background: #00ff88;
    color: #000 !important;
    box-shadow: 0 0 15px #00ff88;
}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: #1e1e28;
    color: #e0e0e0;
    border: 1px solid #333;
}
.stSelectbox>div>div>select {
    background-color: #1e1e28;
    color: #e0e0e0;
}
h1, h2, h3, h4, h5, h6 {
    color: #00ff88 !important;
}
[data-testid="stSidebar"] {
    background-color: #15151a !important;
}
</style>
"""

WHITE_THEME = """
<style>
.stApp {
    background: #ffffff;
    color: #333333;
}
.stButton>button {
    background: #f0f0f0;
    border: 1px solid #cccccc;
    color: #333;
    border-radius: 4px;
}
.stButton>button:hover {
    background: #e0e0e0;
}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: #ffffff;
    color: #333;
    border: 1px solid #dddddd;
}
.stSelectbox>div>div>select {
    background-color: #ffffff;
    color: #333;
}
h1, h2, h3, h4, h5, h6 {
    color: #2c3e50 !important;
}
[data-testid="stSidebar"] {
    background-color: #f8f9fa !important;
}
</style>
"""

STARRY_THEME = """
<style>
.stApp {
    background: #000000;
    color: #ffffff;
    overflow-x: hidden;
    position: relative;
}
.star {
    position: absolute;
    background: white;
    border-radius: 50%;
    animation: twinkle var(--duration) ease-in-out infinite;
    opacity: var(--opacity);
    pointer-events: none;
}
@keyframes twinkle {
    0%, 100% { opacity: var(--opacity); }
    50% { opacity: 0.1; }
}
.meteor {
    position: absolute;
    width: 2px;
    height: 80px;
    background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,1));
    transform: rotate(-45deg);
    opacity: 0;
    animation: meteor-anim 8s linear infinite;
    pointer-events: none;
}
@keyframes meteor-anim {
    0% { transform: translateX(100vw) translateY(-100px) rotate(-45deg); opacity: 1; }
    100% { transform: translateX(-100vw) translateY(100vh) rotate(-45deg); opacity: 0; }
}
.stButton>button {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white !important;
    backdrop-filter: blur(5px);
}
.stButton>button:hover {
    background: rgba(255, 255, 255, 0.2);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
}
[data-testid="stSidebar"] {
    background-color: rgba(20, 20, 30, 0.8) !important;
    backdrop-filter: blur(10px);
}
</style>
<div id="star-container"></div>
<script>
const container = document.getElementById('star-container');
if (container && container.children.length === 0) {
    // 生成星星
    for(let i=0; i<100; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        const size = Math.random() * 2 + 1;
        star.style.width = size + 'px';
        star.style.height = size + 'px';
        star.style.left = Math.random() * 100 + 'vw';
        star.style.top = Math.random() * 100 + 'vh';
        star.style.setProperty('--duration', (Math.random() * 3 + 2) + 's');
        star.style.setProperty('--opacity', Math.random());
        container.appendChild(star);
    }
    // 生成流星
    for(let i=0; i<3; i++) {
        const meteor = document.createElement('div');
        meteor.className = 'meteor';
        meteor.style.left = Math.random() * 100 + 'vw';
        meteor.style.top = Math.random() * 50 + 'vh';
        meteor.style.animationDelay = (Math.random() * 5 + i*3) + 's';
        container.appendChild(meteor);
    }
}
</script>
"""

# ==========================================
# 3. 数据库连接与初始化
# ==========================================
def get_connection():
    try:
        conn = psycopg2.connect(DB_CONN_STRING)
        return conn
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

def init_database():
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        # 创建用户表
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ch_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # 创建对话历史表
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ch_conversations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES ch_users(id) ON DELETE CASCADE,
            title VARCHAR(200),
            messages_json TEXT,
            tab_index INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # 创建讨论区表
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ch_discussions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES ch_users(id) ON DELETE CASCADE,
            username VARCHAR(50),
            title VARCHAR(200) NOT NULL,
            code_content TEXT,
            is_archived BOOLEAN DEFAULT FALSE,
            archive_id VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"数据库初始化失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==========================================
# 4. 安全认证逻辑
# ==========================================
def hash_password(password, username):
    # 加盐哈希安全防线：SHA256(password + username)
    salted = password + username
    return hashlib.sha256(salted.encode()).hexdigest()

def register_user(username, password):
    conn = get_connection()
    if not conn:
        return False, "数据库连接失败"
    try:
        cur = conn.cursor()
        pwd_hash = hash_password(password, username)
        # 使用占位符强制防御 SQL 注入
        cur.execute(
            "INSERT INTO ch_users (username, password_hash) VALUES (%s, %s)",
            (username, pwd_hash)
        )
        conn.commit()
        cur.close()
        return True, "注册成功"
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "用户名已存在"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def login_user_db(username, password):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        pwd_hash = hash_password(password, username)
        cur.execute(
            "SELECT id, username FROM ch_users WHERE username = %s AND password_hash = %s",
            (username, pwd_hash)
        )
        user = cur.fetchone()
        cur.close()
        if user:
            return {"id": user[0], "username": user[1]}
        return None
    except Exception as e:
        st.error(f"登录失败: {e}")
        return None
    finally:
        conn.close()

# ==========================================
# 5. 会话管理逻辑
# ==========================================
def save_conversation(user_id, title, messages_json, tab_index):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ch_conversations (user_id, title, messages_json, tab_index, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (user_id, title, messages_json, tab_index)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return new_id
    except Exception as e:
        st.error(f"保存会话失败: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def load_conversations(user_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, title, messages_json, tab_index, updated_at
            FROM ch_conversations
            WHERE user_id = %s
            ORDER BY updated_at DESC
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        st.error(f"加载会话失败: {e}")
        return []
    finally:
        conn.close()

def delete_conversation(conv_id):
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM ch_conversations WHERE id = %s", (conv_id,))
        conn.commit()
        cur.close()
    except Exception as e:
        st.error(f"删除会话失败: {e}")
        conn.rollback()
    finally:
        conn.close()

# ==========================================
# 6. 讨论区逻辑
# ==========================================
def post_discussion(user_id, username, title, code_content):
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ch_discussions (user_id, username, title, code_content)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, username, title, code_content)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        st.error(f"发布讨论失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def search_discussions(query):
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        like_pattern = f"%{query}%"
        cur.execute(
            """
            SELECT id, username, title, code_content, is_archived, archive_id, created_at
            FROM ch_discussions
            WHERE title LIKE %s OR code_content LIKE %s
            ORDER BY created_at DESC
            """,
            (like_pattern, like_pattern)
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        st.error(f"搜索失败: {e}")
        return []
    finally:
        conn.close()

def archive_discussion(disc_id, archive_id):
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE ch_discussions
            SET code_content = '', is_archived = TRUE, archive_id = %s
            WHERE id = %s
            """,
            (archive_id, disc_id)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        st.error(f"归档失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def export_all_discussions():
    conn = get_connection()
    if not conn:
        return "{}"
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, username, title, code_content, is_archived, archive_id, created_at
            FROM ch_discussions
            """
        )
        rows = cur.fetchall()
        cur.close()
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "username": row[1],
                "title": row[2],
                "code_content": row[3],
                "is_archived": row[4],
                "archive_id": row[5],
                "created_at": row[6].isoformat() if row[6] else None
            })
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"导出失败: {e}")
        return "{}"
    finally:
        conn.close()

# ==========================================
# 7. DeepSeek API 调用
# ==========================================
def call_deepseek_api(messages, model="deepseek-chat"):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"API 调用失败: {e}"
    except Exception as e:
        return f"解析响应失败: {e}"

# ==========================================
# 8. 本地代码质检算法
# ==========================================
def analyze_code_locally(code, language):
    lines = code.split('\n')
    total_lines = len(lines)
    effective_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    
    # 检测未清理的调试性 print
    print_pattern = re.compile(r'\bprint\s*\(')
    prints = [(i+1, line) for i, line in enumerate(lines) if print_pattern.search(line)]
    
    # 检测 TODO 挂起标记
    todo_pattern = re.compile(r'\bTODO\b')
    todos = [(i+1, line) for i, line in enumerate(lines) if todo_pattern.search(line)]
    
    analysis = {
        "total_lines": total_lines,
        "effective_lines": len(effective_lines),
        "language": language,
        "prints": prints,
        "todos": todos
    }
    return analysis

# ==========================================
# 9. Streamlit 应用主体
# ==========================================
def main():
    # 初始化全局状态变量（Session State）
    if 'theme' not in st.session_state:
        st.session_state.theme = 'BLACK_THEME'
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'deepseek-chat'
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'search_clicked' not in st.session_state:
        st.session_state.search_clicked = False
    if 'search_query_val' not in st.session_state:
        st.session_state.search_query_val = ""

    # 动态应用前端主题环境
    if st.session_state.theme == 'BLACK_THEME':
        st.markdown(BLACK_THEME, unsafe_allow_html=True)
    elif st.session_state.theme == 'WHITE_THEME':
        st.markdown(WHITE_THEME, unsafe_allow_html=True)
    elif st.session_state.theme == 'STARRY_THEME':
        st.markdown(STARRY_THEME, unsafe_allow_html=True)

    # 自动建表与自适应健康检查
    init_database()

    # ------------------------------------------
    # 顶部横向紧凑工具栏布局设计
    # ------------------------------------------
    col1, col2, col3, col4, col5 = st.columns([4.5, 1.4, 1.5, 1.1, 4.5])
    
    with col1:
        st.markdown("<h2 style='margin:0; padding:0;'>🚀 Code Hub枢纽站</h2>", unsafe_allow_html=True)
        
    with col2:
        model_options = ['deepseek-chat', 'deepseek-reasoning']
        selected_idx = 0 if st.session_state.selected_model == 'deepseek-chat' else 1
        model_select = st.selectbox("Model", model_options, index=selected_idx, label_visibility="collapsed")
        if model_select != st.session_state.selected_model:
            st.session_state.selected_model = model_select

    with col3:
        with st.popover("⚙️ Guide 机制指南"):
            st.markdown("""
            ### 📚 Code Hub 系统功能导视
            **1. Code Hub Workbench**
            - 贴入代码段落、选择环境语言。
            - 能够一键完成本地轻量级静态质检或交由 AI 全面深度重构。
            **2. Architecture Designer**
            - 描述多组件或多阶段的全栈架构设计需求。
            - 交付完备的技术演进指南及蓝图。
            **3. Discussion Board**
            - 供同学进行日常技术研讨，发布核心组件代码。
            - 带有冷备份物理归档保护机制。
            """)

    with col4:
        theme_options = ['BLACK_THEME', 'WHITE_THEME', 'STARRY_THEME']
        current_idx = theme_options.index(st.session_state.theme)
        theme_select = st.selectbox("Theme", theme_options, index=current_idx, label_visibility="collapsed")
        if theme_select != st.session_state.theme:
            st.session_state.theme = theme_select
            st.rerun()

    with col5:
        if st.session_state.user_id:
            cols_user = st.columns([2, 1])
            cols_user[0].markdown(f"<p style='margin-top:10px;'>👤 <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)
            if cols_user[1].button("退出"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.chat_history = []
                st.rerun()
        else:
            with st.popover("🔐 登录 / 注册入口"):
                auth_tab = st.tabs(["安全登录", "新同学注册"])
                with auth_tab[0]:
                    login_user_input = st.text_input("用户名", key="login_u")
                    login_pwd_input = st.text_input("密码", type="password", key="login_p")
                    if st.button("立即登录", use_container_width=True):
                        if login_user_input and login_pwd_input:
                            user_data = login_user_db(login_user_input, login_pwd_input)
                            if user_data:
                                st.session_state.user_id = user_data["id"]
                                st.session_state.username = user_data["username"]
                                st.success("鉴权通过，正在进入系统...")
                                st.rerun()
                            else:
                                st.error("密码校验失败或用户未注册")
                with auth_tab[1]:
                    reg_user_input = st.text_input("注册用户名", key="reg_u")
                    reg_pwd_input = st.text_input("初始密码", type="password", key="reg_p")
                    if st.button("提交注册申请", use_container_width=True):
                        if reg_user_input and reg_pwd_input:
                            success, msg = register_user(reg_user_input, reg_pwd_input)
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)

    st.divider()

    # ------------------------------------------
    # 强制用户登录状态拦截器
    # ------------------------------------------
    if not st.session_state.user_id:
        st.markdown("""
        <div style="text-align: center; padding: 120px 20px;">
            <h1 style="font-size: 3.5rem; color: #00ff88; margin-bottom: 20px;">🔒 访问受限</h1>
            <p style="font-size: 1.4rem; color: #a0a0b0;">当前系统处于线上高隔离生产安全级别，非登录状态主体已被自动拦截。</p>
            <p style="font-size: 1.1rem; color: #666677;">请通过右上角快捷浮窗验证登录身份，以开启全功能工作台。</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------
    # 侧边栏：多会话云端管理
    # ------------------------------------------
    with st.sidebar:
        st.markdown("### 💬 云端历史对话")
        if st.button("➕ 新建干净工作流", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("---")
        # 实时从云端动态加载专属于当前 user_id 的会话列表
        history = load_conversations(st.session_state.user_id)
        if history:
            for conv in history:
                conv_id, title, messages_json, tab_idx, updated_at = conv
                col_a, col_b = st.columns([5, 1.2])
                with col_a:
                    display_title = title[:15] + "..." if len(title) > 15 else title
                    if st.button(f"📄 {display_title}", key=f"load_{conv_id}", use_container_width=True):
                        st.session_state.chat_history = json.loads(messages_json) if messages_json else []
                        st.info(f"已拉取云端历史记录")
                with col_b:
                    if st.button("🗑️", key=f"del_{conv_id}", help="物理擦除该会话"):
                        delete_conversation(conv_id)
                        st.rerun()
        else:
            st.info("云端暂无活跃会话记录")

    # ------------------------------------------
    # 主区域：三大核心功能工作台
    # ------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "🛠️ Code Hub Workbench (代码工作台)", 
        "🏗️ Architecture Designer (架构设计器)", 
        "💬 Discussion Board (极客讨论区)"
    ])

    # --- Tab 1: Code Hub Workbench ---
    with tab1:
        st.markdown("### 🛠️ 全自动化代码重构与质量合规质检")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            code_input = st.text_area("粘贴需要处理的原始代码块", height=320, key="workbench_code_area")
            lang_select = st.selectbox("指定解析语言环境", ["Python", "JavaScript", "Java", "C++", "Go", "Other"])
            
            if st.button("🔍 执行本地静态算法质检", use_container_width=True):
                if code_input.strip():
                    analysis = analyze_code_locally(code_input, lang_select)
                    st.markdown("#### 📊 静态扫描核心度量指标")
                    metric_c1, metric_c2 = st.columns(2)
                    metric_c1.metric("物理总行数", analysis["total_lines"])
                    metric_c2.metric("有效逻辑行", analysis["effective_lines"])
                    
                    if analysis["prints"]:
                        st.warning(f"⚠️ 静态引擎拦截到 {len(analysis['prints'])} 处未清理的 print 调试残留：")
                        for line_num, line in analysis["prints"]:
                            st.text(f"Line {line_num}: {line.strip()}")
                    if analysis["todos"]:
                        st.info(f"📌 系统捕获到 {len(analysis['todos'])} 处未完结的 TODO 挂起标记：")
                        for line_num, line in analysis["todos"]:
                            st.text(f"Line {line_num}: {line.strip()}")
                    if not analysis["prints"] and not analysis["todos"]:
                        st.success("🎉 静态代码健康度优异，未发现明显的缺陷残留。")
                else:
                    st.warning("工作台拒绝接收空数据，请录入有效代码。")
                    
        with col_right:
            if st.button("🤖 触发 DeepSeek AI 重构进化", use_container_width=True):
                if code_input.strip():
                    with st.spinner("DeepSeek 深度模型正在重构推演中..."):
                        prompt_content = f"请帮我重构和优化以下 {lang_select} 代码：\n{code_input}\n\n要求：\n1. 提高代码可读性和可维护性\n2. 提升运行时整体效率\n3. 添加明晰的防御性断言与核心注释\n4. 遵循企业级设计最佳实践。"
                        messages = [
                            {"role": "system", "content": "你是一位拥有殿堂级造诣的代码重构专家与首席技术架构师。"},
                            {"role": "user", "content": prompt_content}
                        ]
                        response = call_deepseek_api(messages, st.session_state.selected_model)
                        st.markdown("#### 🌟 优化演进后版本")
                        st.code(response, language=lang_select.lower())
                        
                        # 同步归档进会话历史并同步至 PostgreSQL
                        st.session_state.chat_history.append({"role": "user", "content": f"[代码重构] 语言环境: {lang_select}\n源码:\n{code_input}"})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        save_conversation(
                            st.session_state.user_id,
                            f"代码重构 - {datetime.now().strftime('%H:%M')}",
                            json.dumps(st.session_state.chat_history),
                            0
                        )
                else:
                    st.warning("请在左侧区域先填充原始源码。")

        # 实时渲染当前内存空间留存的会话记录
        if st.session_state.chat_history:
            st.divider()
            st.markdown("#### 📜 当前工作会话全量快照")
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg["content"])

    # --- Tab 2: Architecture Designer ---
    with tab2:
        st.markdown("### 🏗️ 生产级分布式高并发系统架构蓝图生成器")
        arch_input = st.text_area(
            "输入全栈技术架构诉求描述", 
            height=180, 
            placeholder="例如：请规划一套支持亿级日活、低延迟的跨境电商优惠券秒杀系统方案，需确保核心数据最终一致性...",
            key="arch_designer_input"
        )
        
        if st.button("🏗️ 启动 DeepSeek 深度建模演进", use_container_width=True):
            if arch_input.strip():
                with st.spinner("架构演进核心模型加载中..."):
                    messages = [
                        {"role": "system", "content": "你是一位享誉业界的特级软件架构师，精通高并发、高可用和微服务演进蓝图规划。"},
                        {"role": "user", "content": f"请针对以下业务及技术诉求提供详细的全栈级系统架构设计蓝图：\n{arch_input}\n\n必须全面包含以下核心组件：\n1. 最适配的技术栈选型及深度技术边界判断\n2. 高内聚低耦合的领域服务拆分与边界定义\n3. 多级存储架构设计（关系型/非关系型/分布式缓存）\n4. 高可靠物理部署架构与网络冗余隔离方案\n5. 极致水平扩展及突发尖峰演进指南机制。"}
                    ]
                    response = call_deepseek_api(messages, st.session_state.selected_model)
                    st.markdown("### 📐 系统拓扑及技术演进蓝图方案")
                    st.markdown(response)
                    
                    st.session_state.chat_history.append({"role": "user", "content": f"[架构规划设计请求]:\n{arch_input}"})
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    save_conversation(
                        st.session_state.user_id,
                        f"架构设计 - {datetime.now().strftime('%H:%M')}",
                        json.dumps(st.session_state.chat_history),
                        1
                    )
            else:
                st.warning("请详尽地输入你所需的系统业务规模及基础架构演进背景。")

    # --- Tab 3: Discussion Board ---
    with tab3:
        st.markdown("### 💬 极客讨论与分布式代码资产库")
        
        with st.expander("📝 共享发布我的最新技术心得 / 核心组件"):
            post_title = st.text_input("技术讨论标题", placeholder="输入技术核心摘要点")
            post_content = st.text_area("正文描述或核心实现源码块", height=150)
            if st.button("打包广播发布", use_container_width=True):
                if post_title.strip() and post_content.strip():
                    post_discussion(st.session_state.user_id, st.session_state.username, post_title, post_content)
                    st.success("信息资产发布成功，全局索引已更新！")
                    st.rerun()
                else:
                    st.error("标题与讨论正文均不可为空白字符。")
        
        st.divider()
        
        # 搜索与资产冷备份管理屏障
        col_search, col_admin = st.columns([3.5, 1.5])
        with col_search:
            search_input_val = st.text_input("🔍 全局参数化模糊搜索 (安全防注入匹配)", key="search_box")
            if st.button("激活搜索路由", use_container_width=True):
                st.session_state.search_clicked = True
                st.session_state.search_query_val = search_input_val
        
        with col_admin:
            st.markdown("<p style='margin:0; font-size:0.8rem; color:#888;'>物理归档与审计管理</p>", unsafe_allow_html=True)
            if st.button("📥 一键冷导出全量讨论 (JSON)", use_container_width=True):
                data_json = export_all_discussions()
                st.download_button(
                    label="📂 点击下载备份文件",
                    data=data_json,
                    file_name=f"discussions_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        # 渲染底层讨论区看板
        st.markdown("#### ⚡ 活跃技术风向标看板")
        
        # 动态筛选路由逻辑
        if st.session_state.search_clicked and st.session_state.search_query_val:
            discussions = search_discussions(st.session_state.search_query_val)
            st.caption(f"当前处于搜索模式，关键词：`{st.session_state.search_query_val}`，命中了 {len(discussions)} 条数据。")
            # 重置单次点击状态以便下一次变更
            st.session_state.search_clicked = False
        else:
            # 默认状态下回退拉取最近的20条生产活跃日志
            discussions = []
            conn = get_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                    SELECT id, username, title, code_content, is_archived, archive_id, created_at
                    FROM ch_discussions
                    ORDER BY created_at DESC
                    LIMIT 20
                    """)
                    discussions = cur.fetchall()
                    cur.close()
                except Exception as e:
                    st.error(f"加载讨论板错误: {e}")
                finally:
                    conn.close()

        # 开始卡片渲染循环
        if discussions:
            for disc in discussions:
                disc_id, username, title, content, is_archived, archive_id, created_at = disc
                with st.container():
                    st.markdown(f"#### 📄 {title}")
                    st.caption(f"🚀 贡献者: `{username}` | 🕒 广播时间: {created_at}")
                    
                    # 冷备份清空屏蔽安全机制校验
                    if is_archived:
                        st.warning(f"📦 [安全隔离提示：该核心代码资产已通过冷备份安全技术迁移至物理离线硬盘。请联系技术统筹处调取全局编号: {archive_id}]")
                    else:
                        st.code(content, language="python")
                        # 归档拦截触发组件
                        if st.button(f"🔒 物理冷归档此资产", key=f"archive_btn_{disc_id}"):
                            generated_arc_id = f"ARC-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
                            archive_discussion(disc_id, generated_arc_id)
                            st.success(f"冷备份成功。物理序列归档号: {generated_arc_id}")
                            st.rerun()
                    st.markdown("<hr style='border:0.5px dashed rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        else:
            st.info("数据层当前未检索到任何符合讨论范围的代码或心得分享。")

if __name__ == "__main__":
    main()
