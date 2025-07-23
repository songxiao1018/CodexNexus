import requests
from flask import Flask, render_template, jsonify, request, session  # Web框架及组件


def login_to_codecin(username, password):
    """处理 CodeCin 登录请求"""
    try:
        # 1. 发送登录请求到 CodeCin
        login_url = "http://121.43.66.70/login"  # 替换为实际的登录URL


        response = requests.post(
            login_url,
            data={'username': username, 'password': password},
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
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"登录 CodeCin 出错: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'登录请求失败: {str(e)}'
        })
