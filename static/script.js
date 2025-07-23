/**
 * 加载文章内容并渲染到页面
 * @param {string} title - 要加载的文章标题
 */
function loadArticle(title) {
    // 发起API请求获取文章数据
    fetch(`/article/${title}`)
        .then(response => response.json())
        .then(data => {
            // 错误处理
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // 更新文章标题和内容区域
            document.getElementById('articleTitle').textContent = data.title;
            document.getElementById('articleContent').innerHTML = `
                <h2 id="articleTitle">${data.title}</h2>
                <div class="article-body">${data.content}</div>
            `;
            
            // 初始化新加载代码区域的自适应高度
            setTimeout(() => {
                const newCodeInputs = document.querySelectorAll('.code-input');
                newCodeInputs.forEach(input => {
                    autoResizeTextarea(input);
                });
            }, 100);
        })
        .catch(error => console.error('Error:', error));
}

/**
 * 发送用户消息到聊天服务器并显示响应
 */
function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    // 空消息校验
    if (!message) return;
    
    // 在聊天框显示用户消息
    addMessage(message, 'user');
    userInput.value = '';
    
    // 发送消息到后端聊天接口
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // 显示机器人回复
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('聊天服务暂时不可用，请稍后再试', 'bot');
    });
}

/**
 * 处理聊天输入框的键盘事件
 * @param {KeyboardEvent} event - 键盘事件对象
 */
function handleKeyPress(event) {
    // 按Enter键发送消息
    if (event.key === 'Enter') {
        sendMessage();
    }
}

/**
 * 在聊天框添加新消息
 * @param {string} content - 消息内容
 * @param {string} sender - 发送者类型 ('user' 或 'bot')
 */
function addMessage(content, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    // 创建消息内容容器
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // 自动滚动到最新消息
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 全局点击事件监听（处理代码操作）
document.addEventListener('click', function(e) {
    // 代码提交按钮处理
    if (e.target && e.target.classList.contains('submit-code')) {
        const button = e.target;
        const container = button.closest('.code-container');
        const codeInput = container.querySelector('.code-input');
        const testInput = container.querySelector('.test-input');
        const testOutput = container.querySelector('.test-output');
        
        // 获取编程语言、代码和测试输入
        const lang = codeInput.getAttribute('data-lang');
        const code = codeInput.value;
        const inputData = testInput.value.trim();

        testOutput.value = '已提交请等待...';
        
        // 提交代码到服务器执行
        fetch('/submit_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lang: lang,
                code: code,
                input: inputData
            })
        })
        .then(response => response.json())
        .then(data => {
            testOutput.value = data.output;
        })
        .catch(error => {
            testOutput.value = '提交出错: ' + error.message;
        });
    }
    
    // 代码重置按钮处理
    if (e.target && e.target.classList.contains('reset-code')) {
        const button = e.target;
        const container = button.closest('.code-container');
        const codeInput = container.querySelector('.code-input');
        const encodedOriginal = codeInput.getAttribute('data-original');
        
        // 解码并恢复原始代码
        try {
            const originalCode = atob(encodedOriginal);
            codeInput.value = originalCode;
            
            // 重置后调整文本区域高度
            setTimeout(() => {
                codeInput.style.height = 'auto';
                codeInput.style.height = (codeInput.scrollHeight) + 'px';
            }, 10);
        } catch (error) {
            console.error('恢复原始代码失败:', error);
        }
    }

    // 在现有的document.addEventListener('click', ...)函数中
    if (e.target && e.target.classList.contains('submit-question')) {
        const button = e.target;
        const unique_id = button.getAttribute('data-target');
        const container = document.getElementById(`container_${unique_id}`);
        const resultDiv = document.getElementById(`result_${unique_id}`);
        
        // 获取正确答案和题目类型
        const correctAnswer = container.getAttribute('data-answer').toUpperCase();
        const questionType = container.getAttribute('data-type');
        
        // 获取用户选择的答案
        let userAnswer = '';
        
        if (questionType === 'single' || questionType === 'judge') {
            // 单选题或判断题 - 查找单选项
            const selected = container.querySelector(`input[name="question_options_${unique_id}"]:checked`);
            if (selected) {
                userAnswer = selected.value;
            }
        } else if (questionType === 'multi') {
            // 多选题 - 查找所有选中的复选框
            const selectedOptions = [];
            const checkboxes = container.querySelectorAll(`input[type="checkbox"]`);
            
            for (const checkbox of checkboxes) {
                if (checkbox.checked) {
                    // 从ID中提取选项字母
                    const idParts = checkbox.id.split('_');
                    const optionLetter = idParts[idParts.length - 1];
                    selectedOptions.push(optionLetter);
                }
            }
            
            userAnswer = selectedOptions.sort().join(', ');
        }
        
        // 判分并显示结果
        const normalizedUserAnswer = userAnswer.replace(/\s+/g, '').toUpperCase();
        const normalizedCorrectAnswer = correctAnswer.replace(/\s+/g, '').toUpperCase();
        
        if (normalizedUserAnswer === normalizedCorrectAnswer) {
            resultDiv.innerHTML = '<span class="correct">✓ 回答正确！</span>';
        } else {
            // resultDiv.innerHTML = `<span class="incorrect">✗ 回答错误！正确答案：${correctAnswer}</span>`;
            resultDiv.innerHTML = `<span class="incorrect">✗ 回答错误！</span>`;
        }
    }
});

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有代码输入框
    const codeInputs = document.querySelectorAll('.code-input');
    codeInputs.forEach(input => {
        const lang = input.getAttribute('data-lang');
        // 设置语言提示文本
        input.setAttribute('placeholder', `在此编辑${lang}代码...`);
        
        // 启用自适应高度
        autoResizeTextarea(input);
    });
});

/**
 * 使文本区域自动调整高度适应内容
 * @param {HTMLTextAreaElement} textarea - 要自动调整的文本区域元素
 */
function autoResizeTextarea(textarea) {
    // 初始化高度设置
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
    
    // 添加输入事件监听器
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}

// 显示登录表单
function showLoginForm() {
    document.getElementById('loginOverlay').style.display = 'flex';
}

// 隐藏登录表单
function hideLoginForm() {
    document.getElementById('loginOverlay').style.display = 'none';
    document.getElementById('loginMessage').style.display = 'none';
}

// 登录到 CodeCin
function loginToCodeCin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageElement = document.getElementById('loginMessage');
    
    // 清空消息
    messageElement.style.display = 'none';
    messageElement.className = 'message';
    
    if (!username || !password) {
        messageElement.textContent = '用户名和密码不能为空';
        messageElement.classList.add('error');
        messageElement.style.display = 'block';
        return;
    }
    
    // 发送登录请求
    fetch('/login_codecin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageElement.textContent = '登录成功！';
            messageElement.classList.add('success');
            messageElement.style.display = 'block';
            
            // 更新登录区域显示
            updateLoginDisplay(username, data.sid, data.sig);
            
            // 3秒后关闭登录框
            setTimeout(() => {
                hideLoginForm();
                document.getElementById('username').value = '';
                document.getElementById('password').value = '';
            }, 3000);
        } else {
            messageElement.textContent = data.message || '登录失败，请重试';
            messageElement.classList.add('error');
            messageElement.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('登录错误:', error);
        messageElement.textContent = '登录请求失败';
        messageElement.classList.add('error');
        messageElement.style.display = 'block';
    });
}


// 更新登录状态显示
function updateLoginDisplay(username, sigIn, sidIn) {
    const loginArea = document.getElementById('loginArea');
    
    // // 创建简化的cookie显示（只显示前6位和后4位）
    // const cookiePreview = cookieInfo ? 
    //     `${cookieInfo.substring(0, 6)}...${cookieInfo.substring(cookieInfo.length - 4)}` : 
    //     '无cookie';
    
    loginArea.innerHTML = `
        <div class="nav-item login-status">
            <div class="login-header">已登录为: ${username}</div>
            <div class="cookie-info">
                <div class="cookie-label">Sid:</div>
                <div class="cookie-value">${sigIn}</div>
                <div class="cookie-label">Sig:</div>
                <div class="cookie-value">${sidIn}</div>
            </div>
            <!-- <button class="logout-btn" onclick="logout()">登出</button> -->
        </div>
    `;
}

// 登出功能
function logout() {
    fetch('/logout_codecin')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 恢复登录按钮
                document.getElementById('loginArea').innerHTML = `
                    <div class="nav-item" onclick="showLoginForm()">登录</div>
                `;
            }
        });
}