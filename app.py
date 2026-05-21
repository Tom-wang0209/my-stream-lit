● import streamlit as st
  import requests
  import json
  from datetime import datetime
  import time
  import random

  DEEPSEEK_API_KEY = "sk-ebed2ac63e5a44d590dbebcb8346f9cd"
  DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
  OLLAMA_API_URL = "http://localhost:11434/api/generate"

  MODELS = {
      'deepseek-chat': {'name': 'DeepSeek Chat', 'type': 'api', 'description': 'Official Flagship'},
      'deepseek-reasoning': {'name': 'DeepSeek R1', 'type': 'api', 'description': 'Official Reasoning'},
      'qwen2.5-coder:7b': {'name': 'Qwen2.5 Coder', 'type': 'ollama', 'description': 'Local Code Model'},
      'deepseek-r1:8b': {'name': 'DeepSeek R1 8B', 'type': 'ollama', 'description': 'Local Reasoning'}
  }

  st.set_page_config(page_title="Code Hub", layout="wide", page_icon="C")

  if 'logged_in' not in st.session_state:
      st.session_state.logged_in = False
  if 'username' not in st.session_state:
      st.session_state.username = 'admin'
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
  if 'show_guide' not in st.session_state:
      st.session_state.show_guide = False
  if 'show_settings' not in st.session_state:
      st.session_state.show_settings = False

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
  """

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
          stars_html += f'<div class="star" style="left:{x}; top:{y}; width:{size}; height:{size};
  animation-delay:{delay}; animation-duration:{duration};"></div>'
      for i in range(3):
          x = f"{random.randint(50, 100)}%"
          y = f"{random.randint(0, 50)}%"
          delay = f"{random.randint(0, 10)}s"
          stars_html += f'<div class="shooting-star" style="left:{x}; top:{y}; animation-delay:{delay};"></div>'
      stars_html += '</div>'
      st.markdown(stars_html, unsafe_allow_html=True)

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
          return "Request timeout. Please try again."
      except requests.exceptions.RequestException as e:
          return f"API call failed: {str(e)}"
      except Exception as e:
          return f"Unknown error: {str(e)}"

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
          return result.get('response', 'No response received')
      except requests.exceptions.ConnectionError:
          return "Cannot connect to local Ollama service. Please ensure Ollama is running (execute `ollama serve`)"
      except requests.exceptions.Timeout:
          return "Local model response timeout. Please try again."
      except Exception as e:
          return f"Local model call failed: {str(e)}"

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

  st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
  col_tb_model, col_tb_guide, col_tb_theme, col_tb_auth, col_spacer = st.columns([2.5, 1.2, 1.5, 1.2, 5.6])

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
      if st.button("Ollama Guide", use_container_width=True, key="guide_btn_toolbar"):
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
              st.session_state.show_settings = False
              st.rerun()
      else:
          with st.popover("Login"):
              username = st.text_input("Username", placeholder="Enter username", key="login_username")
              password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
              if st.button("Login", use_container_width=True, key="login_submit"):
                  if username == st.session_state.username and password == st.session_state.password:
                      st.session_state.logged_in = True
                      st.rerun()
                  else:
                      st.error("Invalid username or password")

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
          <h1 style="color: #58a6ff; margin: 0;">Ollama Setup Guide</h1>
      </div>
      """, unsafe_allow_html=True)
      if st.button("Back to Code Hub", use_container_width=True, key="back_from_guide"):
          st.session_state.show_guide = False
          st.rerun()
      st.markdown("---")
      st.markdown("""
      ## Step 1: Download and Install Ollama

      1. Visit the official website: [ollama.com](https://ollama.com)
      2. Download the installation package for your operating system:
         - **Windows**: Download the .exe installer and run it
         - **macOS**: Download the .dmg file and drag to Applications folder
         - **Linux**: Run the official installation script provided on the website

      ## Step 2: Download and Start Local Models

      Open your terminal (Terminal/CMD) and run the following commands:

      ### Qwen2.5 Coder (Recommended for code tasks)
      ```bash
      ollama run qwen2.5-coder:7b
      ```

      ### DeepSeek R1 8B (Recommended for reasoning tasks)
      ```bash
      ollama run deepseek-r1:8b
      ```

      This will automatically download the model file (approximately 4.7GB for the first time, which may take some time
  depending on your network speed).

      ## Step 3: Ensure Ollama Service is Running

      By default, the Ollama service starts automatically after installation. To manually start or verify the service
  status:

      ### Start Ollama Service
      ```bash
      ollama serve
      ```

      ### Verify Service Status
      Open your browser and visit: http://localhost:11434

      If you see "Ollama is running", the service is working properly.

      ### View Installed Models
      ```bash
      ollama list
      ```

      ## Step 4: Connect to Code Hub

      Once Ollama is running:
      1. Return to Code Hub
      2. Select a local model from the model dropdown menu in the top-right
      3. Start using the zero-cost local AI assistant!

      ## Troubleshooting

      ### Q: Models download very slowly?
      A: You can set up a mirror to accelerate downloads:
      ```bash
      # Windows PowerShell
      $env:OLLAMA_HOST="mirrors.ollama.com"
      # Linux/macOS
      export OLLAMA_HOST="mirrors.ollama.com"
      ```

      ### Q: How to check if Ollama is running?
      A: Browser access http://localhost:11434 or run `ollama list` in terminal

      ### Q: Model response is very slow?
      A: This is normal for local models. Consider upgrading your hardware or switching to cloud models for faster
  responses.
      """)
      st.info("Tip: Local models, while slower, are completely free and protect data privacy. Perfect for code review
  and learning!")

  elif st.session_state.show_settings:
      st.markdown("""
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
          <h1 style="color: #58a6ff; margin: 0;">Security Settings</h1>
      </div>
      """, unsafe_allow_html=True)
      if st.button("Back to Code Hub", use_container_width=True, key="back_from_settings"):
          st.session_state.show_settings = False
          st.rerun()
      st.markdown("---")
      st.markdown("### Account Management")
      st.markdown("Modify your account credentials below. Changes take effect immediately.")
      col1, col2 = st.columns(2)
      with col1:
          new_username = st.text_input(
              "New Username",
              value=st.session_state.username,
              placeholder="Enter new username",
              key="new_username_input"
          )
      with col2:
          new_password = st.text_input(
              "New Password",
              value=st.session_state.password,
              type="password",
              placeholder="Enter new password",
              key="new_password_input"
          )
      col1, col2 = st.columns(2)
      with col1:
          if st.button("Save Changes", use_container_width=True, key="save_security"):
              if new_username.strip() and new_password.strip():
                  st.session_state.username = new_username
                  st.session_state.password = new_password
                  st.success("Account credentials updated successfully!")
                  time.sleep(1)
                  st.rerun()
              else:
                  st.error("Username and password cannot be empty")
      with col2:
          if st.button("Reset to Default", use_container_width=True, key="reset_security"):
              st.session_state.username = 'admin'
              st.session_state.password = '123456'
              st.success("Reset to default credentials!")
              time.sleep(1)
              st.rerun()

  else:
      with st.sidebar:
          st.markdown("""
          <div style="text-align: center; padding: 20px 0;">
              <h1 style="color: #58a6ff; font-size: 1.5rem; margin: 0;">Code Hub</h1>
              <p style="color: #8b949e; font-size: 0.85rem; margin-top: 8px;">AI-Powered Code Assistant</p>
          </div>
          """, unsafe_allow_html=True)
          st.markdown("---")
          if st.button("New Chat", use_container_width=True, key="new_chat_btn_sidebar"):
              st.session_state.messages = []
              st.session_state.current_conversation = None
              st.session_state.new_chat += 1
              st.rerun()
          st.markdown("---")
          search_query = st.text_input(
              "Search History",
              placeholder="Filter conversations...",
              key="history_search_sidebar"
          )
          st.markdown("---")
          if st.session_state.conversations:
              for idx, conv in enumerate(st.session_state.conversations):
                  if search_query.lower() in conv['title'].lower():
                      with st.container():
                          col1, col2 = st.columns([4, 1])
                          with col1:
                              if st.button(
                                  f"{conv['title'][:20]}...",
                                  key=f"conv_{idx}",
                                  use_container_width=True
                              ):
                                  st.session_state.messages = conv['messages'].copy()
                                  st.session_state.current_conversation = conv
                                  st.session_state.chat_tab = conv.get('tab', 0)
                                  st.rerun()
                          with col2:
                              if st.button("Delete", key=f"del_{idx}"):
                                  st.session_state.conversations.pop(idx)
                                  if st.session_state.current_conversation == conv:
                                      st.session_state.current_conversation = None
                                      st.session_state.messages = []
                                  st.rerun()
          else:
              st.info("No conversation history")
          st.markdown("---")
          if st.button("Security Settings", use_container_width=True, key="security_settings_btn"):
              st.session_state.show_settings = True
              st.rerun()

      tab1, tab2 = st.tabs(["Code Hub Workbench", "Cross-Language Architecture Designer"])

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
                                  st.markdown(f'<div class="analysis-card highlight">{highlight}</div>',
  unsafe_allow_html=True)
                          with st.expander("Bug Detection"):
                              if analysis.get('bugs'):
                                  for bug in analysis['bugs']:
                                      st.markdown(f'''
                                      <div class="analysis-card bug">
                                          <strong>Line {bug.get("line", "?")}: {bug.get("issue",
  "Unknown")}</strong><br>
                                          <span style="color: #8b949e;">Reason: {bug.get("reason", "Unknown")}</span>
                                      </div>
                                      ''', unsafe_allow_html=True)
                              else:
                                  st.info("No issues detected!")
                          with st.expander("Suggestions"):
                              for suggestion in analysis.get('suggestions', []):
                                  st.markdown(f'<div class="analysis-card suggestion">{suggestion}</div>',
  unsafe_allow_html=True)
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
                              st.info(f"For longer code, consider downloading the development environment from the
  [official website]({url})")

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
                                          st.metric("Effective Lines", analysis.get('stats', {}).get('effective_lines',
  0))
                                      with cols[2]:
                                          st.metric("Empty Lines", analysis.get('stats', {}).get('empty_lines', 0))
                                      with st.expander("Highlights", expanded=True):
                                          for highlight in analysis.get('highlights', []):
                                              st.markdown(f'<div class="analysis-card highlight">{highlight}</div>',
  unsafe_allow_html=True)
                                      with st.expander("Bug Detection"):
                                          if analysis.get('bugs'):
                                              for bug in analysis['bugs']:
                                                  st.markdown(f'''
                                                  <div class="analysis-card bug">
                                                      <strong>Line {bug.get("line", "?")}: {bug.get("issue",
  "Unknown")}</strong><br>
                                                      <span style="color: #8b949e;">Reason: {bug.get("reason",
  "Unknown")}</span>
                                                  </div>
                                                  ''', unsafe_allow_html=True)
                                          else:
                                              st.info("No issues detected!")
                                      with st.expander("Suggestions"):
                                          for suggestion in analysis.get('suggestions', []):
                                              st.markdown(f'<div class="analysis-card suggestion">{suggestion}</div>',
  unsafe_allow_html=True)
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
                                          st.info(f"For longer code, consider downloading the development environment
  from the [official website]({url})")
                      if st.session_state.current_conversation is None:
                          timestamp = datetime.now().strftime('%H:%M')
                          title = f"Code Refactor {timestamp}"
                          st.session_state.conversations.insert(0, {
                              'title': title,
                              'messages': st.session_state.messages.copy(),
                              'tab': 0
                          })
                          st.session_state.current_conversation = st.session_state.conversations[0]
                      else:
                          st.session_state.current_conversation['messages'] = st.session_state.messages.copy()

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
                          "content": """You are a full-stack architecture design expert for Code Hub. Your tasks are:
  1. Design a complete cross-language full-stack architecture based on user requirements
  2. Output a clear project directory tree structure
  3. Explain the role and interaction of each language module
  4. Recommend appropriate technology stacks
  5. Provide deployment suggestions
  6. Use Markdown format for output, mark code blocks with specific languages
  7. Display the directory tree using a clear tree structure"""
                      }
                      messages = [system_message] + st.session_state.messages
                      response = get_ai_response(messages, st.session_state.selected_model)
                      st.markdown(response)
                      st.session_state.messages.append({"role": "assistant", "content": response})
                      if st.session_state.current_conversation is None:
                          timestamp = datetime.now().strftime('%H:%M')
                          title = f"Architecture Design {timestamp}"
                          st.session_state.conversations.insert(0, {
                              'title': title,
                              'messages': st.session_state.messages.copy(),
                              'tab': 1
                          })
                          st.session_state.current_conversation = st.session_state.conversations[0]
                      else:
                          st.session_state.current_conversation['messages'] = st.session_state.messages.copy()
