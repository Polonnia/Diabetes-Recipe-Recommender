def calculate_health_score(user_data, recipe_nutrition, predicted_glucose):
    # 基础营养需求计算
    bmi = user_data["weight"] / (user_data["height"] / 100) ** 2
    protein_need = 1.2 if bmi > 25 else 0.8
    
    # 血糖控制评分
    if 80 <= predicted_glucose <= 180:
        glucose_score = 10
    else:
        glucose_score = 0
    
    # 综合评分
    health_score = (glucose_score + protein_need * recipe_nutrition["protein"]) / 2
    return min(health_score, 10)