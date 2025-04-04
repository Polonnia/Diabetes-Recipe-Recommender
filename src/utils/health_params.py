def calculate_bmr(user_data):
    weight = float(user_data["weight"])
    height = float(user_data["height"])
    age = float(user_data["age"])
    
    if user_data["gender"].lower() == "female":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    
    return bmr

def calculate_tdee(bmr, activity_level):
    activity_factors = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    
    activity_level = str(activity_level).lower()
    activity_factor = activity_factors.get(activity_level, 1.2)
    
    return bmr * activity_factor

def calculate_nutrient_needs(tdee):
    carb_percentage = 0.5
    protein_percentage = 0.2
    fat_percentage = 0.3
    
    carb_calories = tdee * carb_percentage
    protein_calories = tdee * protein_percentage
    fat_calories = tdee * fat_percentage
    
    return {
        "carb": round(carb_calories / 4),
        "protein": round(protein_calories / 4),
        "fat": round(fat_calories / 9)
    }