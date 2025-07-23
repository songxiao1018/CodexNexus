import markdown
import html
import re
import base64
import json
import hashlib
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from markdown.extensions.toc import TocExtension

def mdToHtml(markdown_text):
    """
    将Markdown文本转换为HTML，特别处理代码块以支持交互式编辑和测试
    
    参数:
    markdown_text: str - 原始Markdown格式文本
    
    返回:
    str - 转换后的HTML字符串
    """
    # 计数器用于生成唯一标识
    question_counter = 0
    
    # 内部函数：处理Markdown中的代码块
    def process_code_blocks(match):
        """
        处理正则匹配到的代码块，生成交互式代码编辑组件
        
        参数:
        match: re.Match - 正则表达式匹配对象
        
        返回:
        str - 生成的HTML代码片段
        """
        nonlocal question_counter

        # 提取代码语言并转为小写 (group1)
        lang = match.group(1).lower()
        # 提取代码内容 (group2)
        code_content = match.group(2)
        
        # 仅处理特定语言的代码块
        if lang == 'select':
            # 处理客观题模式
            try:
                question_data = json.loads(code_content)
                # 生成唯一标识符
                question_counter += 1
                unique_id = f"q_{hashlib.md5(str(question_counter).encode()).hexdigest()[:6]}"
                
                title = question_data.get('title', '题目')
                question_text = question_data.get('question', '')
                options = question_data.get('options', [])
                answer = question_data.get('answer', '')
                select_type = question_data.get('select', 'single')
                
                # 构建客观题HTML结构
                html_output = f'<div class="question-container" data-answer="{html.escape(answer)}" data-type="{select_type}" id="container_{unique_id}">'
                html_output += f'<h3>{html.escape(title)}</h3>'
                html_output += f'<p>{html.escape(question_text)}</p>'
                
                # 添加选项
                option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
                html_output += '<div class="options">'
                
                for i, option in enumerate(options):
                    letter = option_letters[i] if i < len(option_letters) else str(i+1)

                    # 修改这里：为多选类型添加不同的名称处理
                    input_type = 'checkbox' if select_type == 'multi' else 'radio'
                    input_name = f"question_options_{unique_id}_{i}" if select_type == 'multi' else f"question_options_{unique_id}"
                    
                    html_output += f'''
                    <div class="option">
                        <input type="{input_type}" 
                            id="option_{unique_id}_{letter}" 
                            name="{input_name}" 
                            value="{letter}">
                        <label for="option_{unique_id}_{letter}">
                            <span class="option-letter">{letter}.</span>
                            {html.escape(option)}
                        </label>
                    </div>
                    '''
                
                html_output += '</div>'  # 关闭options div
                
                # 添加提交按钮和结果区域
                html_output += f'''
                <div class="question-controls">
                    <button class="submit-question" data-target="{unique_id}">提交答案</button>
                    <div class="question-result" id="result_{unique_id}"></div>
                </div>
                '''
                
                html_output += '</div>'  # 关闭question-container div
                
                return html_output
                
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回原始代码块
                return match.group(0)
        
        elif lang in ['c++', 'python']:
            # Base64编码原始代码（防止HTML注入和保留特殊字符）
            encoded_code = base64.b64encode(code_content.encode('utf-8')).decode('utf-8')
            
            # 构建交互式代码组件HTML结构
            return f'''<div class="code-container">
    <!-- 语言标签和编辑区域 -->
    <label>代码编辑 (<code class="lang-tag">{lang}</code>):</label>
    <textarea class="code-input" data-lang="{lang}" data-original="{encoded_code}">
        {html.escape(code_content)}
    </textarea>
    
    <!-- 测试区域 -->
    <div class="code-test-section">
        <div class="test-row">
            <!-- 测试输入区 -->
            <div class="test-group">
                <label>测试数据输入:</label>
                <textarea class="test-input" placeholder="输入测试数据..."></textarea>
            </div>
            <!-- 输出显示区 -->
            <div class="test-group">
                <label>代码输出:</label>
                <textarea class="test-output" placeholder="输出将显示在这里..." readonly></textarea>
            </div>
        </div>
        <!-- 操作按钮 -->
        <div class="code-controls">
            <button class="reset-code">恢复原始代码</button>
            <button class="submit-code">提交测试</button>
        </div>
    </div>
</div>'''
        
        # 其他语言返回原始内容
        return match.group(0)

    # 处理代码块：使用正则替换特殊格式的代码块
    processed_text = re.sub(
        r'```(c\+\+|python|select)\n([\s\S]*?)\n```',  # 匹配c++/python/select代码块
        process_code_blocks,                           # 替换处理器
        markdown_text,                                 # 原始文本
        flags=re.IGNORECASE                            # 忽略大小写
    )
    
    # 转换剩余Markdown内容为标准HTML
    html_output = markdown.markdown(
        processed_text,
        extensions=[
            ExtraExtension(),       # 支持表格/缩写等扩展语法
            CodeHiliteExtension(),  # 添加代码高亮功能
            TocExtension()           # 生成目录导航
        ]
    )
    
    return html_output