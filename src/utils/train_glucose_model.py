import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import joblib

# 导入数据
df = pd.read_csv('D:\\SCU\\diabetes_diet_recommendation\\data\\glucose.csv')

# 数据预处理
X = df[['碳水 (g)', '脂肪 (g)', '膳食纤维 (g)', '餐前血糖 (mmol/L)']].values
y = df[['餐后60分钟血糖 (mmol/L)', '餐后120分钟血糖 (mmol/L)', '餐后180分钟血糖 (mmol/L)']].values

scaler_X = StandardScaler()
X_scaled = scaler_X.fit_transform(X)

scaler_y = StandardScaler()
y_scaled = scaler_y.fit_transform(y)

# 保存 scaler 对象到文件
joblib.dump(scaler_X, 'D:\\SCU\\diabetes_diet_recommendation\\models\\scaler_X.pkl')
joblib.dump(scaler_y, 'scaler_y.pkl')

# X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.2, random_state=42)

# # 构建FNN模型
# model = Sequential()
# model.add(Dense(64, input_dim=4, activation='relu'))
# for _ in range(11):
#     model.add(Dense(64, activation='relu'))
# model.add(Dense(3, activation='linear'))

# # 编译模型
# model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')

# # 训练模型
# history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2, verbose=1)

# # 保存模型
# model.save('D:\\SCU\\diabetes_diet_recommendation\\models\\glucose_model_P1.h5')

# 保存测试集预测结果到CSV文件
def save_predictions(model, X_test, y_test, scaler_y, output_file):
    """
    使用训练好的模型对测试集进行预测，并将预测结果与实际结果保存到CSV文件。
    
    参数:
    model: 已训练的Keras模型
    X_test: 测试集输入数据
    y_test: 测试集实际输出数据
    scaler_y: 用于逆标准化输出数据的标准化器
    output_file: 输出CSV文件的路径
    """
    # 使用模型进行预测
    y_pred_scaled = model.predict(X_test)
    
    # 对预测结果进行逆标准化
    y_pred_original = scaler_y.inverse_transform(y_pred_scaled)
    y_test_original = scaler_y.inverse_transform(y_test)

    # 计算MSE
    mse = mean_squared_error(y_test_original, y_pred_original)

    # 将预测结果与实际结果合并
    results = pd.DataFrame({
        '实际餐后60分钟血糖': y_test_original[:, 0],
        '实际餐后120分钟血糖': y_test_original[:, 1],
        '实际餐后180分钟血糖': y_test_original[:, 2],
        '预测餐后60分钟血糖': y_pred_original[:, 0],
        '预测餐后120分钟血糖': y_pred_original[:, 1],
        '预测餐后180分钟血糖': y_pred_original[:, 2],
    })

    # 保存到CSV文件
    results.to_csv(output_file, index=False)

    print(f"预测结果和MSE已保存到: {output_file}")

# 使用训练好的模型对测试集进行预测，并保存结果
save_predictions(model, X_test, y_test, scaler_y, 'D:\\SCU\\diabetes_diet_recommendation\\data\\test_predictions.csv')
