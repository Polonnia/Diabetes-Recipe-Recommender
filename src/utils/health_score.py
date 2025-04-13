from math import log10
def calculate_health_score(recipe_nutrition, predicted_glucose, nutrient_needs):
    """
    计算食谱的健康评分。
    
    参数：
    - recipe_nutrition: 食谱的营养成分，包含碳水化合物、蛋白质、脂肪、纤维。
    - predicted_glucose: 预测的餐后血糖值，包含 60、120、180 分钟的值。
    - nutrient_needs: 用户每餐的营养需求，包含碳水、蛋白质、脂肪。
    
    返回：
    - health_score: 健康评分，范围 0-10。
    """
    # 1. 计算 glucose_score
    glucose_score = calculate_glucose_score(predicted_glucose)
    
    # 2. 计算 nutrient_score
    nutrient_score = calculate_nutrient_score(recipe_nutrition, nutrient_needs)
    
    # 3. 综合评分
    health_score = glucose_score * log10(nutrient_score)
    return health_score

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

def calculate_nutrient_score(recipe_nutrition, nutrient_needs):
    """
    根据食谱营养成分和用户营养需求计算 nutrient_score。
    
    参数：
    - recipe_nutrition: 食谱的营养成分，包含碳水化合物、蛋白质、脂肪、纤维。
    - nutrient_needs: 用户每餐的营养需求，包含碳水、蛋白质、脂肪。
    
    返回：
    - nutrient_score: 营养评分，范围 0-10。
    """
    # 计算食谱的营养评分
    nutrient_score = 0
    for nutrient, value in recipe_nutrition.items():
        if nutrient in nutrient_needs:
            ratio = value / nutrient_needs[nutrient]  # 实际含量 / 需求
            # 根据公式：2.5 * (1 - |ratio - 1|)
            score_each = 2.5 * (1 - abs(ratio - 1))
            # 如果不希望出现负分，则可以裁剪到 0
            score_each = max(0, score_each)
            
            nutrient_score += score_each
    
    return nutrient_score
