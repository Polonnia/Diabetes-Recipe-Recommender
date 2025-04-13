import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
#from gevent import pywsgi
import os
import csv
from KG import KnowledgeGraph
from openai import OpenAI
from dotenv import load_dotenv
import json
from functools import lru_cache

# 加载环境变量
load_dotenv()

# 禁用 TensorFlow oneDNN 警告
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)
CORS(app)

# 初始化知识图谱
kg = KnowledgeGraph("bolt://localhost:7687", "neo4j", "2winadmin")
meal_type_default = "lunch"  # 默认餐次
recipes = []

# CSV 数据存储路径
USER_BLOOD_GLUC_DATA_PATH = "../data/user_blood_glucose_data.csv"

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("警告：未设置 DEEPSEEK_API_KEY 环境变量，请检查 .env 文件")
    DEEPSEEK_API_KEY = "your_api_key_here"  # 临时使用默认值，请替换为您的实际 API key

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# 服务器API配置
SERVER_API_URL = "http://e9790bb22df84f8cae565d9b24c0eabe.cloud.lanyun.net:10086"  # 替换为您的服务器地址

# 缓存食谱推荐结果
@lru_cache(maxsize=100)
def get_cached_recommendations(meal_type, user_data_str):
    user_data = json.loads(user_data_str)
    return kg.recommend_recipes(user_data, meal_type)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    return render_template("data.html")

@app.route("/chat", methods=["POST"])
def chat():
    """
    处理前端问答请求：
    请求数据格式：
    {
        "message": "用户输入的消息内容",
        "user_data": { ... }  # 用户健康信息
    }
    
    判断逻辑：
    - 如果消息中包含"推荐"和"食谱"，则认为是食谱推荐请求，进一步解析餐次信息；
    - 否则认为是普通问题，调用 DeepSeek API 回答。
    """
    try:
        data = request.get_json()
        message = data.get("message", "")
        user_data = data.get("user_data", {})

        print(f"Received message: {message}")
        print(f"User data: {user_data}")

        # 判断是否为食谱推荐请求
        if ("推荐" in message and "食谱" in message) or \
           ("吃什么" in message) or \
           ("推荐" in message and ("早餐" in message or "午餐" in message or "晚餐" in message)):
            try:
                # 解析餐次信息，若没有明确说明则默认使用午餐
                if "早餐" in message or "早饭" in message:
                    meal_type = "breakfast"
                elif "午餐" in message or "午饭" in message or "中午" in message:
                    meal_type = "lunch"
                elif "晚餐" in message or "晚饭" in message or "晚上" in message:
                    meal_type = "dinner"
                else:
                    meal_type = meal_type_default
                
                print(f"Selected meal type: {meal_type}")
                
                recipes, ratio, information = kg.recommend_recipes(user_data, meal_type)
                print(f"Recommended recipes: {recipes}")
                print(f"Recipe information: {information}")
                
                prompt = kg.generate_prompt(recipes, meal_type, ratio)
                print("Generated prompt for DeepSeek")
                
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一个专业的糖尿病饮食营养师，请根据用户的需求和健康数据，提供详细的食谱建议。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.7,
                        max_tokens=2000,
                        stream=False
                    )
                    print("DeepSeek API response received")
                    
                    recipe_response = response.choices[0].message.content
                    print(f"DeepSeek response content: {recipe_response[:100]}...")  # 只打印前100个字符
                    
                    return jsonify({
                        "message": recipe_response,
                        "recipes": recipes,
                        "mealType": meal_type,
                        "health_score": information["health_score"],
                        "energy": information["energy"],
                        "PBG": information["PBG"],
                        "carb": information["carb"],
                        "protein": information["protein"],
                        "fat": information["fat"],
                        "fiber": information["fiber"]
                    })
                    
                except Exception as e:
                    print(f"DeepSeek API error: {str(e)}")
                    return jsonify({"error": f"DeepSeek API请求失败: {str(e)}"}), 500
                    
            except Exception as e:
                print(f"Recipe recommendation error: {str(e)}")
                return jsonify({"error": f"食谱推荐失败: {str(e)}"}), 500

        else:
            try:
                # 构建用户信息字符串
                user_info = ""
                if user_data:
                    user_info = f"""
用户信息：
- 身高：{user_data.get('height')}cm
- 体重：{user_data.get('weight')}kg
- 年龄：{user_data.get('age')}岁
- 性别：{user_data.get('gender')}
- 餐前血糖：{user_data.get('pre_meal_glucose')}mmol/L
- 餐前胰岛素：{user_data.get('pre_meal_insulin')}单位
- 运动水平：{user_data.get('activity_level')}
"""

                # 调用 DeepSeek API 回答问题
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个糖尿病领域专家，请根据用户的情况和问题提供专业的建议。回答要详细、专业且易懂。"
                        },
                        {
                            "role": "user",
                            "content": f"{user_info}\n问题：{message}\n\n请提供专业的回答，包括：\n1. 针对问题的直接回答\n2. 相关的健康建议\n3. 需要注意的事项"
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    stream=False
                )
                
                answer = response.choices[0].message.content
                
                return jsonify({"message": answer})
                
            except Exception as e:
                print(f"Question answering error: {str(e)}")
                return jsonify({"error": f"回答问题失败: {str(e)}"}), 500
                
    except Exception as e:
        print(f"General error in chat endpoint: {str(e)}")
        return jsonify({"error": f"处理请求时发生错误: {str(e)}"}), 500

@app.route("/api/user-data", methods=["POST"])
def handle_user_data():
    user_data = request.get_json()
    return jsonify({"message": "用户数据已保存", "user_data": user_data})

@app.route("/update-pref", methods=["POST"])
def update_pref():
    data = request.get_json()
    print(f"Received update_pref data: {data}")
    recipe_name = data.get("recipe")
    rating = data.get("rating")
    
    if not recipe_name or rating is None:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        result = kg.update_pref(rating, recipe_name)
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# @app.route("/store_feedback", methods=["POST"])
# def store_feedback():
#     feedback_data = request.get_json()
#     ratings = feedback_data['ratings']
#     for i, recipe in recipes:
#         kg.update_pref(ratings[i], recipe)
#     pre_meal_glucose = feedback_data['pre_meal_glucose']
#     recipe_nutrition = feedback_data['recipe_nutrition']
#     post_meal_glucose_60 = feedback_data['post_meal_glucose_60']
#     post_meal_glucose_120 = feedback_data['post_meal_glucose_120']
#     post_meal_glucose_180 = feedback_data['post_meal_glucose_180']

#     store_data_to_csv(
#         pre_meal_glucose, recipe_nutrition,
#         post_meal_glucose_60, post_meal_glucose_120, post_meal_glucose_180
#     )
#     return jsonify({"message": "反馈已存储，谢谢！"})

# def store_data_to_csv(pre_meal_glucose, recipe_nutrition, post_meal_glucose_60, post_meal_glucose_120, post_meal_glucose_180):
#     if not os.path.exists(USER_BLOOD_GLUC_DATA_PATH):
#         with open(USER_BLOOD_GLUC_DATA_PATH, mode='w', newline='') as file:
#             writer = csv.writer(file)
#             writer.writerow([
#                 "Pre_Meal_Glucose", "Carb", "Protein", "Fat", "Fiber",
#                 "Post_Meal_Glucose_60min", "Post_Meal_Glucose_120min", "Post_Meal_Glucose_180min"
#             ])
#     with open(USER_BLOOD_GLUC_DATA_PATH, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow([
#             pre_meal_glucose,
#             recipe_nutrition["carb"],
#             recipe_nutrition["protein"],
#             recipe_nutrition["fat"],
#             recipe_nutrition["fiber"],
#             post_meal_glucose_60,
#             post_meal_glucose_120,
#             post_meal_glucose_180
#         ])

if __name__ == "__main__":
    # 禁用调试模式，防止自动重载
    app.run(host='0.0.0.0', port=5000, debug=False)
