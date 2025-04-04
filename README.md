# 糖小智 - 糖尿病饮食推荐系统

糖小智是一个基于人工智能的糖尿病饮食推荐系统，旨在为糖尿病患者提供个性化的饮食建议和健康管理指导。系统通过分析用户的健康数据，结合专业的医学知识，为用户提供合适的食谱推荐和饮食建议。

## 功能特点

- 🤖 智能对话：提供自然语言交互界面，回答用户关于糖尿病饮食的问题
- 📊 个性化推荐：根据用户的健康数据（身高、体重、血糖等）提供定制化的食谱推荐
- 📱 响应式设计：支持各种设备访问，提供良好的移动端体验
- 🎨 现代化界面：采用现代化的UI设计，提供直观的用户体验
- 📝 Markdown支持：支持在对话中显示格式化的文本内容

## 技术栈

- 后端：Python Flask
- 前端：HTML5, CSS3, JavaScript
- UI框架：Bootstrap 5
- 图标：Font Awesome
- 其他：jQuery, Marked.js

## 系统要求

- Python 3.8+
- pip（Python包管理器）

## 安装步骤

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd diabetes_diet_recommendation
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行应用：
```bash
python src/app.py
```

5. 访问系统：
打开浏览器访问 `http://localhost:5000`

## 使用说明

1. 健康数据管理
   - 访问 `/data` 页面
   - 填写个人健康信息（身高、体重、年龄等）
   - 保存数据用于个性化推荐

2. 智能对话
   - 访问首页开始对话
   - 输入问题获取饮食建议
   - 系统会根据您的健康数据提供个性化建议

3. 食谱推荐
   - 系统会自动分析您的健康数据
   - 提供适合的食谱推荐
   - 包含详细的营养成分和烹饪说明

## 项目结构

```
diabetes_diet_recommendation/
├── src/
│   ├── app.py              # Flask应用主文件
│   ├── static/             # 静态资源
│   │   ├── app.js         # 前端JavaScript
│   │   ├── data.js        # 数据页面JavaScript
│   │   └── style.css      # 样式文件
│   └── templates/         # HTML模板
│       ├── index.html     # 主页面
│       └── data.html      # 数据输入页面
├── requirements.txt       # 项目依赖
└── README.md             # 项目文档
```