
from transformers import AutoModelForCausalLM, AutoTokenizer

class DietAssistant:
    def __init__(self, model_path="WaltonFuture/Diabetica-7B"):
        # 指定设备为 cuda
        self.device = "cuda"  # 如有需要，可加入 torch.cuda.is_available() 判断
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype="auto",
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

    def generate_response(self, prompt, max_new_tokens=2048):
        """
        利用聊天模板生成模型回复
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        # 使用 tokenizer 提供的聊天模板，将消息拼接为最终生成的提示词
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
        generated_ids = self.model.generate(
            model_inputs.input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=True,
        )
        # 去除提示词部分，只保留生成部分
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response

    def answer_diabetes_question(self, question, user_data):
        """
        回答糖尿病相关的通用问题，结合用户健康状况。
        """
        # 构建提示词，附加用户健康状况
        prompt = (
            f"你是一名糖尿病健康顾问，请根据以下患者健康状况回答问题：\n"
            f"患者信息：\n"
            f"- 身高：{user_data['height']} cm\n"
            f"- 体重：{user_data['weight']} kg\n"
            f"- 年龄：{user_data['age']} 岁\n"
            f"- 性别：{user_data['gender']}\n"
            f"- 糖尿病类型：{user_data['diabetes_type']}\n"
            f"- 餐前血糖：{user_data['pre_meal_glucose']} mg/dL\n"
            f"- 餐前胰岛素注射量：{user_data['pre_meal_insulin']} 单位\n"
            f"问题：{question}"
        )
        response = self.generate_response(prompt)
        return response

    def generate_recipe_recommendation(self, kg, user_data, meal_type="lunch"):
        """
        生成食谱推荐，包括名称、原料及重量、做法。
        
        参数：
        - kg: 知识图谱对象。
        - user_data: 用户健康数据。
        - meal_type: 餐次类型，可选值为 "breakfast"（早餐）、"lunch"（午餐）、"dinner"（晚餐）。
        
        返回：
        - 食谱推荐描述。
        """
        # 获取推荐的食谱组合
        recommended_recipes = kg.recommend_recipes(meal_type)
        # 假设此处 health_score 是在 kg.recommend_recipes 中计算得到的（如需调整需修改对应逻辑）
        group_health_score = 8.0  # 示例分数

        if not recommended_recipes:
            return "暂无推荐的食谱。"
    
        recommendations = []
        recipe_nutrition = {}
        for recipe_name in recommended_recipes:
            ingredients = kg.get_recipe_ingredients(recipe_name)
            ingredients_text = "\n".join(
                f"- {i['name']} {i['weight']}g" for i in ingredients
            )

            prompt = (
                f"推荐一道适合糖尿病患者的{meal_type}食谱：{recipe_name}\n"
                f"包含的原料及重量：\n{ingredients_text}\n"
                "请用简洁的语言描述这道菜的特点和适合糖尿病患者的原因。"
            )
            response = self.generate_response(prompt)
            recommendations.append(response)

            # 获取食谱的营养成分
            recipe_nutrition[recipe_name] = kg.calculate_recipe_nutrition(recipe_name)

        recommendations.append(f"本组食谱的总健康评分为：{group_health_score:.2f}")
        return recommendations, recipe_nutrition

    def handle_user_request(self, user_input, kg, user_data):
        """
        处理用户请求，自动解析是普通问题还是食谱推荐请求，并区分早、中、晚餐。
        """
        # 检查用户输入是否包含食谱推荐关键词
        if "推荐" in user_input and "食谱" in user_input:
            # 解析餐次信息
            meal_type = None
            if "早餐" in user_input:
                meal_type = "breakfast"
            elif "午餐" in user_input:
                meal_type = "lunch"
            elif "晚餐" in user_input:
                meal_type = "dinner"
            
            if meal_type:
                recommendations, recipe_nutrition = self.generate_recipe_recommendation(kg, user_data, meal_type)
                feedback_prompt = (
                    "请用餐后反馈对食谱的评分（0-10 分）和餐后血糖（60、120、180 分钟），例如：评分：8，餐后血糖：150, 180, 200。"
                )
                return f"{' '.join(recommendations)}\n\n{feedback_prompt}", recipe_nutrition
            else:
                recommendations, recipe_nutrition = self.generate_recipe_recommendation(kg, user_data, "lunch")
                feedback_prompt = (
                    "请用餐后反馈对食谱的评分（0-10 分）和餐后血糖（60、120、180 分钟），例如：评分：8，餐后血糖：150, 180, 200。"
                )
                return f"{' '.join(recommendations)}\n\n{feedback_prompt}", recipe_nutrition
        else:
            return self.answer_diabetes_question(user_input, user_data), {}