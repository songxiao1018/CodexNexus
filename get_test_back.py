# 导入所需库
import requests  # 用于发送HTTP请求
import json      # 用于JSON数据处理（虽然未实际使用，但保留以防未来扩展）
import bs4       # 用于解析HTML文档
import time      # 用于时间控制

def submit_code(data, cookies=None):
    """
    提交代码到在线判题系统并获取判题结果
    
    参数:
    data (dict): 包含提交数据的字典（语言、代码、输入等）
    cookies (dict): 可选，用户认证的cookies
    
    返回:
    str: 判题结果消息文本
    """
    # 服务器基础URL
    base_url = "http://121.43.66.70"
    
    # 优先使用传入的 cookies
    if cookies:
        cookies = cookies
    else:
        # 尝试从 Flask session 获取 cookie
        try:
            from flask import session
            codecin_cookies = session.get('codecin_cookies')
            
            if codecin_cookies:
                cookies = codecin_cookies
            else:
                # 默认 cookie（如果未登录）
                cookies = {
                    "sid": "GFZCe8qM3SMO8340uGoEBL6CzNCK1aKF",
                    "sid.sig": "xzh2ln9ks8eg8RqBm2SV2QKssFE"
                }
        except ImportError:
            # 在非Flask环境中使用默认cookie
            cookies = {
                "sid": "GFZCe8qM3SMO8340uGoEBL6CzNCK1aKF",
                "sid.sig": "xzh2ln9ks8eg8RqBm2SV2QKssFE"
            }

    # 1. 提交代码到判题系统
    post_url = "/p/1/submit"
    # 发送POST请求提交代码
    response = requests.post(base_url + post_url, data=data, cookies=cookies)
    
    # 解析提交响应获取结果页面URL
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    # 从canonical链接提取判题结果页的路径
    href = soup.find("link", rel="canonical")["href"]

    # print(href)

    # 2. 等待判题完成
    # print("="*50)
    # print("等待2秒...")
    time.sleep(2)  # 暂停2秒确保服务器完成判题
    # print("="*50)

    # 3. 获取判题结果
    # 请求判题结果页面
    response = requests.get(base_url + href, cookies=cookies)

    with open("test.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    # 解析结果页面HTML
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    try:
        # 查找包含判题结果的消息元素
        message = soup.find("span", class_="message")
        msg = message.text
    except:
        # pre class="compiler-text"
        message = soup.find("pre", class_="compiler-text")
        msg = message.text
    
    return msg  # 返回判题结果文本

if __name__ == "__main__":
    # 测试用例数据
    data = {
        "lang": "cc.cc20o2",  # 使用的编程语言
        "code": """#include<iostream>
using namespace std;
int main(){
    long n,a,b;
    cin>>n;
    a = n / 4;
    b = n % 4
    cout<<a<<endl;
    cout<<b;
    return 0;
}""",  # 提交的代码
        "input": "5",        # 测试输入
        "pretest": True       # 是否为预测试
    }

    # 用户认证cookies
    cookie = {
        "sid": "GFZCe8qM3SMO8340uGoEBL6CzNCK1aKF",
        "sid.sig": "xzh2ln9ks8eg8RqBm2SV2QKssFE"
    }   

    # 执行代码提交并获取结果
    t = submit_code(data, cookie)
    print(t)  # 打印判题结果