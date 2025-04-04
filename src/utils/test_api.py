from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")

# 初始化客户端
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def test_api():
    try:
        print("正在测试 DeepSeek API 连接...")
        
        # 发送一个简单的测试请求
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个测试助手。"
                },
                {
                    "role": "user",
                    "content": "你好，请回复'测试成功'。"
                }
            ],
            temperature=0.7,
            max_tokens=100,
            stream=False
        )
        
        # 打印响应
        print("\nAPI 响应:")
        print(response.choices[0].message.content)
        print("\nAPI 连接测试成功！")
        
    except Exception as e:
        print("\nAPI 连接测试失败！")
        print(f"错误信息: {str(e)}")

if __name__ == "__main__":
    test_api() 