import torch
import numpy as np
import joblib
from train_glucose_model import GlucosePredictor

# 加载模型
def load_model(model, path = "..\models\llama.pth"):
    model.load_state_dict(torch.load(path))
    model.eval()

# 预测餐后血糖
def predict_glucose(model, scaler, pre_meal_glucose, carb, fat, fiber, insulin):
    # 输入数据
    inputs = np.array([[pre_meal_glucose, carb, fat, fiber, insulin]])
    
    # 标准化
    inputs = scaler.transform(inputs)
    inputs = torch.tensor(inputs, dtype=torch.float32)
    
    # 预测
    with torch.no_grad():
        predicted_glucose = model(inputs).numpy()[0]
    
    return predicted_glucose

# 主函数
def main():
    # 初始化模型
    input_size = 5  # 输入特征数量
    hidden_size = 64
    output_size = 3  # 输出为餐后 60、120、180 分钟的血糖
    model = GlucosePredictor(input_size, hidden_size, output_size)
    
    # 加载模型和标准化器
    load_model(model, "models/glucose_predictor.pth")
    scaler = joblib.load("models/scaler.pkl")

    # 示例预测
    pre_meal_glucose = 120
    carb = 50
    fat = 20
    fiber = 5
    insulin = 5
    predicted_glucose = predict_glucose(model, scaler, pre_meal_glucose, carb, fat, fiber, insulin)
    print(f"预测的餐后血糖值（60分钟、120分钟、180分钟）：{predicted_glucose}")

if __name__ == "__main__":
    main()