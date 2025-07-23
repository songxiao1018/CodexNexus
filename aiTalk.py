from question_post import get_response
import time
import collections
import sqlite3
from datetime import datetime

# 数据库初始化
def init_db():
    """初始化SQLite数据库，创建消息记录表"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# 消息存储函数
def save_message(user_message, ai_response):
    """将聊天记录保存到数据库"""
    timestamp = time.time()
    try:
        conn = sqlite3.connect('chat_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_messages (timestamp, user_message, ai_response)
            VALUES (?, ?, ?)
        ''', (timestamp, user_message, ai_response))
        conn.commit()
    except sqlite3.Error as e:
        print(f"数据库保存失败: {e}")
    finally:
        conn.close()

def get_ai_response(message):
    """获取AI对用户消息的响应（每小时限60次）
    
    参数:
    message (str): 用户输入的消息文本
    
    返回:
    str: AI生成的回复文本或限流提示
    """
    global request_history
    
    current_time = time.time()

    # print("当前已存在请求：")
    # print(request_history)
    # print("当前时间：")
    # print(current_time)
    # print("当前消息：")
    # print(message)
    
    # 清理60分钟前的旧请求 (3600秒 = 60分钟)
    while request_history and current_time - request_history[0] > 4000:
        request_history.popleft()
    
    # 检查当前请求数量
    if len(request_history) >= 5:
        # 计算最近一次请求的剩余生存时间
        oldest_time = request_history[0]
        remaining_time = int(60 - (current_time - oldest_time) / 60)
        return f"当前请求次数已达上限，请{remaining_time}分钟后再试"
    
    # 记录本次请求时间
    request_history.append(current_time)
    
    # 调用AI接口获取响应
    response = get_response(message)

    if "注册" in response:
        # 计算最近一次请求的剩余生存时间
        oldest_time = request_history[0]
        remaining_time = int(60 - (current_time - oldest_time) / 60)
        return f"当前请求次数已达上限，请{remaining_time}分钟后再试"

    # print(f"用户输入：{message}")
    # print(f"AI回复：{response}")
    
    # 保存到数据库
    save_message(message, response)
    
    return response




# 初始化数据库
init_db()

# 请求频率控制
# 使用双端队列存储请求时间戳，最大长度60
request_history = collections.deque(maxlen=60)