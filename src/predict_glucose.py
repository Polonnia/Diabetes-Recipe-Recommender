import torch
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from utils.train_glucose_model import GlucosePredictor

# 加载训练好的 FNN 模型
def load_model(model, path="../models/glucose_fnn.pth"):
    model.load_state_dict(torch.load(path))
    model.eval()

# 增量学习功能
def incremental_train(model, new_data, scaler, batch_size=32):
    """
    对 FNN 模型进行增量训练
    :param model: 当前 FNN 模型
    :param new_data: 新增的用户餐后血糖数据（餐前血糖、碳水化合物、脂肪、纤维、胰岛素量、餐后血糖）
    :param scaler: 数据标准化器
    :param batch_size: 每次训练的批次大小
    """
    # 假设 new_data 是一个包含多个样本的数组
    inputs = np.array([d[:5] for d in new_data])  # 获取前五个输入特征
    outputs = np.array([d[5:] for d in new_data])  # 获取餐后血糖输出（60、120、180分钟）

    # 标准化输入数据
    inputs = scaler.transform(inputs)
    inputs = torch.tensor(inputs, dtype=torch.float32)
    outputs = torch.tensor(outputs, dtype=torch.float32)

    # 设置优化器
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()

    # 增量训练
    model.train()
    for epoch in range(10):  # 进行10轮训练，可以根据需要修改
        for i in range(0, len(inputs), batch_size):
            batch_inputs = inputs[i:i + batch_size]
            batch_outputs = outputs[i:i + batch_size]

            # 清空梯度
            optimizer.zero_grad()

            # 前向传播
            predictions = model(batch_inputs)

            # 计算损失
            loss = criterion(predictions, batch_outputs)
            
            # 反向传播
            loss.backward()
            optimizer.step()

    # 保存增量训练后的模型
    torch.save(model.state_dict(), "../models/glucose_fnn.pth")
    print("Incremental training completed and model saved.")

# 预测餐后血糖
def predict_glucose(pre_meal_glucose, carb, fat, fiber, insulin, model, scaler):
    """
    预测餐后血糖
    :param pre_meal_glucose: 餐前血糖
    :param carb: 碳水化合物
    :param fat: 脂肪
    :param fiber: 纤维
    :param insulin: 胰岛素量
    :param model: 已训练的 FNN 模型
    :param scaler: 数据标准化器
    :return: 预测的餐后血糖（60min、120min、180min）
    """
    # 输入数据
    inputs = np.array([[pre_meal_glucose, carb, fat, fiber, insulin]])
    
    # 标准化
    inputs = scaler.transform(inputs)
    inputs = torch.tensor(inputs, dtype=torch.float32)

    # 预测
    with torch.no_grad():
        predicted_glucose = model(inputs).numpy()[0]
    
    return predicted_glucose
