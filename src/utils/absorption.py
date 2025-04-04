import numpy as np
import matplotlib.pyplot as plt

# 吸收模型的参数和初始化
def absorption_model(carbs, lipids, proteins, fiber, GI):
    # 常数定义
    CHOAvail = 0.76  # 仅在部分食物中有效的常数
    
    # 初始状态（假设每个营养素在时间0时刻为0）
    sProteins = 0
    sLipids = 0
    sFibers = 0
    sMonosac = 0
    sStarchGI = 0

    # 记录时间和吸收过程
    time_steps = 100  # 假设100个时间步长
    proteins_arr = []
    lipids_arr = []
    fibers_arr = []
    monosac_arr = []
    starch_arr = []
    
    # 吸收模型的迭代
    for t in range(time_steps):
        # 计算每个营养素在当前时刻的变化（Δm表示增加的量，Δe表示被吸收的量）
        # 假设吸收速率随着时间变化，且食物成分的影响不同
        ΔmProteins = proteins * 0.1  # 假设蛋白质吸收速率为10%
        ΔeProteins = ΔmProteins * 0.1  # 假设10%的蛋白质被吸收

        ΔmLipids = lipids * 0.05  # 脂肪吸收速率为5%
        ΔeLipids = ΔmLipids * 0.05  # 5%的脂肪被吸收

        ΔmFibres = fiber * 0.02  # 纤维吸收速率为2%
        ΔeFibres = ΔmFibres * 0.02  # 2%的纤维被吸收

        ΔmMonosac = carbs * 0.5  # 假设一半碳水化合物进入血糖
        ΔeMonosac = ΔmMonosac * 0.6  # 60%被吸收

        # 使用GI影响淀粉吸收
        ΔmMonosacGI = carbs * GI * 0.1  # GI对吸收的影响
        ΔeStarchGI = ΔmMonosacGI * 0.3  # 30%被吸收
        
        # 更新吸收量
        sProteins += ΔmProteins - ΔeProteins
        sLipids += ΔmLipids - ΔeLipids
        sFibers += ΔmFibres - ΔeFibres
        sMonosac += ΔmMonosac - ΔeMonosac
        sStarchGI += ΔmMonosacGI - ΔeStarchGI

        # 记录每个时间步的吸收情况
        proteins_arr.append(sProteins)
        lipids_arr.append(sLipids) 
        fibers_arr.append(sFibers)
        monosac_arr.append(sMonosac)
        starch_arr.append(sStarchGI)

    return np.array(proteins_arr), np.array(lipids_arr), np.array(fibers_arr), np.array(monosac_arr), np.array(starch_arr)

# 选择一些测试的食物成分和GI（这是示例数据）
carbs = 30  # 30克碳水化合物
lipids = 10  # 10克脂肪
proteins = 20  # 20克蛋白质
fiber = 5  # 5克纤维
GI = 75  # 假设GI为75

# 运行吸收模型
proteins_arr, lipids_arr, fibers_arr, monosac_arr, starch_arr = absorption_model(carbs, lipids, proteins, fiber, GI)

# 画出吸收曲线
time = np.arange(100)
plt.figure(figsize=(10, 6))
plt.plot(time, proteins_arr, label='Proteins')
plt.plot(time, lipids_arr, label='Lipids')
plt.plot(time, fibers_arr, label='Fibers')
plt.plot(time, monosac_arr, label='Monosaccharides')
plt.plot(time, starch_arr, label='Starch GI')
plt.xlabel('Time (minutes)')
plt.ylabel('Absorption (g)')
plt.title('Absorption Curves for Different Nutrients')
plt.legend()
plt.show()

# 提取特征 p1, p2, p3
p1 = np.argmax(monosac_arr)  # 峰值时间
p2 = np.argmax(monosac_arr > 0.5 * monosac_arr.max())  # 达到峰值50%的时间
p3 = monosac_arr.max()  # 最大吸收速率

print(f"Time to peak (p1): {p1} minutes")
print(f"Time to 50% peak (p2): {p2} minutes")
print(f"Maximum absorption rate (p3): {p3} g/min")
