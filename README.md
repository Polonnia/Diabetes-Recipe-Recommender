src里面是推荐系统的代码，config存用户数据和一些参数，models存放训练好的Llama和FNN模型
---

**健康评分计算模块**

 **功能概述**
健康评分计算模块用于评估食谱的健康程度，结合用户的健康状况和食谱的营养成分，生成一个综合评分（`health_score`）。该评分由两部分组成：
1. **血糖评分（`glucose_score`）**：基于预测的餐后血糖值，评估食谱对血糖控制的影响。
2. **营养评分（`nutrient_score`）**：基于食谱的营养成分是否满足用户的能量需求和营养素比例。

**输入参数**
1. **用户健康数据（`user_data`）**：
   - `height`：身高（cm）。
   - `weight`：体重（kg）。
   - `age`：年龄（岁）。
   - `gender`：性别（`male` 或 `female`）。
   - `activity_level`：活动水平（`sedentary`、`lightly_active`、`moderately_active`、`very_active`、`extra_active`）。

2. **食谱营养成分（`recipe_nutrition`）**：
   - `carb`：碳水化合物含量（g）。
   - `protein`：蛋白质含量（g）。
   - `fat`：脂肪含量（g）。
   - `fiber`：纤维含量（g）。

3. **预测的餐后血糖值（`predicted_glucose`）**：
   - 包含餐后 60、120、180 分钟的血糖值（mmol/L）。

4. **餐次类型（`meal_type`）**：
   - 可选值为 `breakfast`（早餐）、`lunch`（午餐）、`dinner`（晚餐）。

#### **输出结果**
- **健康评分（`health_score`）**：范围 0-10，评分越高表示食谱越健康。

#### **评分逻辑**
1. **血糖评分（`glucose_score`）**：
   - 根据 II 型糖尿病餐后血糖范围，对每个时间点（60、120、180 分钟）的血糖值进行评分。
   - 评分规则：
     - 正常范围：10 分
     - 良好范围：8 分
     - 一般范围：6 分
     - 不良范围：4 分
     - 极其不良范围：0 分
   - 最终 `glucose_score` 为三个时间点评分的平均值。

2. **营养评分（`nutrient_score`）**：
   - 根据用户的健康信息计算每日能量需求（TDEE），再根据餐次类型计算每餐的能量需求。
   - 每餐的营养需求比例：
     - 碳水化合物：50%
     - 蛋白质：20%
     - 脂肪：30%
     - 纤维：10g
   - 对比食谱的营养成分与用户需求，计算 `nutrient_score`：
     - 每个营养素的评分满分为 2.5 分（共 4 个营养素，总分 10 分）。
     - 如果食谱的营养成分在用户需求的 ±20% 范围内，得满分；否则得 0 分。

3. **综合评分（`health_score`）**：
   - `health_score = 0.6 * glucose_score + 0.4 * nutrient_score`
   - 最终评分不超过 10 分。

#### **核心函数**
1. **`calculate_health_score`**：
   - 综合 `glucose_score` 和 `nutrient_score`，计算健康评分。

2. **`calculate_glucose_score`**：
   - 根据预测的餐后血糖值计算血糖评分。

3. **`calculate_nutrient_score`**：
   - 根据用户健康信息和食谱营养成分计算营养评分。

4. **辅助函数**：
   - `calculate_bmr`：计算基础代谢率（BMR）。
   - `calculate_tdee`：计算总能量消耗（TDEE）。
   - `calculate_meal_energy`：计算每餐的能量需求。
   - `calculate_meal_nutrient_needs`：计算每餐的营养需求。

 **示例调用**
```python
# 用户健康数据
user_data = {
    "height": 170,  # 身高（cm）
    "weight": 70,  # 体重（kg）
    "age": 45,  # 年龄（岁）
    "gender": "male",  # 性别（male/female）
    "activity_level": "moderately_active",  # 活动水平
}

# 食谱营养成分
recipe_nutrition = {
    "carb": 50,  # 碳水化合物（g）
    "protein": 20,  # 蛋白质（g）
    "fat": 15,  # 脂肪（g）
    "fiber": 5,  # 纤维（g）
}

# 预测的餐后血糖值
predicted_glucose = [8.0, 7.5, 6.5]  # 60、120、180 分钟

# 计算健康评分
health_score = calculate_health_score(user_data, recipe_nutrition, predicted_glucose, "lunch")
print(f"健康评分：{health_score}")
```

**注意事项**
1. **血糖评分**：
   - 血糖范围基于 II 型糖尿病标准，需确保预测的血糖值单位为 mmol/L。
   - 如果预测的血糖值超出范围，评分会相应降低。

2. **营养评分**：
   - 营养需求基于用户的能量消耗和餐次比例，需确保用户健康数据准确。
   - 食谱的营养成分需与用户需求匹配，允许 ±20% 的误差。

3. **评分权重**：
   - 血糖评分占 60%，营养评分占 40%，可根据实际需求调整权重。
