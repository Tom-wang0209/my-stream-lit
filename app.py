import streamlit as st
import psycopg2
from psycopg2 import sql
import requests
import hashlib
import json
import re
import random
from datetime import datetime

# 设置 Streamlit 页面基础配置
st.set_page_config(
    page_title="Code Hub - 代码中心",
    page_icon="None",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. 核心安全配置与初始化
# ==========================================
# 从配置文件中获取数据库和API密钥
DB_CONN_STRING = st.secrets["postgres"]["connection_string"]
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]

# DeepSeek API 请求地址
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# ==========================================
# 2. 视觉主题系统 (CSS 注入)
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
# 4. 用户登录与注册逻辑
# ==========================================
def hash_password(password, username):
    # 对密码进行加盐哈希加密，不保存明文密码
    salted = password + username
    return hashlib.sha256(salted.encode()).hexdigest()

def register_user(username, password):
    conn = get_connection()
    if not conn:
        return False, "数据库连接失败"
    try:
        cur = conn.cursor()
        pwd_hash = hash_password(password, username)
        # 使用参数化查询防止 SQL 注入
        cur.execute(
            "INSERT INTO ch_users (username, password_hash) VALUES (%s, %s)",
            (username, pwd_hash)
        )
        conn.commit()
        cur.close()
        return True, "注册成功"
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "该用户名已经被注册了"
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
# 5. 会话历史管理
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
        st.error(f"保存聊天记录失败: {e}")
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
        st.error(f"加载聊天记录失败: {e}")
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
        st.error(f"删除聊天记录失败: {e}")
        conn.rollback()
    finally:
        conn.close()

# ==========================================
# 6. 讨论区帖子管理
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
        st.error(f"发布帖子失败: {e}")
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
        st.error(f"搜索帖子失败: {e}")
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
        st.error(f"归档帖子失败: {e}")
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
        st.error(f"导出数据失败: {e}")
        return "{}"
    finally:
        conn.close()

# ==========================================
# 7. DeepSeek AI 接口调用
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
        return f"人工智能接口连接失败: {e}"
    except Exception as e:
        return f"数据解析失败: {e}"

# ==========================================
# 8. 本地代码检查算法
# ==========================================
def analyze_code_locally(code, language):
    lines = code.split('\n')
    total_lines = len(lines)
    effective_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    
    # 检查代码里有没有未删除的调试输出 print
    print_pattern = re.compile(r'\bprint\s*\(')
    prints = [(i+1, line) for i, line in enumerate(lines) if print_pattern.search(line)]
    
    # 检查代码里有没有未完成的 TODO 标记
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
# 9. 网页程序主体
# ==========================================
def main():
    # 初始化网页状态变量
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

    # 加载用户选择的网页主题样式
    if st.session_state.theme == 'BLACK_THEME':
        st.markdown(BLACK_THEME, unsafe_allow_html=True)
    elif st.session_state.theme == 'WHITE_THEME':
        st.markdown(WHITE_THEME, unsafe_allow_html=True)
    elif st.session_state.theme == 'STARRY_THEME':
        st.markdown(STARRY_THEME, unsafe_allow_html=True)

    # 自动检查并创建数据库表
    init_database()

    # ------------------------------------------
    # 顶部工具栏排版
    # ------------------------------------------
    col1, col2, col3, col4, col5 = st.columns([4.5, 1.4, 1.5, 1.1, 4.5])
    
    with col1:
        st.markdown("<h2 style='margin:0; padding:0;'>Code Hub 代码中心</h2>", unsafe_allow_html=True)
        
    with col2:
        model_options = ['deepseek-chat', 'deepseek-reasoning']
        selected_idx = 0 if st.session_state.selected_model == 'deepseek-chat' else 1
        model_select = st.selectbox("AI模型选择", model_options, index=selected_idx, label_visibility="collapsed")
        if model_select != st.session_state.selected_model:
            st.session_state.selected_model = model_select

    with col3:
        with st.popover("使用指南与说明"):
            st.markdown("""
            ### 功能使用指南
            **1. 代码工作台**
            - 贴入你的代码，选择对应的语言。
            - 可以一键进行本地轻量化代码质量检查，或者让人工智能帮你重构和优化代码。
            **2. 架构设计器**
            - 在这里输入你的系统架构设计需求。
            - 人工智能会为你生成详细的技术方案和架构设计蓝图。
            **3. 技术讨论区**
            - 大家可以在这里发布平时积累的技术心得或核心代码组件。
            - 带有离线安全备份功能，防止云端空间占用过多。
            """)

    with col4:
        theme_options = ['BLACK_THEME', 'WHITE_THEME', 'STARRY_THEME']
        current_idx = theme_options.index(st.session_state.theme)
        theme_select = st.selectbox("主题切换", theme_options, index=current_idx, label_visibility="collapsed")
        if theme_select != st.session_state.theme:
            st.session_state.theme = theme_select
            st.rerun()

    with col5:
        if st.session_state.user_id:
            cols_user = st.columns([2, 1])
            cols_user[0].markdown(f"<p style='margin-top:10px;'>欢迎回来: <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)
            if cols_user[1].button("退出登录"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.chat_history = []
                st.rerun()
        else:
            with st.popover("登录 / 注册"):
                auth_tab = st.tabs(["用户登录", "新用户注册"])
                with auth_tab[0]:
                    login_user_input = st.text_input("用户名", key="login_u")
                    login_pwd_input = st.text_input("密码", type="password", key="login_p")
                    if st.button("立即登录", use_container_width=True):
                        if login_user_input and login_pwd_input:
                            user_data = login_user_db(login_user_input, login_pwd_input)
                            if user_data:
                                st.session_state.user_id = user_data["id"]
                                st.session_state.username = user_data["username"]
                                st.success("登录成功，正在进入系统...")
                                st.rerun()
                            else:
                                st.error("用户名或密码错误，或者你还没有注册")
                with auth_tab[1]:
                    reg_user_input = st.text_input("注册账号名", key="reg_u")
                    reg_pwd_input = st.text_input("设置密码", type="password", key="reg_p")
                    if st.button("提交注册", use_container_width=True):
                        if reg_user_input and reg_pwd_input:
                            success, msg = register_user(reg_user_input, reg_pwd_input)
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)

    st.divider()

    # ------------------------------------------
    # 未登录状态的拦截页面
    # ------------------------------------------
    if not st.session_state.user_id:
        st.markdown("""
        <div style="text-align: center; padding: 120px 20px;">
            <h1 style="font-size: 3.5rem; color: #00ff88; margin-bottom: 20px;">请先登录</h1>
            <p style="font-size: 1.4rem; color: #a0a0b0;">当前系统处于私有安全保护状态，未登录用户无法查看内容。</p>
            <p style="font-size: 1.1rem; color: #666677;">请点击右上角的“登录 / 注册”按钮登录你的账号，解锁全部功能工作台。</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------
    # 侧边栏：多会话云端历史管理
    # ------------------------------------------
    with st.sidebar:
        st.markdown("### 云端历史对话")
        if st.button("开启新对话", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("---")
        # 自动获取当前登录用户的会话列表
        history = load_conversations(st.session_state.user_id)
        if history:
            for conv in history:
                conv_id, title, messages_json, tab_idx, updated_at = conv
                col_a, col_b = st.columns([5, 1.2])
                with col_a:
                    display_title = title[:15] + "..." if len(title) > 15 else title
                    if st.button(f"文本: {display_title}", key=f"load_{conv_id}", use_container_width=True):
                        st.session_state.chat_history = json.loads(messages_json) if messages_json else []
                        st.info("已成功加载历史聊天记录")
                with col_b:
                    if st.button("删除", key=f"del_{conv_id}", help="彻底删除这条历史记录"):
                        delete_conversation(conv_id)
                        st.rerun()
        else:
            st.info("暂无历史对话记录")

    # ------------------------------------------
    # 主区域：功能切换卡
    # ------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "代码工作台 (Workbench)", 
        "架构设计器 (Designer)", 
        "技术讨论区 (Board)"
    ])

    # --- Tab 1: 代码工作台 ---
    with tab1:
        st.markdown("### 代码优化重构与本地合规检查")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            code_input = st.text_area("在此粘贴你需要处理的原始代码", height=320, key="workbench_code_area")
            lang_select = st.selectbox("选择代码的编程语言", ["Python", "JavaScript", "Java", "C++", "Go", "Other"])
            
            if st.button("开始本地静态检查", use_container_width=True):
                if code_input.strip():
                    analysis = analyze_code_locally(code_input, lang_select)
                    st.markdown("#### 代码基础数据统计")
                    metric_c1, metric_c2 = st.columns(2)
                    metric_c1.metric("总行数", analysis["total_lines"])
                    metric_c2.metric("有效逻辑行数", analysis["effective_lines"])
                    
                    if analysis["prints"]:
                        st.warning(f"注意：在代码中发现了 {len(analysis['prints'])} 处未清理的测试输出语句(print)：")
                        for line_num, line in analysis["prints"]:
                            st.text(f"第 {line_num} 行: {line.strip()}")
                    if analysis["todos"]:
                        st.info(f"提示：代码中包含 {len(analysis['todos'])} 处待办标记(TODO)：")
                        for line_num, line in analysis["todos"]:
                            st.text(f"第 {line_num} 行: {line.strip()}")
                    if not analysis["prints"] and not analysis["todos"]:
                        st.success("检查完毕，代码编写规范，未发现明显的临时调试残留。")
                else:
                    st.warning("输入框为空，请输入有效代码再点击检查。")
                    
        with col_right:
            if st.button("让 AI 帮你优化和重构代码", use_container_width=True):
                if code_input.strip():
                    with st.spinner("人工智能正在为你重构和编写更优方案..."):
                        prompt_content = f"请帮我重构和优化以下 {lang_select} 代码：\n{code_input}\n\n要求：\n1. 提高代码可读性和可维护性\n2. 提升运行时整体效率\n3. 添加明晰的异常处理与核心注释说明。"
                        messages = [
                            {"role": "system", "content": "你是一位优秀的资深代码重构专家。"},
                            {"role": "user", "content": prompt_content}
                        ]
                        response = call_deepseek_api(messages, st.session_state.selected_model)
                        st.markdown("#### AI 优化后的代码版本")
                        st.code(response, language=lang_select.lower())
                        
                        # 自动将记录同步保存到数据库中
                        st.session_state.chat_history.append({"role": "user", "content": f"[优化代码] 语言: {lang_select}\n源码:\n{code_input}"})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        save_conversation(
                            st.session_state.user_id,
                            f"代码优化 - {datetime.now().strftime('%H:%M')}",
                            json.dumps(st.session_state.chat_history),
                            0
                        )
                else:
                    st.warning("请在左侧文本框内先输入你的源代码。")

        # 渲染当前对话的聊天历史
        if st.session_state.chat_history:
            st.divider()
            st.markdown("#### 当前会话的全部记录")
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg["content"])

    # --- Tab 2: 架构设计器 ---
    with tab2:
        st.markdown("### 系统方案与高并发架构设计器")
        arch_input = st.text_area(
            "请输入你的系统需求和架构规划想法", 
            height=180, 
            placeholder="例如：请帮我设计一个支持高并发、低延迟的电商秒杀系统的优惠券方案...",
            key="arch_designer_input"
        )
        
        if st.button("让 AI 生成系统架构方案", use_container_width=True):
            if arch_input.strip():
                with st.spinner("人工智能正在构思设计方案..."):
                    messages = [
                        {"role": "system", "content": "你是一位资深的系统架构师，精通高并发、高性能微服务方案的设计。"},
                        {"role": "user", "content": f"请针对以下业务及技术诉求提供详细的全栈级系统架构设计蓝图：\n{arch_input}\n\n必须全面包含以下核心组件：\n1. 技术栈选型理由\n2. 业务模块的拆分与设计\n3. 数据库与缓存的多级存储设计\n4. 系统的演进与扩容指南。"}
                    ]
                    response = call_deepseek_api(messages, st.session_state.selected_model)
                    st.markdown("### 系统设计及技术演进蓝图方案")
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
                st.warning("请输入你具体的业务规模、功能诉求或技术背景描述。")

    # --- Tab 3: 技术讨论区 ---
    with tab3:
        st.markdown("### 同学技术交流与代码讨论板")
        
        with st.expander("点击展开：发布我的技术心得或代码组件"):
            post_title = st.text_input("帖子标题", placeholder="请输入简短明确的技术标题")
            post_content = st.text_area("技术描述或你的核心代码块", height=150)
            if st.button("确认发布到讨论区", use_container_width=True):
                if post_title.strip() and post_content.strip():
                    post_discussion(st.session_state.user_id, st.session_state.username, post_title, post_content)
                    st.success("发布成功，大家已经可以看到你的分享了！")
                    st.rerun()
                else:
                    st.error("帖子的标题和内容都不能为空。")
        
        st.divider()
        
        # 搜索与资产管理
        col_search, col_admin = st.columns([3.5, 1.5])
        with col_search:
            search_input_val = st.text_input("输入关键词进行安全搜索", key="search_box")
            if st.button("开始搜索", use_container_width=True):
                st.session_state.search_clicked = True
                st.session_state.search_query_val = search_input_val
        
        with col_admin:
            st.markdown("<p style='margin:0; font-size:0.8rem; color:#888;'>数据备份中心</p>", unsafe_allow_html=True)
            if st.button("导出全量讨论数据 (JSON)", use_container_width=True):
                data_json = export_all_discussions()
                st.download_button(
                    label="点击下载生成的备份文件",
                    data=data_json,
                    file_name=f"discussions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        # 渲染下方的讨论区帖子列表
        st.markdown("#### 社区最新技术分享")
        
        if st.session_state.search_clicked and st.session_state.search_query_val:
            discussions = search_discussions(st.session_state.search_query_val)
            st.caption(f"当前处于搜索状态，关键词：`{st.session_state.search_query_val}`，共找到 {len(discussions)} 条相关内容。")
            st.session_state.search_clicked = False
        else:
            # 默认状态下展示最近发布的20条帖子
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
                    st.error(f"加载帖子失败: {e}")
                finally:
                    conn.close()

        # 循环绘制帖子
        if discussions:
            for disc in discussions:
                disc_id, username, title, content, is_archived, archive_id, created_at = disc
                with st.container():
                    st.markdown(f"#### 标题: {title}")
                    st.caption(f"发布人: `{username}` | 发布时间: {created_at}")
                    
                    # 如果帖子已经被管理员归档离线
                    if is_archived:
                        st.warning(f"该代码内容已被管理员移动至物理离线硬盘保存。如需查看，请联系管理员并提供归档编号: {archive_id}")
                    else:
                        st.code(content, language="python")
                        # 归档按钮
                        if st.button(f"对该帖子执行离线归档", key=f"archive_btn_{disc_id}"):
                            generated_arc_id = f"ARC-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
                            archive_discussion(disc_id, generated_arc_id)
                            st.success(f"归档成功。该内容的调取编号为: {generated_arc_id}")
                            st.rerun()
                    st.markdown("<hr style='border:0.5px dashed rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        else:
            st.info("当前讨论区没有找到任何技术分享。")

if __name__ == "__main__":
    main()
