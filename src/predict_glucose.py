from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model
import joblib

def predict(input_data):
    """
    使用训练好的模型进行预测

    参数:
    model: 已训练的Keras模型
    scaler_X: 已拟合好的输入数据标准化器
    scaler_y: 已拟合好的输出数据标准化器
    input_data: 包含4个输入特征的列表或数组

    返回:
    预测的餐后60分钟、120分钟、180分钟血糖（实际值）
    """
    model = load_model('D:\SCU\diabetes_diet_recommendation\models\glucose_model_P1.h5')
    scaler_X = joblib.load('D:\\SCU\\diabetes_diet_recommendation\\models\\scaler_X.pkl')
    scaler_y = joblib.load('D:\\SCU\\diabetes_diet_recommendation\\models\\scaler_y.pkl')

    # 使用已经拟合好的 scaler 对输入数据进行标准化
    input_scaled = scaler_X.transform([input_data])  # 输入数据需要是一个二维数组

    # 使用模型进行预测
    predicted_scaled = model.predict(input_scaled)

    # 对预测值进行逆标准化
    predicted_original = scaler_y.inverse_transform(predicted_scaled)

    # 返回实际值（逆标准化后的输出）
    return predicted_original[0]  # 返回的是一个包含3个值的数组

if __name__ == "__main__":
    # 示例：使用predict函数
    input_data = [50, 10, 5, 6.0]  # 例如：碳水50g，脂肪10g，膳食纤维5g，餐前血糖6.0 mmol/L

    # 加载训练好的模型
    model = load_model('../models/glucose_model_P1.h5')

    # 加载拟合好的 scaler 对象
    scaler_X = joblib.load('D:\\SCU\\diabetes_diet_recommendation\\models\\scaler_X.pkl')
    scaler_y = joblib.load('D:\\SCU\\diabetes_diet_recommendation\\models\\scaler_y.pkl')

    # 调用预测函数
    predicted_values = predict(model, scaler_X, scaler_y, input_data)

    # 输出预测值
    print(f"预测的餐后血糖（60分钟、120分钟、180分钟）：{predicted_values}")
