document.addEventListener('DOMContentLoaded', function() {
    const courseSetup = document.getElementById('course-setup');
    const pointsDisplay = document.getElementById('points-display');
    const quickPoints = document.getElementById('quick-points');
    const studentSelect = document.getElementById('student-select');
    const historyCourses = document.getElementById('history-courses');
    
    let currentCourseId = null;
    let studentsList = [];
    
    // 设置默认日期为今天
    document.getElementById('course-date').valueAsDate = new Date();
    
    // 加载历史课程
    loadHistoryCourses();
    
    // 开始课程按钮事件
    document.getElementById('start-course').addEventListener('click', function() {
        const courseName = document.getElementById('course-name').value.trim();
        const courseDate = document.getElementById('course-date').value;
        const studentsText = document.getElementById('students').value.trim();
        
        // 检查输入是否有效
        if (!courseName) {
            alert('请输入课程名称');
            return;
        }
        
        if (!studentsText) {
            alert('请输入上课学生');
            return;
        }
        
        // 处理学生名单
        const students = studentsText.split(',').map(s => s.trim()).filter(s => s);
        
        // 准备要发送的数据
        const data = {
            name: courseName,
            date: courseDate,
            students: students.join(', ')
        };
        
        // 创建新课程
        fetch('/create_course', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // 设置当前课程信息
            currentCourseId = data.course_id;
            studentsList = data.students;
            
            // 更新界面
            courseSetup.style.display = 'none';
            pointsDisplay.style.display = 'block';
            quickPoints.style.display = 'block';
            
            // 显示课程信息
            document.getElementById('display-course-name').textContent = courseName;
            document.getElementById('display-course-date').textContent = courseDate;
            
            // 创建学生选择区
            createStudentSelection();
            
            // 加载学生积分数据
            loadPointsData();
            
            // 重新加载历史课程列表
            loadHistoryCourses();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('发生错误: ' + error.message);
        });
    });
    
    // 历史课程选择框事件
    historyCourses.addEventListener('change', function() {
        const courseId = this.value;
        if (!courseId) return;
        
        // 获取选中的课程信息
        fetch(`/get_course_data?course_id=${courseId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                // 填充表单
                document.getElementById('course-name').value = data.course_name;
                document.getElementById('course-date').value = data.course_date;
                document.getElementById('students').value = data.students.join(', ');
            })
            .catch(error => {
                console.error('Error loading history course:', error);
            });
    });
    
    // 创建学生选择区域
    function createStudentSelection() {
        studentSelect.innerHTML = '';
        
        studentsList.forEach(student => {
            const container = document.createElement('div');
            container.className = 'student-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `student-${student}`;
            checkbox.value = student;
            
            const label = document.createElement('label');
            label.htmlFor = `student-${student}`;
            label.textContent = student;
            
            container.appendChild(checkbox);
            container.appendChild(label);
            studentSelect.appendChild(container);
        });
    }
    
    // 加载积分数据
    function loadPointsData() {
        if (!currentCourseId) return;
        
        fetch(`/get_course_data?course_id=${currentCourseId}`)
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#points-table tbody');
            tbody.innerHTML = '';
            
            studentsList.forEach(student => {
                const row = document.createElement('tr');
                
                const nameCell = document.createElement('td');
                nameCell.textContent = student;
                
                const totalCell = document.createElement('td');
                totalCell.textContent = data.student_points[student] || 0;
                
                const todayCell = document.createElement('td');
                todayCell.textContent = data.today_points[student] || 0;
                
                row.appendChild(nameCell);
                row.appendChild(totalCell);
                row.appendChild(todayCell);
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading points:', error);
        });
    }
    
    // 加分按钮处理
    const pointButtons = document.querySelectorAll('.btn-points');
    pointButtons.forEach(button => {
        button.addEventListener('click', function() {
            const points = this.getAttribute('data-points');
            
            if (points === 'custom') {
                document.getElementById('custom-points').style.display = 'flex';
                return;
            }
            
            addPointsToStudents(parseInt(points));
        });
    });
    
    // 自定义积分确认按钮
    document.getElementById('confirm-custom').addEventListener('click', function() {
        const pointsInput = document.getElementById('custom-points-input');
        const pointsValue = parseInt(pointsInput.value);
        
        if (isNaN(pointsValue)) {
            alert('请输入有效的正数积分值');
            return;
        }
        
        addPointsToStudents(pointsValue);
        document.getElementById('custom-points').style.display = 'none';
        pointsInput.value = '';
    });
    
    // 为选中学生添加积分
    function addPointsToStudents(points) {
        const selectedStudents = [];
        const checkboxes = studentSelect.querySelectorAll('input[type="checkbox"]:checked');
        
        if (checkboxes.length === 0) {
            alert('请选择至少一个学生');
            return;
        }
        
        checkboxes.forEach(checkbox => {
            selectedStudents.push(checkbox.value);
        });
        
        const data = {
            course_id: currentCourseId,
            students: selectedStudents,
            points: points
        };
        
        fetch('/add_points', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                // 刷新积分显示
                loadPointsData();
                
                // 清除选择
                checkboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('发生错误: ' + error.message);
        });
    }
    
    // 加载历史课程列表
    function loadHistoryCourses() {
        fetch('/get_courses')
            .then(response => response.json())
            .then(courses => {
                // 保存当前选中的课程ID（如果有）
                const currentSelected = historyCourses.value;
                
                // 清空下拉框
                historyCourses.innerHTML = '';
                
                // 添加默认选项
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '-- 选择历史课程 --';
                historyCourses.appendChild(defaultOption);
                
                // 添加历史课程选项
                courses.forEach(course => {
                    const option = document.createElement('option');
                    option.value = course.id;
                    option.textContent = `${course.name} (${course.date})`;
                    historyCourses.appendChild(option);
                });
                
                // 恢复之前选中的课程
                if (currentSelected && courses.some(course => course.id === parseInt(currentSelected))) {
                    historyCourses.value = currentSelected;
                }
            })
            .catch(error => {
                console.error('Error loading history courses:', error);
            });
    }
});