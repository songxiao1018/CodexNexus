import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import os
import time
import math
from collections import namedtuple, defaultdict
from typing import List, Optional, NamedTuple
import shutil
import json
import csv  # 新增csv模块
from datetime import datetime, timedelta


import matplotlib
matplotlib.use('Agg')  # 在 import plt 前设置非交互后端


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image





# 配置常量
HTML_FILE = "page.html"
DB_FILE = "submissions_get.db"
BASE_URL = "https://codecin.com"
MAX_USERS = 3200
MAX_121_43_66_70 = 30 
MAX_codecin = 3200  
# BASE_URL = "http://121.43.66.70"
# MAX_USERS = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# SEARCH_USER = True  # 是否搜索用户提交记录
SEARCH_USER = False  # 是否搜索用户提交记录
SEARCH_PAGE = True  # 是否搜索提交记录页面
# SEARCH_PAGE = False  # 是否搜索提交记录页面
MAX_PAGE = 3
cookies_测试 = {
    "sid": "wAnFRAjNrZDZwYt9oS1Pez4byt9zGHfC",
    "sid.sig": "a5eOYbZ0GljDPGsBkhu_6eSEg2c"
}
cookies_宋杰 = { 
    "sid": "80jCkfCQdYV8yU5wXXdWvrtPJu3f06p3",
    "sid.sig": "xxuNrxBFv_4OnGlfHCTQmfZ2k28"
}

# 定义结构化数据类型
Submission = namedtuple('Submission', [
    'record_id', 'status', 'problem_code', 'problem_name', 
    'problem_url', 'submitter_name', 'submitter_id', 'time', 
    'memory', 'language', 'submit_time', 'school', 'result_url'
])




# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题





def fix_date_format(date_str):
    """将非标准日期格式转换为YYYY-MM-DD格式"""
    parts = re.split(r'[-/: ]', date_str)
    
    if len(parts) < 3:
        return date_str
    
    year = parts[0]
    month = parts[1].zfill(2)
    day = parts[2].zfill(2)
    
    return f"{year}-{month}-{day}"

def generate_submission_report(names, db_path='submissions.db', output_file='submission_report.json', csv_file='submission_data.csv'):
    """
    生成指定用户最近7天的提交统计报告，并将原始数据写入CSV
    
    参数:
    names (list): 需要统计的用户名列表
    db_path (str): SQLite数据库文件路径，默认为'submissions.db'
    output_file (str): 输出JSON文件路径，默认为'submission_report.json'
    csv_file (str): 输出CSV文件路径，默认为'submission_data.csv'
    """
    
    # 1. 确定日期范围（最近7天）
    today = datetime.now().date()
    dates = [today - timedelta(days=i) for i in range(7)]
    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    
    # 存储原始数据用于CSV
    all_rows = []
    column_names = []
    
    # 2. 连接数据库并执行查询
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 获取列名
        c.execute("PRAGMA table_info(submissions)")
        column_info = c.fetchall()
        column_names = [col[1] for col in column_info]  # 列名在元组的第二个位置
        
        # 构建SQL查询
        placeholders = ', '.join(['?'] * len(names))
        query = f"""
        SELECT *
        FROM submissions
        WHERE submitter_name IN ({placeholders})
        """
        # AND language = 'Python 3'
        
        # 执行查询
        c.execute(query, names)
        rows = c.fetchall()
        all_rows = rows  # 保存所有原始行数据
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return
    finally:
        if conn:
            conn.close()
    
    # 3. 处理查询结果 - 在Python中处理日期
    user_stats = defaultdict(lambda: defaultdict(int))
    filtered_rows = []  # 用于存储符合日期条件的行
    
    # 先获取列索引
    name_index = column_names.index('submitter_name')
    time_index = column_names.index('submit_time')
    
    for row in rows:
        submitter_name = row[name_index]
        submit_time = row[time_index]
        
        try:
            # 提取日期部分并修复格式
            raw_date = submit_time.split()[0]  # 取空格前的部分作为日期
            fixed_date = fix_date_format(raw_date)
            
            # 转换为日期对象
            submit_date = datetime.strptime(fixed_date, "%Y-%m-%d").date()
            
            # 检查是否在最近7天内
            if submit_date in dates:
                user_stats[submitter_name][submit_date.strftime("%Y-%m-%d")] += 1
                # 保存该行数据（包括原始日期格式）
                filtered_rows.append(row)
                
        except Exception as e:
            print(f"处理日期时出错: {submit_time} -> {e}")
    
    # 4. 构建结果字典
    result = {
        "times": date_strs,
        "datas": {}
    }
    
    for name in names:
        daily_counts = [user_stats[name].get(d, 0) for d in date_strs]
        result["datas"][name] = daily_counts
    
    # 5. 写入JSON文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"报告已成功生成到: {output_file}")
        
        # 调试输出
        print("日期范围:", date_strs)
        print("统计结果示例:")
        for name, counts in result["datas"].items():
            print(f"{name}: {counts}")
            
    except IOError as e:
        print(f"文件写入错误: {e}")

    
    columns_to_exclude = ['result_url', 'problem_url', 'record_id']
    filtered_rows = [list(row) for row in filtered_rows if all(col not in columns_to_exclude for col in row)]
    
    
    # 6. 写入CSV文件（包含所有原始列）
    if filtered_rows:
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写入列标题
                writer.writerow(column_names)
                # 写入数据行
                writer.writerows(filtered_rows)
            print(f"CSV数据已写入: {csv_file}")
        except Exception as e:
            print(f"写入CSV文件时出错: {e}")
    else:
        print("没有符合条件的数据可写入CSV")





# 从JSON文件加载数据
def load_data_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 主绘图函数
def plot_line_chart(data):
    # 准备时间数据（转换为datetime对象）
    dates = [datetime.strptime(t, "%Y-%m-%d") for t in data["times"]]
    
    # 设置图形
    plt.figure(figsize=(14, 8), dpi=100)
    plt.title("未来引擎-刷题变化趋势", fontsize=16, fontweight='bold')
    plt.xlabel("日期", fontsize=14)
    plt.ylabel("提交次数", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # 为每个人绘制折线
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'X']
    colors = plt.cm.tab10(np.linspace(0, 1, len(data["datas"])))
    
    for i, (name, values) in enumerate(data["datas"].items()):
        plt.plot(
            dates, 
            values,
            linewidth=2.5,
            marker=markers[i % len(markers)],
            markersize=8,
            color=colors[i],
            alpha=0.9,
            label=name
        )
    
    # 设置日期格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gcf().autofmt_xdate()
    
    # 添加图例
    plt.legend(title="人员列表", fontsize=11, title_fontsize=12, loc='best')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('static/user.png', dpi=150)
    
    # plt.show()





def remove_white_background(input_path, output_path, tolerance=15):
    """
    去除图片中的白色背景（设为透明）
    
    参数:
    input_path: 输入图片路径
    output_path: 输出图片路径（支持PNG格式）
    tolerance: 颜色容差（0-255），值越大被视为白色的颜色范围越广
    """
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        # 检测是否为白色像素（或接近白色）
        if item[0] > 255 - tolerance and item[1] > 255 - tolerance and item[2] > 255 - tolerance:
            # 设为完全透明 (R, G, B, A) 其中 A=0 表示透明
            new_data.append((255, 255, 255, 0))
        else:
            # 保留原始颜色和透明度
            new_data.append(item)
    
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"白色背景已移除！临时文件保存至: {output_path}")

def add_scaled_watermark(background_path, watermark_path, output_path, position=(0, 0), opacity=1.0, tolerance=15, scale=0.2):
    """
    将水印图片宽度缩放到背景图的指定比例后添加到主图上
    
    参数:
    background_path: 背景图片路径
    watermark_path: 水印图片路径
    output_path: 输出图片路径
    position: 水印位置 (x, y)，默认为左上角 (0, 0)
    opacity: 水印透明度 (0.0 - 1.0)
    tolerance: 白色检测容差
    scale: 水印宽度相对于背景宽度的比例 (例如0.2表示水印宽度=背景宽度×0.2)
    """
    # 1. 首先去除水印图的白色背景
    transparent_watermark_path = "transparent_temp.png"
    remove_white_background(watermark_path, transparent_watermark_path, tolerance)
    
    # 2. 准备背景和水印图片
    background = Image.open(background_path).convert("RGBA")
    watermark = Image.open(transparent_watermark_path).convert("RGBA")
    
    # 3. 计算新的水印尺寸 - 宽度为背景宽度的五分之一
    new_width = int(background.width * scale)
    
    # 计算新高度（保持宽高比）
    aspect_ratio = watermark.height / watermark.width
    new_height = int(new_width * aspect_ratio)
    
    # 4. 调整水印大小（使用高质量的重采样算法）
    watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
    
    # 5. 调整水印透明度
    if opacity < 1.0:
        alpha = watermark.getchannel("A")
        alpha = alpha.point(lambda p: p * opacity)
        watermark.putalpha(alpha)
    
    # 6. 创建透明图层放置水印
    watermark_layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
    watermark_layer.paste(watermark, position, watermark)
    
    # 7. 合并图片
    combined = Image.alpha_composite(background, watermark_layer)
    combined.convert("RGB").save(output_path)
    print(f"水印添加完成！图片已保存至: {output_path}")
    print(f"水印尺寸: {watermark.size} (缩放比例: {scale} = 1/{int(1/scale)})")
    print(f"水印位置: ({position[0]}, {position[1]}) - 左上角")




def merge_images_vertically(image_path1, image_path2, output_path):
    """
    将两张图片等比缩放至相同宽度后上下拼接
    
    参数:
    image_path1 -- 上方图片路径
    image_path2 -- 下方图片路径
    output_path -- 保存路径
    """
    # 打开两张图片
    img1 = Image.open(image_path1)
    img2 = Image.open(image_path2)
    
    # 选择最大宽度作为目标宽度
    target_width = max(img1.width, img2.width)
    
    # 计算等比缩放后的高度
    img1_ratio = img1.height / img1.width
    img2_ratio = img2.height / img2.width
    
    img1_height = int(target_width * img1_ratio)
    img2_height = int(target_width * img2_ratio)
    
    # 应用相同的目标宽度进行等比缩放
    img1_resized = img1.resize((target_width, img1_height), Image.Resampling.LANCZOS)
    img2_resized = img2.resize((target_width, img2_height), Image.Resampling.LANCZOS)
    
    # 创建新画布（宽度相同，高度为两图之和）
    merged_height = img1_height + img2_height
    merged = Image.new('RGB', (target_width, merged_height), (255, 255, 255))
    
    # 拼接图片
    merged.paste(img1_resized, (0, 0))
    merged.paste(img2_resized, (0, img1_height))
    
    # 保存结果
    merged.save(output_path)








def fetch_page(url: str, output_file: str = HTML_FILE) -> bool:
    """
    抓取网页并保存为HTML文件
    
    Args:
        url: 要抓取的URL
        output_file: 输出文件路径
        
    Returns:
        True表示成功，False表示失败
    """
    headers = {'User-Agent': USER_AGENT}
    try:
        if "codecin" in url:
            cookie = cookies_宋杰
        else:
            cookie = cookies_测试
        response = requests.get(url, headers=headers, timeout=15, cookies=cookie)
        
        response.raise_for_status()
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"✅ 网页已保存至: {output_file}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except IOError as e:
        print(f"❌ 文件写入错误: {e}")
        return False

def parse_submission_row(row, row_index: int) -> Optional[Submission]:
    """
    解析单行提交记录
    
    Args:
        row: BeautifulSoup表格行对象
        row_index: 行索引(用于错误报告)
        
    Returns:
        结构化提交记录或None(解析失败时)
    """
    try:
        # 提取记录ID
        record_id = row.get('data-rid', '').strip()
        if not record_id:
            print(f"⚠️ 第{row_index+1}行缺少record_id，跳过该行")
            return None
        
        # 状态信息
        status_div = row.find('td', class_='col--status')
        status_text = ' '.join(status_div.get_text(strip=True).split()) if status_div else ""
        
        # 题目信息
        problem_td = row.find('td', class_='col--problem')
        problem_link = problem_td.find('a') if problem_td else None
        
        problem_code, problem_name, problem_url = "", "", ""
        if problem_link:
            b_tag = problem_link.find('b')
            problem_code = b_tag.text.strip() if b_tag else ""
            problem_name = problem_link.text.replace(problem_code, '', 1).strip()
            problem_url = f"{BASE_URL}{problem_link['href']}" if problem_link.get('href') else ""
        else:
            problem_name = problem_td.get_text(strip=True) if problem_td else ""
        
        # 递交者信息
        submitter_td = row.find('td', class_='col--submit-by')
        submitter_link = submitter_td.find('a') if submitter_td else None
        submitter_name = submitter_link.text.strip() if submitter_link else ""
        submitter_id = submitter_link['href'].split('/')[-1] if submitter_link and 'href' in submitter_link.attrs else ""
        
        # 提取性能信息
        time = safe_extract_text(row, 'col--time')
        memory = safe_extract_text(row, 'col--memory')
        language = safe_extract_text(row, 'col--lang')
        
        # 递交时间
        submit_time_span = row.find('td', class_='col--submit-at')
        submit_time_span = submit_time_span.find('span') if submit_time_span else None
        submit_time = re.sub(r'\s+', ' ', submit_time_span.text.strip()) if submit_time_span else ""
        
        # 学校信息
        school = safe_extract_text(row, 'col--school')
        
        # 结果链接
        result_url = f"{BASE_URL}/record/{record_id}"
        
        # 创建结构化对象
        return Submission(
            record_id=record_id,
            status=status_text,
            problem_code=problem_code,
            problem_name=problem_name,
            problem_url=problem_url,
            submitter_name=submitter_name,
            submitter_id=submitter_id,
            time=time,
            memory=memory,
            language=language,
            submit_time=submit_time,
            school=school,
            result_url=result_url
        )
        
    except Exception as e:
        print(f"❌ 解析第{row_index+1}行时出错: {e}")
        return None

def safe_extract_text(row, class_name: str) -> str:
    """安全提取文本内容"""
    element = row.find('td', class_=class_name)
    return element.text.strip() if element else ""

def parse_submissions(input_file: str = HTML_FILE) -> List[Submission]:
    """
    从HTML文件中解析提交记录
    
    Args:
        input_file: HTML文件路径
        
    Returns:
        提交记录列表
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        submissions = []
        
        submission_table = soup.find('table', class_='record_main__table')
        if not submission_table:
            print("⚠️ 未找到提交记录表格")
            return submissions
        
        tbody = submission_table.find('tbody')
        if not tbody:
            print("⚠️ 表格中未找到tbody部分")
            return submissions
        
        rows = tbody.find_all('tr')
        if not rows:
            print("ℹ️ 表格中没有数据行")
            return submissions
        
        for i, row in enumerate(rows):
            submission = parse_submission_row(row, i)
            if submission:
                submissions.append(submission)
        
        print(f"✅ 成功解析 {len(submissions)} 条提交记录")
        return submissions
        
    except Exception as e:
        print(f"❌ 解析HTML时发生错误: {e}")
        return []

def setup_database() -> bool:
    """
    初始化数据库
    
    Returns:
        True表示成功，False表示失败
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # 创建提交记录表（如果不存在）
        c.execute('''CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    status TEXT,
                    problem_code TEXT,
                    problem_name TEXT,
                    problem_url TEXT,
                    submitter_name TEXT,
                    submitter_id TEXT,
                    time TEXT,
                    memory TEXT,
                    language TEXT,
                    submit_time TEXT,
                    school TEXT,
                    result_url TEXT
                )''')
        
        conn.commit()
        conn.close()
        print(f"✅ 数据库已准备就绪: {DB_FILE}")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def save_to_database(submissions: List[Submission]) -> int:
    """
    保存提交记录到数据库
    
    Args:
        submissions: 提交记录列表
        
    Returns:
        成功保存的记录数
    """
    if not submissions:
        return 0
        
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        saved_count = 0
        for sub in submissions:
            try:
                c.execute('''INSERT OR IGNORE INTO submissions (
                            record_id, status, problem_code, problem_name, problem_url,
                            submitter_name, submitter_id, time, memory, language,
                            submit_time, school, result_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        tuple(sub))
                saved_count += 1
            except sqlite3.IntegrityError:
                # 忽略重复记录
                pass
            except Exception as e:
                print(f"⚠️ 保存记录 {sub.record_id} 时出错: {e}")
        
        conn.commit()
        print(f"✅ 成功保存 {saved_count} 条记录到数据库")
        return saved_count
        
    except Exception as e:
        print(f"❌ 数据库保存失败: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def process_page(url) -> int:
    """
    处理单个页面
    
    Args:
        url: 页面URL

    Returns:
        处理成功的记录数
    """
    
    if not fetch_page(url):
        return 0
    
    submissions = parse_submissions()
    if not submissions:
        return 0
    
    return save_to_database(submissions)

def estimate_remaining_time(start_time, processed, total):
    """估算剩余时间"""
    if processed == 0:
        return "未知"
    
    elapsed = time.time() - start_time
    time_per_item = elapsed / processed
    remaining = (total - processed) * time_per_item
    
    if remaining > 3600:
        return f"{remaining/3600:.1f}小时"
    elif remaining > 60:
        return f"{remaining/60:.1f}分钟"
    return f"{remaining:.0f}秒"

def get_total_datas():
    """主程序逻辑"""
    if not setup_database():
        return
    
    print("\n🚀 开始抓取提交记录...")
    total_users = MAX_USERS
    start_time = time.time()
    processed_users = 0

    if SEARCH_PAGE:
        page = 1
        while True and page <= MAX_PAGE:
            url = f"{BASE_URL}/record?page={page}"
            print(f"\n{'='*50}")
            print(f"📑 第 {page} 页 | 🌐 {url}")
            print(f"{'='*50}")

            saved_count = process_page(url)
            if saved_count == 0:
                break
            page += 1
            # exit()
            # 添加短暂延迟，避免请求过于频繁
            time.sleep(0.5)
    
    if SEARCH_USER :
        for user_id in range(total_users):
            page = 1
            user_records = 0
            
            # 处理当前用户的所有页面
            while True:
                url = f"{BASE_URL}/record?uidOrName={user_id}&page={page}"
                print(f"\n{'='*50}")
                print(f"👤 用户 {user_id} | 📑 第 {page} 页 | 🌐 {url}")
                print(f"{'='*50}")

                saved_count = process_page(url)
                if saved_count == 0:
                    break
                user_records += saved_count
                page += 1
                # 添加短暂延迟，避免请求过于频繁
                # time.sleep(0.5)
            
            processed_users += 1
            
            # 进度报告
            if user_id % 10 == 0 or user_id == total_users - 1:
                elapsed = time.time() - start_time
                remaining_time = estimate_remaining_time(
                    start_time, processed_users, total_users
                )
                print(f"\n📊 进度: {processed_users}/{total_users} 用户 ({processed_users/total_users*100:.1f}%)")
                print(f"⏱️ 用时: {elapsed:.1f}秒 | 剩余: {remaining_time}")
    
    print("\n🎉 所有操作已完成！")
    print(f"📂 数据库位置: {DB_FILE}")


def o1ne_get_codecin_data_output():

    print("开始抓取提交记录...")

    start_time = time.time()
    MAX_USERS = MAX_121_43_66_70
    BASE_URL = "http://121.43.66.70"
    get_total_datas()
    MAX_USERS = MAX_codecin
    BASE_URL = "https://codecin.com"
    get_total_datas()
    
    end_time = time.time()

    print(f"✅ 抓取完成，耗时: {end_time - start_time:.2f}秒")

    time.sleep(1)


def t2wo_remove_struct_name():

    print("开始删除无意义的提交记录...")
    
    start_time = time.time()

    # 连接到你的SQLite数据库（替换为你的数据库路径）
    db_path = 'submissions_get.db'  # 修改为实际的数据库文件路径

    # 复制数据库文件
    if os.path.exists('submissions.db'):  # 检查数据库文件是否存在
        os.remove('submissions.db')
    shutil.copyfile(db_path, 'submissions.db')

    db_path = 'submissions.db'

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行更新操作
        cursor.execute(
            "UPDATE submissions SET submitter_name = ? WHERE submitter_name = ?",
            ('李泰然', '李泰然2014')
        )
        update_count = cursor.rowcount
        
        # 执行删除操作：删除problem_name为*的记录
        cursor.execute(
            "DELETE FROM submissions WHERE problem_name = '*'"
        )
        delete_count = cursor.rowcount
        
        # 提交事务
        conn.commit()

        print(f"成功更新 {update_count} 条记录")
        print(f"成功删除 {delete_count} 条记录")
        
    except sqlite3.Error as e:
        print("数据库操作出错:", e)
        conn.rollback()
        
    finally:
        # 关闭连接
        if conn:
            conn.close()

    end_time = time.time()
    print(f"✅ 删除完成，耗时: {end_time - start_time:.2f}秒")

    time.sleep(1)


def t3hree_count_user_result():

    print("开始生成报告...")

    start_time = time.time()

    #user_names = ["胡斯桐", "邱子墨", "周淼", "周堃禾"]
    user_names = ["衣邢桉苒", "章新胜", "高云铮", "王子墨", "咸景熙", "李泰然", "刘卓奕", "殷梓骞", "邱子墨"]
    generate_submission_report(names=user_names)

    end_time = time.time()
    print(f"✅ 生成完成，耗时: {end_time - start_time:.2f}秒")

    time.sleep(1)




def t4four_count_ok_question_num():

    print("开始生成报告...")

    start_time = time.time()

    
    # 数据库文件路径
    DB_PATH = 'submissions.db'  # 替换为你的数据库路径
    JSON_FILE = 'statistics.json'  # 输出JSON文件名

    # 目标姓名列表
    target_names = ["衣邢桉苒", "章新胜", "高云铮", "王子墨", "咸景熙", 
                "李泰然", "刘卓奕", "徐先蓬", "殷梓骞", "邱子墨"]

    # target_names = ["胡斯桐", "邱子墨", "周淼", "周堃禾"]
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 为每个姓名单独查询并统计
    result_list = []

    for name in target_names:
        # 为每个姓名单独构建查询
        query = """
        SELECT COUNT(DISTINCT problem_code)
        FROM submissions 
        WHERE submitter_name = ?
        AND status LIKE '%Accepted%'
        """
        #   AND language = "Python 3" 
        
        # 执行查询
        cursor.execute(query, (name,))
        count = cursor.fetchone()[0]  # 获取计数结果

        print(f"{name} 的完成题目数量为：{count}")
        
        # 添加到结果列表
        result_list.append({
            "name": name,
            "num": count
        })

    # 关闭数据库连接
    conn.close()

    # 构建输出数据结构
    output = {"datas": result_list}

    # 保存到JSON文件
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"统计完成，结果已保存至 {JSON_FILE}")

    end_time = time.time()
    print(f"✅ 统计完成，耗时: {end_time - start_time:.2f}秒")

    time.sleep(1)



def f5ive_make_user_png():

    print("开始生成用户折线图报告...")

    start_time = time.time()


    # 从JSON文件加载数据
    json_filename = "submission_report.json"  # 替换为你的JSON文件名
    data = load_data_from_json(json_filename)
    
    # 打印文件路径确认
    print(f"从文件 '{json_filename}' 加载数据...")
    
    # 检查数据是否加载成功
    if data:
        print(f"成功加载数据: {len(data['datas'])} 个人的数据")
        print(f"时间范围: {data['times'][0]} 至 {data['times'][-1]}")
        
        # 绘制折线图
        plot_line_chart(data)
        print("图表已生成并保存为 'static/user.png'")
    else:
        print("数据加载失败，请检查文件路径和内容")

    
    end_time = time.time()
    print(f"✅ 统计完成，耗时: {end_time - start_time:.2f}秒")

    time.sleep(1)



def s6ix_make_question_png():

    print("开始生成正确题目图报告...")
    start_time = time.time()

    
    # 从文件读取JSON数据
    with open('statistics.json', 'r', encoding='utf-8') as f:
        json_data = f.read()

    # 解析 JSON 数据
    data = json.loads(json_data)
    datas = data['datas']

    # 按数量从小到大排序
    datas_sorted = sorted(datas, key=lambda x: x['num'])

    # 提取排序后的姓名和数量
    names = [item['name'] for item in datas_sorted]
    values = [item['num'] for item in datas_sorted]

    # 设置图形大小和DPI
    plt.figure(figsize=(10, 6), dpi=100)
    # 设置中文字体（解决中文乱码问题）
    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 创建条形图（按升序排列）
    bars = plt.bar(names, values, color=['#4C72B0', '#55A868', '#DD8452'])

    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 垂直偏移
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10)

    # 添加标题和标签
    plt.title('未来引擎 学员已通过题目数量', fontsize=14, pad=20)
    plt.xlabel('姓名', fontsize=12)
    plt.ylabel('已通过的题目数量', fontsize=12)

    # 设置网格线
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 添加背景色
    plt.gca().set_facecolor('#F5F5F5')

    # 旋转X轴标签防止重叠（特别是当名字较长时）
    plt.xticks(rotation=20)

    # 调整边距
    plt.tight_layout()

    # 保存图表
    plt.savefig('static/question.png', dpi=150)

    # 显示图形
    # plt.show()

    print("✅ 状态图表已保存为 static/question.png")

    end_time = time.time()
    print(f"✅ 统计完成，耗时: {end_time - start_time:.2f}秒")

    time.sleep(1)
    



def s7even_add_watermark():

    print("开始添加水印...")

    start_time = time.time()

    # 主图片路径（背景）
    background_image = "static/user.png"
    # 水印图片路径
    watermark_image = "static/logo.png"
    # 输出图片路径
    output_image = "static/user.png"
    
    # 在左上角添加去除白底的水印，宽度为背景宽度的1/5
    add_scaled_watermark(
        background_image, 
        watermark_image, 
        output_image,
        position=(0, 0),  # 左上角位置
        opacity=0.7,       # 70%透明度
        tolerance=15,      # 颜色容差
        scale=0.2          # 水印宽度=背景宽度×0.2 (即1/5)
    )
    
    # 主图片路径（背景）
    background_image = "static/question.png"
    # 输出图片路径
    output_image = "static/question.png"
    # 在左上角添加去除白底的水印，宽度为背景宽度的1/5
    add_scaled_watermark(
        background_image, 
        watermark_image, 
        output_image,
        position=(0, 0),  # 左上角位置
        opacity=0.7,       # 70%透明度
        tolerance=15,      # 颜色容差
        scale=0.2          # 水印宽度=背景宽度×0.2 (即1/5)
    )


    end_time = time.time()
    print(f"✅ 添加水印完成，耗时: {end_time - start_time:.2f}秒")
    time.sleep(1)
        


def e8ight_stick_png():

    print("开始合并图片...")

    start_time = time.time()


    # 使用示例
    merge_images_vertically("static/user.png", "static/question.png", "static/report.png")

    end_time = time.time()
    print(f"✅ 合并图片完成，耗时: {end_time - start_time:.2f}秒")
    time.sleep(1)






def main():
    

    o1ne_get_codecin_data_output()

    t2wo_remove_struct_name()

    t3hree_count_user_result()

    t4four_count_ok_question_num()

    f5ive_make_user_png()

    s6ix_make_question_png()

    s7even_add_watermark()

    e8ight_stick_png()

    

    # 删除临时文件
    os.remove("page.html")
    os.remove("statistics.json")
    os.remove("submission_report.json")
    os.remove("submissions.db")
    os.remove("transparent_temp.png")

if __name__ == "__main__":
    last_day = time.localtime().tm_mday


    while True:

        # 获取当前分钟
        day = time.localtime().tm_mday
        month = time.localtime().tm_mon
        year = time.localtime().tm_year
        hour = time.localtime().tm_hour
        minute = time.localtime().tm_min
        print(f"[检查时间] 当前时间: {year}/{month}/{day} {hour}:{minute}")


        if day != last_day:

            SEARCH_USER = True
            SEARCH_PAGE = False

            print(f"[检查日期] 当前日期: {year}/{month}/{day}")
            
            print("开始生成报告...")
            s = time.time()

            main()

            print(f"✅ 报告生成完成，耗时: {time.time() - s:.2f}秒")

            last_day = day
            SEARCH_PAGE = True
            SEARCH_USER = False

        elif hour % 5 == 0:

            MAX_PAGE = 20

            print(f"[检查小时数] 当前小时: {hour}")

            print("开始生成报告...")

            s = time.time()

            main()

            print(f"✅ 报告生成完成，耗时: {time.time() - s:.2f}秒")

            MAX_PAGE = 1



        elif minute % 5 == 0:

            print(f"[检查分钟数] 当前分钟: {minute}")
            print("开始生成报告...")
            s = time.time()

            main()

            print(f"✅ 报告生成完成，耗时: {time.time() - s:.2f}秒")


        else:
            print(f"[跳过] 当前分钟 {minute} 不满足条件")
            time.sleep(60)

        