import time
import collections
import sqlite3
import os
import json
import requests
from datetime import datetime
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from language_replace import *


def normalize_words(words):
    """标准化分词结果，合并同义词并过滤停用词"""
    normalized = []
    for word in words:
        # 跳过停用词
        if word in STOPWORDS:
            continue
        # 合并同义词
        for key, synonyms in SYNONYMS.items():
            if word in synonyms:
                normalized.append(key)
                break
        else:
            normalized.append(word)
    return normalized


def is_valid_question(text):
    """验证问题有效性（增加标准化处理）"""
    # 分词处理
    words = list(jieba.cut(text))
    normalized_words = normalize_words(words)
    
    # 检查有效词汇量
    if len(normalized_words) < 3:
        return False
    
    # 检查有效字符数（过滤纯表情等无效内容）
    clean_text = ''.join(filter(str.isalnum, text))
    if len(clean_text) < 10:
        return False
        
    return True

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
            ai_response TEXT NOT NULL,
            message_hash TEXT NOT NULL UNIQUE  -- 添加唯一哈希字段
        )
    ''')
    # 创建倒序索引加速查询
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_hash ON chat_messages(message_hash)')
    conn.commit()
    conn.close()

def get_text_hash(text):
    """生成标准化文本哈希"""
    import hashlib
    
    # 分词并标准化处理
    words = list(jieba.cut(text))
    normalized_words = normalize_words(words)
    
    # 去重后排序（消除语序影响）
    unique_words = sorted(set(normalized_words))
    
    # 生成标准化字符串
    normalized_str = " ".join(unique_words)
    
    # 返回MD5哈希
    return hashlib.md5(normalized_str.encode()).hexdigest()

def calculate_similarity(text1, text2):
    """计算文本相似度（优化向量化）"""
    try:
        vectorizer = TfidfVectorizer(tokenizer=jieba.cut, stop_words='english')
        tfidf = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    except:
        return 0.0  # 异常情况返回0相似度

def find_similar_question(new_question, threshold=0.8):
    """查找相似问题（优化查询逻辑）"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    # 生成标准化哈希
    new_hash = get_text_hash(new_question)
    
    # 直接精确匹配
    cursor.execute('SELECT user_message, ai_response FROM chat_messages WHERE message_hash = ?', (new_hash,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return (True, result, 1.0)  # 完全匹配
    return (False, None, 0.0)



# 消息存储函数
def save_message(user_message, ai_response):
    """添加新问题记录"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO chat_messages (timestamp, user_message, ai_response, message_hash)
            VALUES (?, ?, ?, ?)
        ''', (
            time.time(),
            user_message,
            ai_response,
            get_text_hash(user_message)
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        # 处理重复哈希的情况（理论上概率极低）
        pass
    finally:
        conn.close()

def ai_chat(message):
    url = "https://api.siliconflow.cn/v1/chat/completions"

    content = """
    你现在是一名编程大师，你需要回答我关于编程的问题，请使用中文回答，内容简洁明了。
    不要直接给我结果，告诉我思维的方法。
    请以正常文章的形式回答，不要使用markdown语法格式。
    禁止直接回答代码。"""

    content = content.replace("\n", "").replace(" ", "")

    payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": content
            },
            {# user, assistant, system
                "role": "user",
                "content": message
            }
        ]
    }
    headers = {
        "Authorization": "Bearer sk-xxxxxxxxxxxxxxxxxxx", # 请填写API-KEY
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    message_back = response.text


    json_data = json.loads(message_back)
    data = json_data["choices"][0]["message"]["content"]

    return data

def get_ai_response(message):

    global request_history
    
    current_time = time.time()

        # 先检查缓存
    is_similar, match, similarity = find_similar_question(message)
    
    if is_similar:
        print(f"找到相似问题（相似度{similarity:.2f}），直接返回缓存结果")
        return "使用已有的ai回答\n\n" + match[1]  # 返回已有回答

    
    if len(message) < 5 or not is_valid_question(message):
        return "请发送有效消息"
    
    return message[::-1]  # 防止恶意脚本消耗余量，实际工作请删除
    
    # 清理60分钟前的旧请求 (3600秒 = 60分钟)
    while request_history and current_time - request_history[0] > 3000:
        request_history.popleft()
    
    # 检查当前请求数量
    if len(request_history) >= 100:
        # 计算最近一次请求的剩余生存时间
        oldest_time = request_history[0]
        remaining_time = int(60 - (current_time - oldest_time) / 60)
        return f"当前请求次数已达上限，请{remaining_time}分钟后再试"
    
    # 记录本次请求时间
    request_history.append(current_time)

    data = ai_chat(message)
    
    # 保存到数据库
    save_message(message, data)
    
    return data




# 初始化数据库
init_db()

# 请求频率控制
# 使用双端队列存储请求时间戳，最大长度100
request_history = collections.deque(maxlen=100)