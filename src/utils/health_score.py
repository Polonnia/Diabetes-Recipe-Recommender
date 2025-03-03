def calculate_health_score(user_data, recipe_nutrition, predicted_glucose, meal_type):
    """
    计算食谱的健康评分。
    
    参数：
    - user_data: 用户健康数据，包含身高、体重、年龄、性别、活动水平等。
    - recipe_nutrition: 食谱的营养成分，包含碳水化合物、蛋白质、脂肪、纤维。
    - predicted_glucose: 预测的餐后血糖值，包含 60、120、180 分钟的值。
    - meal_type: 餐次类型，可选值为 "breakfast"（早餐）、"lunch"（午餐）、"dinner"（晚餐）。
    
    返回：
    - health_score: 健康评分，范围 0-10。
    """
    # 1. 计算 glucose_score
    glucose_score = calculate_glucose_score(predicted_glucose)
    
    # 2. 计算 nutrient_score
    nutrient_score = calculate_nutrient_score(user_data, recipe_nutrition, meal_type)
    
    # 3. 综合评分
    health_score = 0.6 * glucose_score + 0.4 * nutrient_score
    return min(health_score, 10)  # 确保评分不超过 10

def calculate_glucose_score(predicted_glucose):
    """
    根据预测的餐后血糖值计算 glucose_score。
    
    参数：
    - predicted_glucose: 预测的餐后血糖值，包含 60、120、180 分钟的值。
    
    返回：
    - glucose_score: 血糖评分，范围 0-10。
    """
    # II 型糖尿病餐后血糖范围
    glucose_ranges = {
        "60": {"normal": (6.7, 8.3), "good": (8.3, 9.9), "fair": (10.0, 12.7), "poor": (12.7, 16.1), "very_poor": (16.6, float("inf"))},
        "120": {"normal": (5.0, 7.2), "good": (7.2, 8.8), "fair": (8.9, 11.0), "poor": (11.1, 15.3), "very_poor": (15.5, float("inf"))},
        "180": {"normal": (4.4, 6.7), "good": (6.7, 8.2), "fair": (8.3, 9.9), "poor": (8.3, 14.4), "very_poor": (14.4, float("inf"))},
    }
    
    # 评分规则
    score_rules = {
        "normal": 10,
        "good": 8,
        "fair": 6,
        "poor": 4,
        "very_poor": 0,
    }
    
    # 计算每个时间点的评分
    scores = []
    for i, time in enumerate(["60", "120", "180"]):
        glucose = predicted_glucose[i]
        for range_name, (lower, upper) in glucose_ranges[time].items():
            if lower <= glucose <= upper:
                scores.append(score_rules[range_name])
                break
    
    # 取三个时间点评分的平均值
    glucose_score = sum(scores) / len(scores)
    return glucose_score

def calculate_nutrient_score(user_data, recipe_nutrition, meal_type):
    """
    根据用户健康信息和食谱营养成分计算 nutrient_score。
    
    参数：
    - user_data: 用户健康数据，包含身高、体重、年龄、性别、活动水平等。
    - recipe_nutrition: 食谱的营养成分，包含碳水化合物、蛋白质、脂肪、纤维。
    - meal_type: 餐次类型，可选值为 "breakfast"（早餐）、"lunch"（午餐）、"dinner"（晚餐）。
    
    返回：
    - nutrient_score: 营养评分，范围 0-10。
    """
    meal_ratios = {
    "breakfast": 0.3,
    "lunch": 0.4,
    "dinner": 0.3,
    }

    # 计算每餐的营养需求
    meal_nutrient_needs = [nutrient * meal_ratios["meal_type"] for nutrient in user_data["nutrient_needs"]]
    
    # 计算食谱的营养评分
    nutrient_score = 0
    for nutrient, value in recipe_nutrition.items():
        if nutrient in meal_nutrient_needs:
            ratio = value / meal_nutrient_needs[nutrient]
            if ratio >= 0.8 and ratio <= 1.2:  # 允许 ±20% 的误差
                nutrient_score += 2.5  # 每个营养素满分为 2.5 分（共 4 个营养素）
    
    return nutrient_score

