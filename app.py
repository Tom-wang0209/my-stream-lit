import streamlit as st
  import time
  from datetime import datetime

  # 页面配置
  st.set_page_config(
      page_title="代码重构助手",
      page_icon="🔧",
      layout="wide",
      initial_sidebar_state="expanded"
  )

  # 自定义CSS - 极客暗黑风
  st.markdown("""
  <style>
      .stApp {
          background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
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
          transition: all 0.3s;
      }
      .stButton>button:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
      }
      .sidebar-title {
          color: #58a6ff;
          font-size: 1.2rem;
          font-weight: bold;
          margin-bottom: 1rem;
      }
      .history-item {
          padding: 0.5rem;
          margin: 0.3rem 0;
          background: #21262d;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
      }
      .history-item:hover {
          background: #30363d;
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
  </style>
  """, unsafe_allow_html=True)

  # ==================== Session State 初始化 ====================
  if 'logged_in' not in st.session_state:
      st.session_state.logged_in = False
  if 'username' not in st.session_state:
      st.session_state.username = ''
  if 'password' not in st.session_state:
      st.session_state.password = '123456'  # 默认密码
  if 'reset_count' not in st.session_state:
      st.session_state.reset_count = 0
  if 'conversations' not in st.session_state:
      st.session_state.conversations = []
  if 'current_conversation' not in st.session_state:
      st.session_state.current_conversation = None
  if 'selected_language' not in st.session_state:
      st.session_state.selected_language = 'Python'
  if 'selected_model' not in st.session_state:
      st.session_state.selected_model = '本地基础模型'

  # 代码重构模拟（纯前端逻辑）
  def simulate_refactor(code, language):
      """模拟代码重构输出"""
      refactored = f"# 重构后的{language}代码\n"
      refactored += f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
      refactored += "# ==================== 开始 ====================\n\n"

      lines = code.split('\n')
      for i, line in enumerate(lines, 1):
          if line.strip():
              refactored += f"    # {language} 优化后的逻辑\n"
              refactored += f"    {line.strip()}\n"
          else:
              refactored += "\n"

      refactored += "\n# ==================== 结束 ====================\n"
      refactored += f"# 共 {len([l for l in lines if l.strip()])} 行有效代码\n"

      return refactored

  # 深度剖析模拟
  def analyze_code(code, language):
      """生成代码深度剖析结果"""
      lines = code.split('\n')
      non_empty = len([l for l in lines if l.strip()])

      highlights = []
      bugs = []
      suggestions = []

      if len(lines) > 50:
          highlights.append(f"🚀 代码规模较大 ({len(lines)} 行)，建议拆分为模块化管理")
      highlights.append(f"✨ 支持 {language} 语言特性优化")
      highlights.append(f"📊 代码复杂度评估: 中等")

      if "print" in code.lower():
          bugs.append({
              'line': code.lower().index("print") // max(1, len(code) // len(lines)) + 1,
              'issue': '调试语句未清理',
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

  # 获取语言对应的GitHub环境链接
  def get_github_url(language):
      urls = {
          'Python': 'https://github.com/features/actions',
          'C++': 'https://github.com/features/actions',
          'JavaScript': 'https://github.com/features/actions'
      }
      return urls.get(language, 'https://github.com')

  # ==================== 登录页面 ====================
  if not st.session_state.logged_in:
      st.markdown('<h1 style="color: #58a6ff; text-align: center;">🔐 代码重构助手</h1>', unsafe_allow_html=True)
      st.markdown('<p style="color: #8b949e; text-align: center;">极客暗黑风 · 本地零成本运行</p>',
  unsafe_allow_html=True)

      # 登录表单
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
                      # 第一次重置，直接设新密码
                      new_password = st.text_input("新密码", type="password", key="new_pwd_first")
                      if st.button("确认重置", key="confirm_first"):
                          if new_password:
                              st.session_state.password = new_password
                              st.session_state.reset_count += 1
                              st.success("密码重置成功！")
                              time.sleep(1)
                              st.rerun()
                  else:
                      # 后续重置，需要旧密码验证
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
      # 侧边栏
      with st.sidebar:
          st.markdown('<div class="sidebar-title">📁 历史记录</div>', unsafe_allow_html=True)

          # 新建对话
          if st.button("➕ 新建对话", use_container_width=True):
              st.session_state.current_conversation = None
              st.rerun()

          # 历史搜索
          search_query = st.text_input("🔍 搜索历史", placeholder="输入关键词过滤...")

          # 显示历史记录
          st.markdown("---")
          if st.session_state.conversations:
              filtered = [c for c in st.session_state.conversations
                         if search_query.lower() in c['title'].lower()]

              for idx, conv in enumerate(filtered):
                  col1, col2 = st.columns([4, 1])
                  with col1:
                      if st.button(f"💬 {conv['title'][:20]}...",
                                  key=f"conv_{idx}",
                                  use_container_width=True):
                          st.session_state.current_conversation = conv
                          st.rerun()
                  with col2:
                      if st.button("🗑️", key=f"del_{idx}"):
                          st.session_state.conversations.remove(conv)
                          st.rerun()
          else:
              st.info("暂无历史记录")

          # 语言选择
          st.markdown("---")
          st.markdown('<div class="sidebar-title">⚙️ 设置</div>', unsafe_allow_html=True)
          language = st.selectbox(
              "编程语言",
              ["Python", "C++", "JavaScript"],
              index=["Python", "C++", "JavaScript"].index(st.session_state.selected_language)
          )
          st.session_state.selected_language = language

          # 模型选择
          model = st.selectbox(
              "代码模型",
              ["本地基础模型", "本地高级模型", "本地专业模型"],
              index=["本地基础模型", "本地高级模型", "本地专业模型"].index(st.session_state.selected_model)
          )
          st.session_state.selected_model = model

          # 登出
          st.markdown("---")
          if st.button("🚪 退出登录", use_container_width=True):
              st.session_state.logged_in = False
              st.rerun()

      # 主内容区
      st.markdown('<h1 style="color: #58a6ff;">🔧 代码重构助手</h1>', unsafe_allow_html=True)
      st.markdown(f'<p style="color: #8b949e;">当前模型: {st.session_state.selected_model} | 语言:
  {st.session_state.selected_language}</p>',
                  unsafe_allow_html=True)

      # 代码输入区
      st.markdown("---")
      col1, col2 = st.columns([3, 1])
      with col1:
          st.markdown("### 📝 输入代码")

      code_input = st.text_area(
          "请粘贴需要重构的代码...",
          height=300,
          value=st.session_state.current_conversation['input'] if st.session_state.current_conversation else "",
          key="code_area"
      )

      # 操作按钮
      col1, col2, col3 = st.columns(3)
      with col1:
          if st.button("🚀 优化重构", use_container_width=True):
              if code_input.strip():
                  with st.spinner("正在分析代码..."):
                      time.sleep(1.5)

                      # 生成重构代码
                      refactored = simulate_refactor(code_input, st.session_state.selected_language)
                      analysis = analyze_code(code_input, st.session_state.selected_language)

                      # 保存到历史
                      timestamp = datetime.now().strftime('%H:%M')
                      title = f"对话 {timestamp}"
                      st.session_state.conversations.insert(0, {
                          'title': title,
                          'input': code_input,
                          'output': refactored,
                          'analysis': analysis,
                          'language': st.session_state.selected_language,
                          'time': datetime.now()
                      })
                      st.session_state.current_conversation = st.session_state.conversations[0]

                      st.success("重构完成！")
                      st.rerun()
              else:
                  st.warning("请输入代码！")

      with col2:
          if st.button("🗑️ 清空", use_container_width=True):
              st.session_state.current_conversation = None
              st.rerun()

      # 显示结果
      if st.session_state.current_conversation:
          st.markdown("---")
          st.markdown("### ✨ 重构结果")

          refactored = st.session_state.current_conversation['output']
          st.code(refactored, language=st.session_state.selected_language.lower())

          # 深度剖析面板
          st.markdown("---")
          st.markdown("### 🔍 代码深度剖析")

          analysis = st.session_state.current_conversation['analysis']

          # 统计信息
          cols = st.columns(3)
          with cols[0]:
              st.metric("总行数", analysis['stats']['total_lines'])
          with cols[1]:
              st.metric("有效行数", analysis['stats']['effective_lines'])
          with cols[2]:
              st.metric("空行数", analysis['stats']['empty_lines'])

          # 亮点
          with st.expander("✨ 代码亮点", expanded=True):
              for highlight in analysis['highlights']:
                  st.markdown(f'<div class="analysis-card highlight">{highlight}</div>',
                             unsafe_allow_html=True)

          # Bug定位
          with st.expander("🪲 Bug定位与根因"):
              if analysis['bugs']:
                  for bug in analysis['bugs']:
                      st.markdown(f'''
                      <div class="analysis-card bug">
                          <strong>第 {bug['line']} 行: {bug['issue']}</strong><br>
                          <span style="color: #8b949e;">根因: {bug['reason']}</span>
                      </div>
                      ''', unsafe_allow_html=True)
              else:
                  st.info("🎉 未发现明显问题！")

          # 简化建议
          with st.expander("💡 可简化建议"):
              for suggestion in analysis['suggestions']:
                  st.markdown(f'<div class="analysis-card suggestion">{suggestion}</div>',
                             unsafe_allow_html=True)

          # 长代码提示
          if analysis['stats']['total_lines'] > 30:
              st.markdown("---")
              st.info(f"💾 代码较长，建议在 {get_github_url(st.session_state.selected_language)} 官方环境测试")
