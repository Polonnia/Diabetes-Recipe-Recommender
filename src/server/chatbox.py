import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class DietAssistant:
    def __init__(self, model_path="/root/ddr/models/diabetica"):
        """
        初始化饮食助手，使用 Hugging Face 提供的模型进行文本生成。
        参数：
        - model_path：Hugging Face 上的模型标识符或本地模型路径。
        """
        # 设置设备
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = model_path

        print(f"正在从 {model_path} 加载模型到 {self.device} ...")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype="auto",
            device_map="auto"
        )
        print("模型加载完成！")

        print("正在加载分词器...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        print("分词器加载完成！")

    def generate_response(self, question: str, user_data: dict = None) -> str:
        """
        生成回答，支持带用户数据的糖尿病相关问题和不带用户数据的一般问题
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(question, user_data) if user_data else self._build_general_prompt(question)
            
            # 生成回答
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # 解码回答
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(response)
            return response.split("回答：")[-1].strip()
            
        except Exception as e:
            print(f"生成回答时出错: {str(e)}")
            return "抱歉，处理您的问题时出现了错误，请稍后重试。"

    def _build_prompt(self, question: str, user_data: dict) -> str:
        """
        构建带用户数据的提示词
        """
        user_info = f"""
用户信息：
- 身高：{user_data['height']}cm
- 体重：{user_data['weight']}kg
- 年龄：{user_data['age']}岁
- 性别：{user_data['gender']}
- 餐前血糖：{user_data['pre_meal_glucose']}mg/dL
- 餐前胰岛素：{user_data['pre_meal_insulin']}单位
- 运动水平：{user_data['activity_level']}
"""
        
        prompt = f"""你是一个专业的糖尿病饮食营养师。请根据以下用户信息和问题，提供专业的建议。

{user_info}

问题：{question}

请提供详细的回答，包括：
1. 针对用户具体情况的建议
2. 相关的饮食注意事项
3. 可能的风险提示

回答："""
        return prompt

    def _build_general_prompt(self, question: str) -> str:
        """
        构建一般性问题的提示词
        """
        return f"""你是一个专业的糖尿病饮食营养师。请回答以下问题：

问题：{question}

请提供专业的回答："""
    
if __name__ == "__main__":
    llm = DietAssistant()
    response = llm.generate_response(question="我早餐可以吃什么", 
                                            user_data={'height': 165, 'weight': 120, 
                                             'age': 25, 'gender': 'female', 
                                             'pre_meal_glucose': 5, 'pre_meal_insulin': 0, 
                                             'activity_level': 'moderately_active', 'TDEE': 1600})
    print(response)