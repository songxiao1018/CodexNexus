# 导入依赖模块
import markdown  # Markdown处理库
import os  # 文件系统操作
import get_test_back  # 自定义模块：代码执行和结果返回
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, abort  # Web框架及组件
from aiTalk import get_ai_response  # 自定义模块：AI对话处理
from md_2_html import mdToHtml  # 自定义模块：Markdown转HTML
import requests
from flask_cors import CORS  # pip install flask-cors
import sqlite3
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime
import threading
import time



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 设置一个安全的密钥
DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'points.db')

# 设置文章存储目录配置
app.config['ARTICLES_DIR'] = 'articles'

CORS(app)  # 启用跨域支持




# 在 app.config 下方或合适位置定义收藏
BOOKMARKS = [
    # {'name': 'Google', 'url': 'https://www.google.com'},
    # {'name': 'GitHub', 'url': 'https://github.com'},
    # {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com'},
    # {'name': 'ChatGPT', 'url': 'https://chat.openai.com'},
    # {'name': 'Bing', 'url': 'https://www.bing.com'},
    # {'name': '知乎', 'url': 'https://www.zhihu.com'},
    # {'name': '掘金', 'url': 'https://juejin.cn'},
    # {'name': '哔哩哔哩', 'url': 'https://www.bilibili.com'},
    # {'name': 'YouTube', 'url': 'https://www.youtube.com'},
    # {'name': 'LeetCode', 'url': 'https://leetcode.com'},
    # {'name': 'W3Schools', 'url': 'https://www.w3schools.com'},
    # {'name': 'MDN Web Docs', 'url': 'https://developer.mozilla.org'},
    {'name': '积分系统', 'url': '/all_points'},
    {'name': '学员状态', 'url': '/userresult'},
    {'name': '芯晴花园', 'url': 'https://codecin.com'},
    {'name': '未来引擎', 'url': 'http://121.43.66.70'},
]





@app.route('/userresult', methods=['GET', 'POST'])
def userresult():
    image = 'report.png'  # 默认图片
    
    if request.method == 'POST':
        # 获取用户输入并添加.png后缀
        user_input = request.form.get('image_name')
        if len(user_input) > 10:
            image = 'report.png'
        else: 
            # 简单清理输入（防止路径遍历攻击）
            safe_input = ''.join(filter(str.isalnum, user_input)) if user_input else ''
            if safe_input:
                image = f"{safe_input}.png"
    
    return render_template('userresult.html', image_file=image)


def split_into_rows(items, rows=2):
    """将列表平均分配成指定行数"""
    result = []
    k = []
    for idx, item in enumerate(items):
        k.append(item)
        if len(k) == rows:
            result.append(k)
            k = []
    if k:
        result.append(k)
    return result


# 密码验证装饰器
def password_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session and request.path != '/all_points':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin':  # 硬编码的密码
            session['authenticated'] = True
            return redirect(url_for('class_'))
        else:
            return render_template('login.html', error='密码错误')
    return render_template('login.html')

# 登出
@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))



def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    if not os.path.exists(os.path.dirname(DATABASE)):
        os.makedirs(os.path.dirname(DATABASE))
        
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date DATE NOT NULL,
            students TEXT NOT NULL
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            course_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/class')
@password_required
def class_():
    return render_template('class.html')

@app.route('/get_courses', methods=['GET'])
@password_required
def get_courses():
    conn = get_db_connection()
    courses = conn.execute(
        'SELECT id, name, date, students FROM courses ORDER BY date DESC'
    ).fetchall()
    conn.close()
    
    courses_list = []
    for course in courses:
        courses_list.append({
            'id': course['id'],
            'name': course['name'],
            'date': course['date'],
            'students': course['students']
        })
    
    return jsonify(courses_list[:10])

@app.route('/create_course', methods=['POST'])
@password_required
def create_course():
    data = request.get_json()
    name = data['name']
    date = data['date']
    students = data['students']
    
    # 验证日期格式
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建课程
    cursor.execute(
        'INSERT INTO courses (name, date, students) VALUES (?, ?, ?)',
        (name, date, students)
    )
    course_id = cursor.lastrowid
    
    # 初始化学生积分
    student_list = [s.strip() for s in students.split(',')]
    for student in student_list:
        cursor.execute(
            'INSERT INTO points (student_name, points, course_id) VALUES (?, ?, ?)',
            (student, 0, course_id)
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'status': 'success',
        'course_id': course_id,
        'students': student_list
    })

@app.route('/get_course_data', methods=['GET'])
@password_required
def get_course_data():
    course_id = request.args.get('course_id')
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # 获取所有学生的累计积分
    student_points = {}
    for student in course['students'].split(','):
        student = student.strip()
        total = conn.execute(
            'SELECT SUM(points) as total FROM points WHERE student_name = ?',
            (student,)
        ).fetchone()['total'] or 0
        student_points[student] = total
    
    # 获取今日积分
    today_points = {}
    today_records = conn.execute(
        'SELECT student_name, points FROM points WHERE course_id = ?',
        (course_id,)
    ).fetchall()
    
    for record in today_records:
        student = record['student_name']
        points = record['points']
        if student in today_points:
            today_points[student] += points
        else:
            today_points[student] = points
    
    conn.close()
    
    return jsonify({
        'course_name': course['name'],
        'course_date': course['date'],
        'students': course['students'].split(','),
        'student_points': student_points,
        'today_points': today_points
    })

@app.route('/add_points', methods=['POST'])
@password_required
def add_points():
    data = request.get_json()
    course_id = data['course_id']
    student_names = data['students']
    points = int(data['points'])
    
    if not student_names:
        return jsonify({'error': 'No students selected'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 验证课程是否存在
        course = cursor.execute(
            'SELECT students FROM courses WHERE id = ?',
            (course_id,)
        ).fetchone()
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        valid_students = [s.strip() for s in course['students'].split(',')]
        
        # 为每个学生添加积分
        for student in student_names:
            if student not in valid_students:
                return jsonify({
                    'error': f'Student {student} not in course'
                }), 400
            
            cursor.execute(
                'INSERT INTO points (student_name, points, course_id) VALUES (?, ?, ?)',
                (student, points, course_id)
            )
        
        conn.commit()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

@app.route('/all_points')
def all_points():
    conn = get_db_connection()
    
    # # 查询所有学生的总积分
    # cursor = conn.execute('''
    #     SELECT student_name, SUM(points) as total 
    #     FROM points 
    #     GROUP BY student_name
    #     ORDER BY total DESC
    # ''')

    # 查询points表中所有的学生姓名
    cursor = conn.execute('SELECT DISTINCT student_name FROM points')
    students = cursor.fetchall()

    # 打印全部学生姓名
    student_names = [row['student_name'] for row in students]
    # print("All students:", student_names)


    studentss = []
    for student in student_names:
        total_points = conn.execute(
            'SELECT SUM(points) as total FROM points WHERE student_name = ?',
            (student,)
        ).fetchone()['total'] or 0

        studentss.append({
            'name': student,
            'total': total_points
        })

    # 添加按积分排序
    studentss.sort(key=lambda x: x['total'], reverse=True)
    
    conn.close()
    return render_template('all_points.html', students=studentss)

# 添加新路由 - 积分调整页面
@app.route('/adjust_points', methods=['GET', 'POST'])
@password_required
def adjust_points():
    if request.method == 'POST':
        student_name = request.form['student_name'].strip()
        operation = request.form['operation']
        points_value = int(request.form['points_value'])
        
        if not student_name:
            return render_template('adjust_points.html', error="请填写学生姓名")
        
        if points_value <= 0:
            return render_template('adjust_points.html', error="积分值必须大于0")
        
        # 确定最终积分值（加分或扣分）
        points = points_value if operation == 'add' else -points_value
        
        conn = get_db_connection()
        try:
            # 查找学生是否存在于任何课程中
            student_exists = conn.execute(
                'SELECT 1 FROM points WHERE student_name = ? LIMIT 1',
                (student_name,)
            ).fetchone()
            
            # if not student_exists:
            #     return render_template('adjust_points.html', error=f"学生 {student_name} 不存在")
            
            # 插入积分记录（不关联特定课程）
            conn.execute(
                'INSERT INTO points (student_name, course_id, points) VALUES (?, ?, ?)',
                (student_name, 1, points)
            )
            conn.commit()
            
            # 获取学生当前总积分
            total_points = conn.execute(
                'SELECT SUM(points) as total FROM points WHERE student_name = ?',
                (student_name,)
            ).fetchone()['total'] or 0
            
            success_msg = f"已为 {student_name} {operation} {points_value} 分。当前总分: {total_points}"
            return render_template('adjust_points.html', success=success_msg)
            
        except Exception as e:
            conn.rollback()
            return render_template('adjust_points.html', error=f"操作失败: {str(e)}")
            
        finally:
            conn.close()
    
    # GET 请求时显示空表单
    return render_template('adjust_points.html')


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
    """主页路由"""
    articles = get_article_list()
    bookmarks = split_into_rows(BOOKMARKS)  # 分成4行
    return render_template('index.html', articles=articles, bookmarks=bookmarks)



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


    app.run(host="0.0.0.0", port=3333)  # 注意关闭reloader避免重复启动


    # app.run(host="0.0.0.0", port=3333, use_reloader=False, threaded=False)