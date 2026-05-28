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
    page_title="Code Hub - 技术开发者社区",
    page_icon="None",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. 核心安全配置与初始化
# ==========================================
DB_CONN_STRING = st.secrets["postgres"]["connection_string"]
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# ==========================================
# 2. 视觉主题与高精对齐系统 (CSS 注入)
# ==========================================
ALIGNMENT_CSS = """
<style>
/* 统一对齐与单行高度控制 */
.stSelectbox>div>div>div, .stTextInput>div>div>input, .stButton>button, .stPopover>button {
    height: 42px !important;
    line-height: 42px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
/* 调整下拉框文字垂直居中 */
.stSelectbox>div>div>select {
    height: 42px !important;
}
/* 消除组件顶部的多余间距 */
[data-testid="stForm"] {
    padding: 15px !important;
}
div[data-testid="stColumn"] {
    display: flex;
    align-items: flex-end;
}
</style>
"""

BLACK_THEME = ALIGNMENT_CSS + """
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
h1, h2, h3, h4, h5, h6 {
    color: #00ff88 !important;
}
[data-testid="stSidebar"] {
    background-color: #15151a !important;
}
</style>
"""

WHITE_THEME = ALIGNMENT_CSS + """
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
h1, h2, h3, h4, h5, h6 {
    color: #2c3e50 !important;
}
[data-testid="stSidebar"] {
    background-color: #f8f9fa !important;
}
</style>
"""

STARRY_THEME = ALIGNMENT_CSS + """
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
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ch_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
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
    salted = password + username
    return hashlib.sha256(salted.encode()).hexdigest()

def register_user(username, password):
    conn = get_connection()
    if not conn:
        return False, "数据库连接失败"
    try:
        cur = conn.cursor()
        pwd_hash = hash_password(password, username)
        cur.execute(
            "INSERT INTO ch_users (username, password_hash) VALUES (%s, %s)",
            (username, pwd_hash)
        )
        conn.commit()
        cur.close()
        return True, "注册成功"
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "该用户名已被注册"
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
        st.error(f"保存历史记录失败: {e}")
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
        st.error(f"加载历史记录失败: {e}")
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
        st.error(f"删除历史记录失败: {e}")
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
        st.error(f"发布失败: {e}")
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
        st.error(f"检索失败: {e}")
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
        st.error(f"备份失败: {e}")
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
        return f"大模型服务连接失败: {e}"
    except Exception as e:
        return f"数据格式转换异常: {e}"

# ==========================================
# 8. 本地代码检查算法
# ==========================================
def analyze_code_locally(code, language):
    lines = code.split('\n')
    total_lines = len(lines)
    effective_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    
    print_pattern = re.compile(r'\bprint\s*\(')
    prints = [(i+1, line) for i, line in enumerate(lines) if print_pattern.search(line)]
    
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

    if st.session_state.theme == 'BLACK_THEME':
        st.markdown(BLACK_THEME, unsafe_allow_html=True)
    elif st.session_state.theme == 'WHITE_THEME':
        st.markdown(WHITE_THEME, unsafe_allow_html=True)
    elif st.session_state.theme == 'STARRY_THEME':
        st.markdown(STARRY_THEME, unsafe_allow_html=True)

    init_database()

    # ------------------------------------------
    # 精准控制宽度的顶部单行导航栏
    # ------------------------------------------
    col1, col2, col3, col4, col5 = st.columns([3.5, 2.0, 1.8, 1.5, 3.2])
    
    with col1:
        st.markdown("<h2 style='margin:0; padding:0; line-height:42px; font-size:1.65rem; white-space:nowrap;'>Code Hub 开发者社区</h2>", unsafe_allow_html=True)
        
    with col2:
        model_options = ['deepseek-chat', 'deepseek-reasoning']
        selected_idx = 0 if st.session_state.selected_model == 'deepseek-chat' else 1
        model_select = st.selectbox("核心模型", model_options, index=selected_idx, label_visibility="collapsed")
        if model_select != st.session_state.selected_model:
            st.session_state.selected_model = model_select

    with col3:
        with st.popover("阅读社区指南", use_container_width=True):
            st.markdown("""
            ### 社区模块说明
            **1. 代码工作台 (Workbench)**
            - 支持主流语言的本地静态规范检查与 AI 深度性能重构。
            **2. 架构设计器 (Designer)**
            - 支撑分布式、高并发全栈级生产系统演进方案的一键建模。
            **3. 技术讨论区 (Board)**
            - 全局技术资产沉淀与代码共享板块，支持冷备份数据归档。
            """)

    with col4:
        theme_options = ['BLACK_THEME', 'WHITE_THEME', 'STARRY_THEME']
        current_idx = theme_options.index(st.session_state.theme)
        theme_select = st.selectbox("系统主题", theme_options, index=current_idx, label_visibility="collapsed")
        if theme_select != st.session_state.theme:
            st.session_state.theme = theme_select
            st.rerun()

    with col5:
        if st.session_state.user_id:
            cols_user = st.columns([1.8, 1.2])
            cols_user[0].markdown(f"<p style='margin:0; line-height:42px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>用户: <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)
            if cols_user[1].button("注销登录", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.chat_history = []
                st.rerun()
        else:
            with st.popover("用户登录 / 注册", use_container_width=True):
                auth_tab = st.tabs(["身份验证", "建立新账号"])
                with auth_tab[0]:
                    login_user_input = st.text_input("用户名", key="login_u")
                    login_pwd_input = st.text_input("密码", type="password", key="login_p")
                    if st.button("进入社区", use_container_width=True):
                        if login_user_input and login_pwd_input:
                            user_data = login_user_db(login_user_input, login_pwd_input)
                            if user_data:
                                st.session_state.user_id = user_data["id"]
                                st.session_state.username = user_data["username"]
                                st.success("验证通过")
                                st.rerun()
                            else:
                                st.error("凭证有误或账号不存在")
                with auth_tab[1]:
                    reg_user_input = st.text_input("新账号名", key="reg_u")
                    reg_pwd_input = st.text_input("安全密码", type="password", key="reg_p")
                    if st.button("创建用户", use_container_width=True):
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
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="font-size: 3rem; color: #00ff88; margin-bottom: 20px;">开发者社区保护提示</h1>
            <p style="font-size: 1.2rem; color: #a0a0b0;">当前系统处于安全隔离状态，需验证开发者身份后方可访问。</p>
            <p style="font-size: 1rem; color: #666677;">请通过顶栏右侧的“用户登录 / 注册”面板进行身份验证，以解锁全部核心工作台。</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ------------------------------------------
    # 侧边栏：多会话云端历史管理
    # ------------------------------------------
    with st.sidebar:
        st.markdown("### 专属历史对话")
        if st.button("新建空白会话", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("---")
        history = load_conversations(st.session_state.user_id)
        if history:
            for conv in history:
                conv_id, title, messages_json, tab_idx, updated_at = conv
                col_a, col_b = st.columns([3.8, 1.2])
                with col_a:
                    display_title = title[:12] + "..." if len(title) > 12 else title
                    if st.button(f"会话: {display_title}", key=f"load_{conv_id}", use_container_width=True):
                        st.session_state.chat_history = json.loads(messages_json) if messages_json else []
                        st.info("历史记录已载入")
                with col_b:
                    if st.button("清除", key=f"del_{conv_id}"):
                        delete_conversation(conv_id)
                        st.rerun()
        else:
            st.caption("暂无活跃的历史对话")

    # ------------------------------------------
    # 主区域：标准开发者工作台
    # ------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "代码工作台 (Workbench)", 
        "架构设计器 (Designer)", 
        "技术讨论区 (Board)"
    ])

    # --- Tab 1: 代码工作台 ---
    with tab1:
        st.markdown("### 代码审查与自动化性能重构")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            code_input = st.text_area("请在此粘贴需要处理的源代码", height=300, key="workbench_code_area")
            lang_select = st.selectbox("源语言环境", ["Python", "JavaScript", "Java", "C++", "Go", "Other"])
            
            if st.button("运行本地静态规则扫描", use_container_width=True):
                if code_input.strip():
                    analysis = analyze_code_locally(code_input, lang_select)
                    st.markdown("#### 度量与指标统计")
                    metric_c1, metric_c2 = st.columns(2)
                    metric_c1.metric("物理行总数", analysis["total_lines"])
                    metric_c2.metric("有效逻辑行", analysis["effective_lines"])
                    
                    if analysis["prints"]:
                        st.warning(f"检测到 {len(analysis['prints'])} 处开发残留的调试输出语句 (print)：")
                        for line_num, line in analysis["prints"]:
                            st.text(f"行 {line_num}: {line.strip()}")
                    if analysis["todos"]:
                        st.info(f"检测到 {len(analysis['todos'])} 处挂起的待办事务标记 (TODO)：")
                        for line_num, line in analysis["todos"]:
                            st.text(f"行 {line_num}: {line.strip()}")
                    if not analysis["prints"] and not analysis["todos"]:
                        st.success("静态规则检查通过，未发现明显的临时调试代码残留。")
                else:
                    st.warning("请先录入需要扫描的代码内容。")
                    
        with col_right:
            if st.button("调用 AI 执行性能重构", use_container_width=True):
                if code_input.strip():
                    with st.spinner("生产级演进重构中..."):
                        # ==========================================
                        # 优化：强冷淡系统提示词，彻底规避繁琐与每一句的脚注
                        # ==========================================
                        system_instruction = """你是一个高冷的代码编译器，信奉极简主义。
【铁律】：
1. 必须只输出 Markdown 格式的纯净代码块，不准附带任何解释。
2. 严禁输出任何代码外部的文字、脚注、前言或总结。
3. 严格限制注释：代码内部的注释率必须低于 5%，只允许在最晦涩处写单行注释。
4. 杜绝过度设计：拒绝一切不必要的变量声明和过度封装。"""

                        user_instruction = f"请直接优化并重构以下 {lang_select} 源码，不准留下任何脚注或字外解释：\n{code_input}"

                        messages = [
                            {"role": "system", "content": system_instruction.strip()},
                            {"role": "user", "content": user_instruction.strip()}
                        ]
                        
                        response = call_deepseek_api(messages, st.session_state.selected_model)
                        st.markdown("#### 优化后的推荐版本")
                        st.code(response, language=lang_select.lower())
                        
                        st.session_state.chat_history.append({"role": "user", "content": f"[代码优化] 语言: {lang_select}\n源码:\n{code_input}"})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        save_conversation(
                            st.session_state.user_id,
                            f"代码优化 - {datetime.now().strftime('%H:%M')}",
                            json.dumps(st.session_state.chat_history),
                            0
                        )
                else:
                    st.warning("请在左侧区域先填充原始源码。")

        if st.session_state.chat_history:
            st.divider()
            st.markdown("#### 当前会话历史快照")
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg["content"])

    # --- Tab 2: 架构设计器 ---
    with tab2:
        st.markdown("### 分布式系统架构设计与高并发规划")
        arch_input = st.text_area(
            "业务诉求与系统瓶颈定义说明", 
            height=160, 
            placeholder="请在此描述您的业务图景，例如：设计一套具备高可用、具备多级缓存能力的全球化订单系统...",
            key="arch_designer_input"
        )
        
        if st.button("启动大模型方案推演", use_container_width=True):
            if arch_input.strip():
                with st.spinner("系统拓扑与解耦推演中..."):
                    # ==========================================
                    # 优化：强实用主义架构师提示词，杜绝车轱辘话和零碎脚注
                    # ==========================================
                    system_arch_instruction = """你是一位崇尚实用主义、言简意赅的资深系统架构师。
【铁律】：
1. 严禁使用任何形式的页面底部脚注。
2. 严禁学术化的长篇大论，直接使用 Markdown 表格、高干货列表输出解耦模块。
3. 方案仅包含核心拓扑栈、数据库多级存储以及确定的集群扩容步骤，去掉废话。"""

                    user_arch_instruction = f"请针对以下业务及技术诉求直接提供高并发架构设计蓝图，拒绝任何多余脚注：\n{arch_input}"

                    messages = [
                        {"role": "system", "content": system_arch_instruction.strip()},
                        {"role": "user", "content": user_arch_instruction.strip()}
                    ]
                    
                    response = call_deepseek_api(messages, st.session_state.selected_model)
                    st.markdown("### 技术演进蓝图与方案细节")
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
                st.warning("请输入具体的系统规模或技术改进诉求。")

    # --- Tab 3: 技术讨论区 ---
    with tab3:
        st.markdown("### 开发者公共技术研讨与代码资产版面")
        
        with st.expander("共享并发布我的最新开发心得 / 核心组件"):
            post_title = st.text_input("主题摘要", placeholder="请输入明确的技术讨论核心要点（限单行展示）")
            post_content = st.text_area("具体实现源码或详尽的技术方案描述", height=120)
            if st.button("广播发布到社区公共板块", use_container_width=True):
                if post_title.strip() and post_content.strip():
                    post_discussion(st.session_state.user_id, st.session_state.username, post_title, post_content)
                    st.success("发布成功，已并入公共检索库！")
                    st.rerun()
                else:
                    st.error("文章标题与正文详情均不可为空。")
        
        st.divider()
        
        # 统一控制对齐的长宽高与单行搜索排版
        col_search, col_admin = st.columns([3.5, 1.5])
        with col_search:
            search_input_val = st.text_input("技术关键词安全检索", placeholder="支持代码段或主题标题的参数化匹配", key="search_box", label_visibility="collapsed")
            if st.button("触发全局搜索", use_container_width=True):
                st.session_state.search_clicked = True
                st.session_state.search_query_val = search_input_val
        
        with col_admin:
            if st.button("全量资产冷备份导出 (JSON)", use_container_width=True):
                data_json = export_all_discussions()
                st.download_button(
                    label="保存生成的备份文件",
                    data=data_json,
                    file_name=f"discussions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        st.markdown("#### 最新公共研讨看板")
        
        if st.session_state.search_clicked and st.session_state.search_query_val:
            discussions = search_discussions(st.session_state.search_query_val)
            st.caption(f"搜索路由激活。关键词：`{st.session_state.search_query_val}`，命中结果： {len(discussions)} 项。")
            st.session_state.search_clicked = False
        else:
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
                    st.error(f"公共看板数据加载异常: {e}")
                finally:
                    conn.close()

        # 循环绘制标准的公共技术帖子卡片
        if discussions:
            for disc in discussions:
                disc_id, username, title, content, is_archived, archive_id, created_at = disc
                with st.container():
                    st.markdown(f"#### 主题: {title}")
                    st.caption(f"发布者: `{username}` | 沉淀时间: {created_at}")
                    
                    if is_archived:
                        st.warning(f"[安全提示] 该段核心代码资产已通过冷备份迁移至离线安全存储设备。如需调取完整快照，请联系管理员核对出库序列号: {archive_id}")
                    else:
                        st.code(content, language="python")
                        if st.button(f"安全离线归档", key=f"archive_btn_{disc_id}"):
                            generated_arc_id = f"ARC-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
                            archive_discussion(disc_id, generated_arc_id)
                            st.success(f"已安全离线。全局资产追踪号: {generated_arc_id}")
                            st.rerun()
                    st.markdown("<hr style='border:0.5px dashed rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        else:
            st.info("当前公共资产板块未检索到任何相关的技术讨论。")

if __name__ == "__main__":
    main()
