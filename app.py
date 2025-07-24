# 导入依赖模块
import markdown  # Markdown处理库
import os  # 文件系统操作
import get_test_back  # 自定义模块：代码执行和结果返回
from flask import Flask, render_template, jsonify, request, session  # Web框架及组件
from aiTalk import get_ai_response  # 自定义模块：AI对话处理
from md_2_html import mdToHtml  # 自定义模块：Markdown转HTML
import requests
from flask_cors import CORS  # pip install flask-cors

app = Flask(__name__)
CORS(app)  # 启用跨域支持



# 初始化Flask应用
app = Flask(__name__)
# 在 app = Flask(__name__) 之后添加
app.secret_key = 'your_secret_key_here'  # 设置一个安全的密钥
# 设置文章存储目录配置
app.config['ARTICLES_DIR'] = 'articles'

def get_article_list():
    """获取文章列表
    从配置目录中扫描所有Markdown文件，返回文章标题列表"""
    files = os.listdir(app.config['ARTICLES_DIR'])

    file_list = []
    list = [f.replace('.md', '') for f in files if f.endswith('.md')]

    for f in list:
        k = f.split(' ')
        file_list.append((int(k[0]),f))
        
    # 按标题排序
    articles = sorted(file_list, key=lambda x: x[0], reverse=False)

    # print(file_list)
    # print(list)
    # print(articles)

    return [k[1] for k in articles]

@app.route('/')
def index():
    """主页路由
    渲染包含所有文章标题的首页模板"""
    articles = get_article_list()
    return render_template('index.html', articles=articles)

@app.route('/article/<title>')
def get_article(title):
    """文章获取接口
    参数:
        title - 文章标题（来自URL路径）
    返回:
        JSON格式的文章内容（HTML格式）或404错误"""
    try:
        filepath = os.path.join(app.config['ARTICLES_DIR'], f"{title}.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # 将Markdown内容转换为HTML
        html_content = mdToHtml(content)
        return jsonify({
            'title': title,
            'content': html_content
        })
    except FileNotFoundError:
        return jsonify({'error': 'Article not found'}), 404
    


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()  # 更安全的获取JSON方式
        if not data or 'message' not in data:
            return jsonify({'error': 'Invalid request format'}), 400
            
        user_message = data['message']
        ai_response = get_ai_response(user_message)
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({'response': '系统处理消息时出错'})
    


@app.route('/submit_code', methods=['POST'])
def submit_code():
    """代码执行接口（POST请求）
    提交并执行用户代码，返回执行结果
    请求体:
        JSON格式：{
            "lang": "编程语言", 
            "code": "代码内容",
            "input": "输入数据"
        }
    返回:
        JSON格式：{"output": "执行结果"}"""
    data = request.json
    lang = data.get('lang')
    code = data.get('code')
    input_data = data.get('input')

    # 转换语言标识符（兼容处理）
    if lang == "python":
        lang = "py.py3"
    else:
        lang = "cc.cc20o2"

    # 调用自定义模块执行代码
    json_data = {
        "lang": lang,
        "code": code,
        "input": input_data,
        "pretest": True
    }
    execution_result = get_test_back.submit_code(data=json_data)
    
    return jsonify({
        'output': execution_result
    })



@app.route('/login_codecin', methods=['POST'])
def login_to_codecin():
    """处理 CodeCin 登录请求"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    try:
        # 1. 发送登录请求到 CodeCin
        login_url = "http://121.43.66.70/login"  # 替换为实际的登录URL
        data = {
            'uname': username,
            'password': password,
            'tfa': username,
            'authnChallenge': ""
        }
        
        response = requests.post(
            login_url,
            data=data,
            allow_redirects=False
        )
        
        # 2. 检查登录是否成功（根据实际网站调整）
        if response.status_code != 302:  # 通常登录成功会有重定向
            return jsonify({
                'success': False, 
                'message': '登录失败，请检查用户名和密码'
            })
        
        # 3. 获取登录后的 cookie
        cookies = response.cookies.get_dict()
        
        # 4. 将 cookie 存储到 session 中
        session['codecin_cookies'] = cookies
    
        # 获取第一个cookie的值用于显示
        sid = cookies.get("sid")
        sig = cookies.get("sid.sig")
        cookie_value = sid
        
        return jsonify({
            'success': True,
            'sid': sid,
            'sig': sig,
        })
        
    except Exception as e:
        # print(f"登录 CodeCin 出错: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'登录请求失败: {str(e)}'
        })

@app.route('/logout_codecin', methods=['POST'])
def logout_codecin():
    # 从session中移除cookie
    session.pop('codecin_cookies', None)
    return jsonify({'success': True})


if __name__ == '__main__':
    # 启动Flask开发服务器
    app.run(debug=True,port=3333,host="0.0.0.0")