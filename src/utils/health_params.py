def calculate_bmr(user_data):
    """
    计算基础代谢率（BMR）。
    """
    if user_data["gender"] == "male":
        bmr = 10 * user_data["weight"] + 6.25 * user_data["height"] - 5 * user_data["age"] + 5
    else:
        bmr = 10 * user_data["weight"] + 6.25 * user_data["height"] - 5 * user_data["age"] - 161
    return bmr

def calculate_tdee(bmr, activity_level):
    """
    计算总能量消耗（TDEE）。
    """
    activity_factors = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }
    return bmr * activity_factors.get(activity_level, 1.2)

def calculate_nutrient_needs(meal_energy):
    """
    计算每餐的营养需求。
    """
    return [
        meal_energy * 0.5 / 4,  # 碳水化合物占 50%，1g 碳水化合物 = 4 kcal
        meal_energy * 0.2 / 4,  # 蛋白质占 20%，1g 蛋白质 = 4 kcal
        meal_energy * 0.3 / 9,  # 脂肪占 30%，1g 脂肪 = 9 kcal
        10,  # 每餐膳食纤维需求（假设为 10g）
    ]