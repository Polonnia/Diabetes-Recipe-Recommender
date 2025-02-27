from transformers import LlamaForCausalLM, LlamaTokenizer
import torch
from KG import recommend_recipes

class LlamaDietAssistant:
    def __init__(self, model_name="decapoda-research/llama-7b-hf"):
        # 加载 Llama 模型和分词器
        self.tokenizer = LlamaTokenizer.from_pretrained(model_name)
        self.model = LlamaForCausalLM.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def generate_response(self, prompt, max_length=200):
        """
        生成 Llama 模型的回答。
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    def answer_diabetes_question(self, question, user_data):
        """
        回答糖尿病相关的通用问题，结合用户的健康状况。
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
        
        # 生成回答
        response = self.generate_response(prompt)
        return response

    def generate_recipe_recommendation(self, kg):
        """
        生成食谱推荐，包括名称、原料及重量、做法。
        """
        # 获取推荐的食谱
        recommended_recipes = recommend_recipes(kg)
        
        if not recommended_recipes:
            return "暂无推荐的食谱。"
        
        
        # 生成食谱推荐描述
        recommendations = []
        for recipe in recommended_recipes:
            ingredients = kg.get_recipe_ingredients(recipe)
            ingredients_text = "\n".join(
                f"- {i['name']} {i['weight']}g" for i in ingredients
            )
            
            prompt = (
                f"推荐一道适合糖尿病患者的食谱：{recipe_name}\n"
                f"包含的原料及重量：\n{ingredients_text}\n"
                "请用描述制作这道菜的步骤，并简洁的语言描述这道菜的特点和适合糖尿病患者的原因。"
            )
            response = self.generate_response(prompt)
            recommendations.append(response)
        
        return "\n\n".join(recommendations)

    def process_user_rating(self, rating, recipe_name, kg):
        """
        处理用户打分，并更新食谱和食材的 preference_score。
        """
        try:
            rating = float(rating)
            if 0 <= rating <= 10:
                # 更新食谱的 preference_score
                with kg.driver.session() as session:
                    session.write_transaction(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name}) "
                            "SET r.preference_score = (r.preference_score + $rating) / 2",
                            name=recipe_name, rating=rating
                        )
                    )
                
                # 更新食材的 preference_score
                with kg.driver.session() as session:
                    session.write_transaction(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name})-[:CONTAINS]->(i:Ingredient) "
                            "SET i.preference_score = (i.preference_score + $rating) / 2",
                            name=recipe_name, rating=rating
                        )
                    )
                
                return f"感谢您的评分！食谱和食材的偏好评分已更新。"
            else:
                return "评分必须在 0 到 10 之间。"
        except ValueError:
            return "请输入有效的数值。"

    def handle_user_request(self, user_input, kg, user_data):
        """
        处理用户请求，自动解析是普通问题还是食谱推荐请求。
        """
        if "推荐" in user_input and "食谱" in user_input:
            # 用户请求食谱推荐
            recommendations = self.generate_recipe_recommendation(kg, user_data)
            feedback_prompt = (
                "请用餐后反馈对食谱的评分（0-10 分）和餐后血糖（可选）。\n"
                "例如：评分：8，餐后血糖：150。"
            )
            return f"{recommendations}\n\n{feedback_prompt}"
        else:
            # 用户提出普通问题
            return self.answer_diabetes_question(user_input)

# 示例用法
if __name__ == "__main__":

    # 初始化 Llama 助手
    llama_assistant = LlamaDietAssistant()

    # 初始化知识图谱
    kg = KnowledgeGraph("bolt://localhost:7687", "neo4j", "password")

    # 用户健康数据
    user_data = {
        "height": 170,
        "weight": 70,
        "age": 45,
        "gender": "male",
        "diabetes_type": "II",
        "pre_meal_glucose": 120,
        "pre_meal_insulin": 5
    }

    # 用户请求
    user_input = "请为我推荐今天的早餐食谱"
    response = llama_assistant.handle_user_request(user_input, kg, user_data)
    print(response)

    # 用户反馈
    user_feedback = "评分：8，餐后血糖：150"
    recipe_name = "清蒸鲈鱼"  # 假设用户食用的是清蒸鲈鱼
    rating = user_feedback.split("：")[1].split("，")[0]  # 提取评分
    update_result = llama_assistant.process_user_rating(rating, recipe_name, kg)
    print(update_result)