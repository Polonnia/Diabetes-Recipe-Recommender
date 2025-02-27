import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 自定义数据集类
class GlucoseDataset(Dataset):
    def __init__(self, data, targets):
        self.data = data
        self.targets = targets

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.targets[idx]

# 血糖预测模型
class GlucosePredictor(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(GlucosePredictor, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# 数据预处理
def preprocess_data(data_path):
    # 加载数据
    data = pd.read_csv(data_path)
    
    # 假设数据列名为：pre_meal_glucose, carb, fat, fiber, insulin, post_meal_60, post_meal_120, post_meal_180
    features = data[["pre_meal_glucose", "carb", "fat", "fiber", "insulin"]]
    targets = data[["post_meal_60", "post_meal_120", "post_meal_180"]]
    
    # 标准化特征
    scaler = StandardScaler()
    features = scaler.fit_transform(features)
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(features, targets, test_size=0.2, random_state=42)
    
    # 转换为 PyTorch 张量
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train.values, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test.values, dtype=torch.float32)
    
    return X_train, X_test, y_train, y_test, scaler

# 训练模型
def train_model(model, train_loader, criterion, optimizer, num_epochs=50):
    model.train()
    for epoch in range(num_epochs):
        for inputs, targets in train_loader:
            # 前向传播
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            # 反向传播和优化
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}")

# 测试模型
def test_model(model, test_loader):
    model.eval()
    predictions = []
    actuals = []
    with torch.no_grad():
        for inputs, targets in test_loader:
            outputs = model(inputs)
            predictions.extend(outputs.tolist())
            actuals.extend(targets.tolist())
    
    # 计算均方误差
    mse = np.mean((np.array(predictions) - np.array(actuals)) ** 2)
    print(f"Test MSE: {mse:.4f}")

# 保存模型
def save_model(model, path):
    torch.save(model.state_dict(), path)

# 主函数
def main():
    # 数据路径
    data_path = "data/glucose_data.csv"
    
    # 数据预处理
    X_train, X_test, y_train, y_test, scaler = preprocess_data(data_path)
    
    # 创建数据集和数据加载器
    train_dataset = GlucoseDataset(X_train, y_train)
    test_dataset = GlucoseDataset(X_test, y_test)
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
    
    # 初始化模型
    input_size = 5  # 输入特征数量
    hidden_size = 64
    output_size = 3  # 输出为餐后 60、120、180 分钟的血糖
    model = GlucosePredictor(input_size, hidden_size, output_size)
    
    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 训练模型
    train_model(model, train_loader, criterion, optimizer, num_epochs=50)
    
    # 测试模型
    test_model(model, test_loader)
    
    # 保存模型和标准化器
    save_model(model, "models/glucose_predictor.pth")
    import joblib
    joblib.dump(scaler, "models/scaler.pkl")

if __name__ == "__main__":
    main()