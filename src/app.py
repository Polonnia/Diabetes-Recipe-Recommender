from flask import Flask, request, jsonify
import json
import os
import csv
from utils.health_params import *
from models.fnn_model import GlucosePredictor
from KG import KnowledgeGraph
from chatbox import DietAssistant
import predict_glucose
from utils.health_score import calculate_health_score


app = Flask(__name__)
# 初始化交互助手
assistant = DietAssistant()
    
# 初始化知识图谱
kg = KnowledgeGraph("bolt://localhost:7687", "neo4j", "2winadmin")

# 初始化模型和Scaler
model = GlucosePredictor()  # 这是一个假设的模型类，需根据实际情况修改
scaler = None  # 你可以加载已训练的scaler
user_data = {}
meal_type = "lunch"
recipes = []

# 数据存储路径
USER_BLOOD_GLUC_DATA_PATH = "../data/user_blood_glucose_data.csv"

@app.route("/submit_user_data", methods=["POST"])
def submit_user_data():
    user_data = request.get_json()
    # 计算 TDEE 和 meal_nutrient_needs
    bmr = calculate_bmr(user_data)
    tdee = calculate_tdee(bmr, user_data["activity_level"])
    nutrient_needs = calculate_nutrient_needs(tdee)
    user_data["nutrient_needs"] = nutrient_needs

# 路由：获取推荐的食谱
@app.route("/get_recipe_recommendation", methods=["POST"])
def get_recipe_recommendation():
    user_data = request.get_json()
    
    # 假设你有一个基于用户数据获取推荐食谱的函数
    recipes = kg.recommend_recipes(user_data, meal_type)
    
    # 返回食谱推荐给前端
    return jsonify({"recipes": recipes})


# 路由：处理用户反馈并存储
@app.route("/store_feedback", methods=["POST"])
def store_feedback():
    feedback_data = request.get_json()

    ratings = feedback_data['ratings']
    for i, recipe in recipes:
        kg.update_pref(ratings[i], recipe)

    pre_meal_glucose = feedback_data['pre_meal_glucose']
    recipe_nutrition = feedback_data['recipe_nutrition']
    post_meal_glucose_60 = feedback_data['post_meal_glucose_60']
    post_meal_glucose_120 = feedback_data['post_meal_glucose_120']
    post_meal_glucose_180 = feedback_data['post_meal_glucose_180']

    # 存储用户反馈数据到 CSV 文件
    store_data_to_csv(pre_meal_glucose, recipe_nutrition, post_meal_glucose_60, post_meal_glucose_120, post_meal_glucose_180)

    # 返回反馈处理成功信息
    return jsonify({"message": "感谢您的反馈！"})


# 存储用户数据到 CSV 文件
def store_data_to_csv(pre_meal_glucose, recipe_nutrition, post_meal_glucose_60, post_meal_glucose_120, post_meal_glucose_180):
    if not os.path.exists(USER_BLOOD_GLUC_DATA_PATH):
        # 如果文件不存在，先写入列标题
        with open(USER_BLOOD_GLUC_DATA_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Pre_Meal_Glucose", "Carb", "Protein", "Fat", "Fiber",
                "Post_Meal_Glucose_60min", "Post_Meal_Glucose_120min", "Post_Meal_Glucose_180min"
            ])

    # 存储数据
    with open(USER_BLOOD_GLUC_DATA_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            pre_meal_glucose, recipe_nutrition["carb"], recipe_nutrition["protein"],
            recipe_nutrition["fat"], recipe_nutrition["fiber"], post_meal_glucose_60, post_meal_glucose_120, post_meal_glucose_180
        ])


# 启动 Flask 应用
if __name__ == "__main__":
    app.run(debug=True)
