# CodexNexus

### CodexNexus - Python Flask 技术博客系统

# **项目概述**  

CodexNexus是一个基于Python Flask框架构建的现代化技术博客平台，集成了Markdown文档处理、交互式编程练习、AI智能助手和在线判题系统等功能。项目专为编程学习设计，提供沉浸式的技术文章阅读和代码实践体验。

# **核心技术栈**：

- **语言**：Python 3.x
- **框架**：Flask (Web服务) + Jinja2 (模板引擎)
- **前端**：HTML5 + CSS3 + JavaScript (原生)
- **数据处理**：SQLite（聊天记录存储）
- **辅助库**：Markdown、Requests、BeautifulSoup等

# **核心模块功能**：

- [x] 动态文章系统
- [x] AI智能助手
- [x] 代码判题引擎
- [x] 用户系统
- [x] 响应式UI

# **核心功能模块**：

1. **动态文章系统**
   - 支持Markdown格式技术文章（带代码高亮）
   - 交互式代码块（支持C++/Python在线编辑运行）
   - 客观题组件（单选/多选题自动判分）
   - 文章目录自动生成与导航

2. **AI智能助手**
   - 基于频率控制的聊天机器人（每小时60次请求）
   - 对话历史持久化存储（SQLite数据库）
   - 消息队列管理（collections.deque）

3. **代码判题引擎**
   - 集成在线判题系统（Hydro）
   - 支持C++/Python代码提交与测试
   - 输入/输出测试功能
   - 登录凭证管理（Session+Cookies）

4. **用户系统**
   - Hydro账户登录集成
   - Session管理
   - 凭证安全存储与展示

5. **响应式UI**
   - 三栏式布局（导航+文章+聊天）
   - 自适应代码编辑器（自动调整高度）
   - 移动端友好设计

# **项目结构**：
```
myblog/
├── aiTalk.py                 # AI聊天核心逻辑
├── app.py                    # Flask主应用
├── chat_history.db           # 聊天记录数据库
├── get_test_back.py          # 代码判题接口
├── language_replace.py       # 语言替换
├── login_hosts.py            # 登录凭证管理
├── md_2_html.py              # Markdown转换器（含交互组件）
├── templates/                # 前端模板
│   └── index.html            # 主界面
├── articles/                 # Markdown技术文章
│   ├── 文章1.md
│   ├── 文章2.md
│   └── 文章3.md
└── static/                   # 静态资源
    ├── style.css             # 全局样式
    └── script.js             # 交互逻辑
```

# **技术亮点**：

1. **Markdown深度扩展**：通过正则解析实现交互式代码/选择题组件
2. **频率控制算法**：滑动窗口限流保护AI服务（collections.deque）
3. **安全凭证管理**：Cookie分段存储+会话隔离
4. **代码沙盒集成**：通过CodeCin实现安全的远程代码执行
5. **UI/UX优化**：自动调整的代码编辑器、实时聊天滚动、响应式布局

# **应用场景**：

- 编程教学平台
- 技术博客社区
- 算法练习系统
- AI辅助学习工具

项目通过Flask的轻量级特性和模块化设计，实现了复杂交互功能与高性能的平衡，为技术学习者提供了一站式的编程学习环境。

# **鸣谢**：

感谢[Hydro](https://hydro.js.org/)开源OJ系统的作者，利用您的优秀项目，我成功实现了一个完整的编程学习平台。





# **项目日志**

2025-07-24 基础功能完成
2025-07-14 项目立项
