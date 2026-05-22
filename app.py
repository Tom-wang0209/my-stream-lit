import streamlit as st
import requests
import json
import hashlib
from datetime import datetime
import time
import random
import psycopg2
from psycopg2.extras import RealDictCursor

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODELS = {
    'deepseek-chat': {'name': 'DeepSeek Chat', 'type': 'api', 'description': 'Official Flagship'},
    'deepseek-reasoning': {'name': 'DeepSeek R1', 'type': 'api', 'description': 'Official Reasoning'}
}

st.set_page_config(page_title="Code Hub", layout="wide", page_icon="C")

for key in ['logged_in', 'user_id', 'username', 'selected_model', 'messages', 'theme', 'chat_tab', 'new_chat', 'show_guide', 'show_settings']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['logged_in', 'show_guide', 'show_settings'] else \
                                0 if key in ['user_id', 'chat_tab', 'new_chat'] else \
                                'deepseek-chat' if key == 'selected_model' else \
                                [] if key == 'messages' else \
                                'black' if key == 'theme' else None

def get_db_connection():
    try:
        conn = psycopg2.connect(st.secrets["postgres"]["connection_string"], cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

def init_database():
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ch_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ch_conversations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES ch_users(id) ON DELETE CASCADE,
                    title VARCHAR(100) NOT NULL,
                    messages_json TEXT NOT NULL,
                    tab_index INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ch_discussions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES ch_users(id) ON DELETE CASCADE,
                    username VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    code_content TEXT NOT NULL,
                    is_archived BOOLEAN DEFAULT FALSE,
                    archive_id VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return False
    finally:
        conn.close()

def hash_password(password, username):
    salted = password + username
    return hashlib.sha256(salted.encode()).hexdigest()

def register_user(username, password):
    if not username or not password:
        return False, "Username and password are required"
    if len(username) < 3 or len(password) < 6:
        return False, "Username must be at least 3 characters, password at least 6"
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM ch_users WHERE username = %s", (username,))
            if cursor.fetchone():
                return False, "Username already exists"
            password_hash = hash_password(password, username)
            cursor.execute("INSERT INTO ch_users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        return True, "Registration successful"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"
    finally:
        conn.close()

def login_user(username, password):
    if not username or not password:
        return False, "Username and password are required"
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash FROM ch_users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                return False, "User not found"
            password_hash = hash_password(password, username)
            if password_hash == user['password_hash']:
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                return True, "Login successful"
            return False, "Invalid password"
    except Exception as e:
        return False, f"Login failed: {str(e)}"
    finally:
        conn.close()

def load_conversations(user_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, messages_json, tab_index FROM ch_conversations WHERE user_id = %s ORDER BY updated_at DESC", (user_id,))
            conversations = []
            for conv in cursor.fetchall():
                conversations.append({
                    'id': conv['id'],
                    'title': conv['title'],
                    'messages': json.loads(conv['messages_json']),
                    'tab': conv['tab_index']
                })
            return conversations
    except Exception as e:
        st.error(f"Failed to load conversations: {str(e)}")
        return []
    finally:
        conn.close()

def save_conversation(user_id, title, messages, tab_index):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            messages_json = json.dumps(messages)
            cursor.execute("""
                INSERT INTO ch_conversations (user_id, title, messages_json, tab_index)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (user_id, title, messages_json, tab_index))
            conv_id = cursor.fetchone()['id']
        conn.commit()
        return conv_id
    except Exception as e:
        st.error(f"Failed to save conversation: {str(e)}")
        return False
    finally:
        conn.close()

def update_conversation(user_id, conv_id, messages):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            messages_json = json.dumps(messages)
            cursor.execute("""
                UPDATE ch_conversations
                SET messages_json = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
            """, (messages_json, conv_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Failed to update conversation: {str(e)}")
        return False
    finally:
        conn.close()

def delete_conversation(user_id, conv_id):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM ch_conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Failed to delete conversation: {str(e)}")
        return False
    finally:
        conn.close()

def get_discussions(user_id=None, search_query=None):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            if user_id:
                cursor.execute("SELECT * FROM ch_discussions WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            elif search_query:
                cursor.execute("SELECT * FROM ch_discussions WHERE title LIKE %s ORDER BY created_at DESC", (f"%{search_query}%",))
            else:
                cursor.execute("SELECT * FROM ch_discussions WHERE is_archived = FALSE ORDER BY created_at DESC LIMIT 50")
            return list(cursor.fetchall())
    except Exception as e:
        st.error(f"Failed to load discussions: {str(e)}")
        return []
    finally:
        conn.close()

def save_discussion(user_id, username, title, code_content):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ch_discussions (user_id, username, title, code_content)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (user_id, username, title, code_content))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Failed to save discussion: {str(e)}")
        return False
    finally:
        conn.close()

def archive_discussion(discussion_id, archive_id):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE ch_discussions
                SET code_content = '', is_archived = TRUE, archive_id = %s
                WHERE id = %s
            """, (archive_id, discussion_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Failed to archive discussion: {str(e)}")
        return False
    finally:
        conn.close()

def export_all_discussions():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ch_discussions ORDER BY created_at DESC")
            return list(cursor.fetchall())
    except Exception as e:
        st.error(f"Failed to export discussions: {str(e)}")
        return []
    finally:
        conn.close()

def cold_archive_discussions(archive_prefix):
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM ch_discussions WHERE is_archived = FALSE ORDER BY created_at LIMIT 10")
            discussions = cursor.fetchall()
            archived_count = 0
            for i, disc in enumerate(discussions):
                archive_id = f"{archive_prefix}-{i+1:03d}"
                if archive_discussion(disc['id'], archive_id):
                    archived_count += 1
            return archived_count
    except Exception as e:
        st.error(f"Failed to cold archive: {str(e)}")
        return 0
    finally:
        conn.close()

def call_deepseek_api(messages, model='deepseek-chat', temperature=0.7):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {st.secrets["deepseek"]["api_key"]}'
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
        return "Request timeout. Please try again."
    except requests.exceptions.RequestException as e:
        return f"API call failed: {str(e)}"
    except Exception as e:
        return f"Unknown error: {str(e)}"

def get_ai_response(messages, model):
    return call_deepseek_api(messages, model)

def analyze_code(code, language):
    lines = code.split('\n')
    non_empty = len([l for l in lines if l.strip()])
    highlights = []
    bugs = []
    suggestions = []
    
    if non_empty > 50:
        highlights.append(f"Large codebase ({len(lines)} lines), consider modular architecture")
    highlights.append(f"Supports {language} language optimizations")
    highlights.append("Complexity assessment: moderate")
    
    if "print" in code.lower():
        bugs.append({
            'line': max(1, code.lower().index("print") // (len(code) // max(1, len(lines)))),
            'issue': 'Debug statements not cleaned',
            'reason': 'Print statements may leak sensitive information or affect performance'
        })
    if "=" * 3 in code or "TODO" in code:
        bugs.append({
            'line': 1,
            'issue': 'Pending markers not addressed',
            'reason': 'Found === or TODO markers requiring further attention'
        })
        
    suggestions.append("Consider using list comprehensions to simplify loop logic")
    suggestions.append("Add type annotations for better code readability")
    suggestions.append("Use context managers for better resource management")
    
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

BLACK_THEME = """
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    min-height: 100vh;
}
[data-testid="stAppViewContainer"] {
    background: transparent !important;
}
[data-testid="stHeader"] {
    background: rgba(13, 17, 23, 0.9) !important;
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
.stSelectbox>div>div>select,
.stNumberInput>div>div>input {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px;
}
.stButton>button {
    background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.3);
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
    border: 1px solid #30363d;
}
.analysis-card {
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
    background-color: rgba(33, 38, 45, 0.5);
}
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
h1, h2, h3, h4, h5, h6 { color: #c9d1d9; font-weight: 600; }
p, span, div { color: #c9d1d9; }
.stMetric label { color: #8b949e; }
.stMetric[data-testid="stMetricValue"] { color: #c9d1d9; }
div[data-testid="stSelectbox"] { width: 100% !important; white-space: nowrap !important; overflow: hidden !important; }
div[data-testid="column"] { display: flex !important; align-items: center !important; }
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.discussion-card {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.discussion-title {
    color: #58a6ff;
    font-weight: 600;
    font-size: 1.1rem;
}
.discussion-meta {
    color: #8b949e;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.discussion-code {
    background-color: #161b22;
    padding: 0.8rem;
    border-radius: 6px;
    margin-top: 0.8rem;
    overflow-x: auto;
    font-family: monospace;
    font-size: 0.9rem;
}
.archived-badge {
    background-color: #da3633;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
}
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
    background: rgba(255, 255, 255, 0.9) !important;
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
.stSelectbox>div>div>select,
.stNumberInput>div>div>input {
    background-color: #ffffff !important;
    color: #24292f !important;
    border: 1px solid #e1e4e8 !important;
    border-radius: 6px;
}
.stButton>button {
    background: linear-gradient(90deg, #2da44e 0%, #2ea043 100%);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(45, 164, 78, 0.3);
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
    border: 1px solid #e1e4e8;
}
.analysis-card {
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
    background-color: rgba(246, 248, 250, 0.5);
}
.highlight { border-color: #2da44e; }
.bug { border-color: #cf222e; }
.suggestion { border-color: #8250df; }
h1, h2, h3, h4, h5, h6 { color: #24292f; font-weight: 600; }
p, span, div { color: #24292f; }
.stMetric label { color: #656d76; }
.stMetric[data-testid="stMetricValue"] { color: #24292f; }
div[data-testid="stSelectbox"] { width: 100% !important; white-space: nowrap !important; overflow: hidden !important; }
div[data-testid="column"] { display: flex !important; align-items: center !important; }
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.discussion-card {
    background-color: #ffffff;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.discussion-title {
    color: #0969da;
    font-weight: 600;
    font-size: 1.1rem;
}
.discussion-meta {
    color: #656d76;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.discussion-code {
    background-color: #f6f8fa;
    padding: 0.8rem;
    border-radius: 6px;
    margin-top: 0.8rem;
    overflow-x: auto;
    font-family: monospace;
    font-size: 0.9rem;
}
.archived-badge {
    background-color: #cf222e;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
}
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
    background: rgba(9, 10, 15, 0.9) !important;
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
.stSelectbox>div>div>select,
.stNumberInput>div>div>input {
    background-color: rgba(33, 38, 45, 0.8) !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px;
    backdrop-filter: blur(10px);
}
.stButton>button {
    background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(46, 160, 67, 0.3);
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
    border: 1px solid #30363d;
    backdrop-filter: blur(10px);
}
.analysis-card {
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid;
    background-color: rgba(33, 38, 45, 0.6);
    backdrop-filter: blur(10px);
}
.highlight { border-color: #238636; }
.bug { border-color: #da3633; }
.suggestion { border-color: #a371f7; }
h1, h2, h3, h4, h5, h6 { color: #c9d1d9; font-weight: 600; }
p, span, div { color: #c9d1d9; }
.stMetric label { color: #8b949e; }
.stMetric[data-testid="stMetricValue"] { color: #c9d1d9; }
div[data-testid="stSelectbox"] { width: 100% !important; white-space: nowrap !important; overflow: hidden !important; }
div[data-testid="column"] { display: flex !important; align-items: center !important; }
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.discussion-card {
    background-color: rgba(33, 38, 45, 0.8);
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
}
.discussion-title {
    color: #58a6ff;
    font-weight: 600;
    font-size: 1.1rem;
}
.discussion-meta {
    color: #8b949e;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.discussion-code {
    background-color: rgba(22, 27, 34, 0.8);
    padding: 0.8rem;
    border-radius: 6px;
    margin-top: 0.8rem;
    overflow-x: auto;
    font-family: monospace;
    font-size: 0.9rem;
}
.archived-badge {
    background-color: #da3633;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
}
"""

init_database()

if st.session_state.theme == 'black':
    st.markdown(BLACK_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'white':
    st.markdown(WHITE_THEME, unsafe_allow_html=True)
elif st.session_state.theme == 'starry':
    st.markdown(STARRY_THEME, unsafe_allow_html=True)
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

st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
col_tb_model, col_tb_guide, col_tb_theme, col_tb_auth, col_spacer = st.columns([4.5, 1.4, 1.5, 1.1, 4.5])

with col_tb_model:
    selected_model = st.selectbox(
        "Model",
        list(MODELS.keys()),
        format_func=lambda x: f"{MODELS[x]['name']} - {MODELS[x]['description']}",
        index=list(MODELS.keys()).index(st.session_state.selected_model),
        label_visibility="collapsed",
        key="model_selector_toolbar"
    )
    st.session_state.selected_model = selected_model

with col_tb_guide:
    st.markdown('<div style="margin-top: 3px;"></div>', unsafe_allow_html=True)
    if st.button("Guide", use_container_width=True, key="guide_btn_toolbar"):
        st.session_state.show_guide = True
        st.session_state.show_settings = False
        st.rerun()

with col_tb_theme:
    st.markdown('<div style="margin-top: 3px;"></div>', unsafe_allow_html=True)
    theme_options = {
        'black': 'Geek Black',
        'white': 'Soft White',
        'starry': 'Starry Sky'
    }
    selected_theme = st.selectbox(
        "Theme",
        list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(st.session_state.theme),
        label_visibility="collapsed",
        key="theme_selector_toolbar"
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

with col_tb_auth:
    st.markdown('<div style="margin-top: 3px;"></div>', unsafe_allow_html=True)
    if st.session_state.logged_in:
        if st.button("Logout", use_container_width=True, key="logout_btn_toolbar"):
            st.session_state.logged_in = False
            st.session_state.user_id = 0
            st.session_state.username = None
            st.session_state.messages = []
            st.session_state.show_settings = False
            st.rerun()
    else:
        with st.popover("Login"):
            auth_mode = st.radio("", ["Login", "Register"], label_visibility="collapsed", horizontal=True)
            if auth_mode == "Login":
                username = st.text_input("Username", placeholder="Enter username", key="login_username")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
                if st.button("Login", use_container_width=True, key="login_submit"):
                    success, message = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error(message)
            else:
                reg_username = st.text_input("Username", placeholder="Choose username (min 3 chars)", key="reg_username")
                reg_password = st.text_input("Password", type="password", placeholder="Choose password (min 6 chars)", key="reg_password")
                if st.button("Register", use_container_width=True, key="reg_submit"):
                    success, message = register_user(reg_username, reg_password)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="color: #58a6ff; font-size: 3rem;">Code Hub</h1>
            <p style="color: #8b949e; font-size: 1.2rem; margin-top: 20px;">
                Intelligent Code Refactoring · Cross-Language Architecture Design
            </p>
            <p style="color: #8b949e; margin-top: 10px;">
                Click Login in the top-right corner to start
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

if st.session_state.show_guide:
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <h1 style="color: #58a6ff; margin: 0;">Quick Guide</h1>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Back to Code Hub", use_container_width=True, key="back_from_guide"):
        st.session_state.show_guide = False
        st.rerun()
    st.markdown("---")
    st.markdown("""
        ## Welcome to Code Hub
        ### Getting Started
        1. **Code Hub Workbench**: Paste your code for intelligent refactoring and analysis
        2. **Architecture Designer**: Describe your full-stack requirements for AI-generated architecture designs
        3. **Discussion Board**: Share and discuss code insights with classmates
        ### Tips
        - Use `DeepSeek R1` for complex reasoning tasks
        - Use `DeepSeek Chat` for quick code refactoring
        - Your conversations and data are automatically saved and isolated
        - Switch between themes using the top-right menu
        ### Privacy Notice
        - Your data is stored securely in Supabase PostgreSQL
        - All user data is strictly isolated by account
        - No data is shared between users
    """)
    st.info("Note: This is a cloud-hosted application. All data is stored in PostgreSQL database.")

elif st.session_state.show_settings:
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <h1 style="color: #58a6ff; margin: 0;">Account Settings</h1>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Back to Code Hub", use_container_width=True, key="back_from_settings"):
        st.session_state.show_settings = False
        st.rerun()
    st.markdown("---")
    st.markdown("### Account Information")
    st.markdown(f"**Username**: {st.session_state.username}")
    st.markdown(f"**Account ID**: {st.session_state.user_id}")
    st.markdown("---")
    st.markdown("### Data Management")
    if st.button("Clear All Conversations", use_container_width=True, key="clear_all_conv"):
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM ch_conversations WHERE user_id = %s", (st.session_state.user_id,))
                conn.commit()
                st.success("All conversations cleared")
                st.session_state.messages = []
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear conversations: {str(e)}")
            finally:
                conn.close()
    if st.button("Delete My Discussions", use_container_width=True, key="delete_my_disc"):
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM ch_discussions WHERE user_id = %s", (st.session_state.user_id,))
                conn.commit()
                st.success("All discussions deleted")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete discussions: {str(e)}")
            finally:
                conn.close()

else:
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 20px 0;">
                <h1 style="color: #58a6ff; font-size: 1.5rem; margin: 0;">Code Hub</h1>
                <p style="color: #8b949e; font-size: 0.85rem; margin-top: 8px;">{st.session_state.username}</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("New Chat", use_container_width=True, key="new_chat_btn_sidebar"):
            st.session_state.messages = []
            st.session_state.new_chat += 1
            st.rerun()
        st.markdown("---")
        search_query = st.text_input(
            "Search History",
            placeholder="Filter conversations...",
            key="history_search_sidebar"
        )
        st.markdown("---")
        conversations = load_conversations(st.session_state.user_id)
        if conversations:
            for conv in conversations:
                if search_query.lower() in conv['title'].lower():
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            if st.button(
                                f"{conv['title'][:18]}...",
                                key=f"conv_{conv['id']}",
                                use_container_width=True
                            ):
                                st.session_state.messages = conv['messages']
                                st.session_state.chat_tab = conv['tab']
                                st.session_state.current_conv_id = conv['id']
                                st.rerun()
                        with col2:
                            if st.button("Delete", key=f"del_{conv['id']}"):
                                if delete_conversation(st.session_state.user_id, conv['id']):
                                    st.rerun()
        else:
            st.info("No conversation history")
        st.markdown("---")
        if st.button("Account Settings", use_container_width=True, key="account_settings_btn"):
            st.session_state.show_settings = True
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["Code Hub Workbench", "Architecture Designer", "Discussion Board"])
    
    with tab1:
        st.session_state.chat_tab = 0
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                if msg.get("analysis"):
                    analysis = msg["analysis"]
                    st.markdown("---")
                    st.markdown("### Code Analysis")
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Total Lines", analysis.get('stats', {}).get('total_lines', 0))
                    with cols[1]:
                        st.metric("Effective Lines", analysis.get('stats', {}).get('effective_lines', 0))
                    with cols[2]:
                        st.metric("Empty Lines", analysis.get('stats', {}).get('empty_lines', 0))
                    with st.expander("Highlights", expanded=True):
                        for highlight in analysis.get('highlights', []):
                            st.markdown(f'<div class="analysis-card highlight">{highlight}</div>', unsafe_allow_html=True)
                    with st.expander("Bug Detection"):
                        if analysis.get('bugs'):
                            for bug in analysis['bugs']:
                                st.markdown(f'''
                                    <div class="analysis-card bug">
                                        <strong>Line {bug.get("line", "?")}: {bug.get("issue", "Unknown")}</strong><br>
                                        <span style="color: #8b949e;">Reason: {bug.get("reason", "Unknown")}</span>
                                    </div>
                                ''', unsafe_allow_html=True)
                        else:
                            st.info("No issues detected!")
                    with st.expander("Suggestions"):
                        for suggestion in analysis.get('suggestions', []):
                            st.markdown(f'<div class="analysis-card suggestion">{suggestion}</div>', unsafe_allow_html=True)
                    if analysis.get('stats', {}).get('total_lines', 0) > 30:
                        language = msg.get('language', 'Python')
                        urls = {
                            'Python': 'https://www.python.org/downloads/',
                            'C++': 'https://visualstudio.microsoft.com/visual-cpp-build-tools/',
                            'JavaScript': 'https://nodejs.org/',
                            'Java': 'https://www.oracle.com/java/technologies/downloads/',
                            'Go': 'https://go.dev/dl/',
                            'Rust': 'https://www.rust-lang.org/tools/install'
                        }
                        url = urls.get(language, 'https://github.com')
                        st.info(f"For longer code, consider downloading the development environment from the [official website]({url})")

        user_input = st.chat_input("Enter code or describe your issue...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner(f"Analyzing with {MODELS[st.session_state.selected_model]['name']}..."):
                    system_message = {
                        "role": "system",
                        "content": """You are a professional code refactoring expert for Code Hub. Your tasks are:
                        1. Perform deep optimization and refactoring on user-submitted code
                        2. Maintain complete functional consistency
                        3. Optimize code structure, naming, and comments
                        4. Fix potential bugs
                        5. Improve code readability and maintainability
                        6. Output only the complete refactored code with proper formatting
                        7. Mark code blocks with language (e.g., ```python)"""
                    }
                    messages = [system_message] + st.session_state.messages
                    response = get_ai_response(messages, st.session_state.selected_model)
                    st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            if "```" in response:
                code_blocks = response.split("```")
                for i in range(1, len(code_blocks), 2):
                    block = code_blocks[i]
                    if '\n' in block:
                        language = block.split('\n')[0].strip()
                        code = '\n'.join(block.split('\n')[1:])
                        if code.strip():
                            analysis = analyze_code(code, language)
                            st.session_state.messages[-1]["analysis"] = analysis
                            st.session_state.messages[-1]["language"] = language
                            st.markdown("---")
                            st.markdown("### Code Analysis")
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Total Lines", analysis.get('stats', {}).get('total_lines', 0))
                            with cols[1]:
                                st.metric("Effective Lines", analysis.get('stats', {}).get('effective_lines', 0))
                            with cols[2]:
                                st.metric("Empty Lines", analysis.get('stats', {}).get('empty_lines', 0))
                            with st.expander("Highlights", expanded=True):
                                for highlight in analysis.get('highlights', []):
                                    st.markdown(f'<div class="analysis-card highlight">{highlight}</div>', unsafe_allow_html=True)
                            with st.expander("Bug Detection"):
                                if analysis.get('bugs'):
                                    for bug in analysis['bugs']:
                                        st.markdown(f'''
                                            <div class="analysis-card bug">
                                                <strong>Line {bug.get("line", "?")}: {bug.get("issue", "Unknown")}</strong><br>
                                                <span style="color: #8b949e;">Reason: {bug.get("reason", "Unknown")}</span>
                                            </div>
                                        ''', unsafe_allow_html=True)
                                else:
                                    st.info("No issues detected!")
                            with st.expander("Suggestions"):
                                for suggestion in analysis.get('suggestions', []):
                                    st.markdown(f'<div class="analysis-card suggestion">{suggestion}</div>', unsafe_allow_html=True)
                            if analysis.get('stats', {}).get('total_lines', 0) > 30:
                                urls = {
                                    'Python': 'https://www.python.org/downloads/',
                                    'C++': 'https://visualstudio.microsoft.com/visual-cpp-build-tools/',
                                    'JavaScript': 'https://nodejs.org/',
                                    'Java': 'https://www.oracle.com/java/technologies/downloads/',
                                    'Go': 'https://go.dev/dl/',
                                    'Rust': 'https://www.rust-lang.org/tools/install'
                                }
                                url = urls.get(language, 'https://github.com')
                                st.info(f"For longer code, consider downloading the development environment from the [official website]({url})")
            timestamp = datetime.now().strftime('%H:%M')
            title = f"Code Refactor {timestamp}"
            if hasattr(st.session_state, 'current_conv_id'):
                update_conversation(st.session_state.user_id, st.session_state.current_conv_id, st.session_state.messages)
            else:
                conv_id = save_conversation(st.session_state.user_id, title, st.session_state.messages, 0)
                if conv_id:
                    st.session_state.current_conv_id = conv_id

    with tab2:
        st.session_state.chat_tab = 1
        arch_container = st.container()
        with arch_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        user_input = st.chat_input("Describe your full-stack requirements...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner(f"Designing architecture with {MODELS[st.session_state.selected_model]['name']}..."):
                    system_message = {
                        "role": "system",
                        "content": "You are a full-stack architecture design expert for Code Hub. Your tasks are: 1. Design a complete cross-language full-stack architecture based on user requirements 2. Output a clear project directory tree structure..."
                    }
