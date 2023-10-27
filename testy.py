# 1. 引入所需的库
import numpy as np
import matplotlib.pyplot as plt

# 2. 创建数据
x = np.linspace(0, 2 * np.pi, 100)  # 创建一个包含100个点的x轴数据，范围从0到2π
y = np.sin(x)  # 计算每个x对应的正弦值

# 3. 绘制图形
plt.plot(x, y, label="正弦曲线")  # 使用plot函数绘制曲线，label参数为曲线的标签

# 4. 设置图形的标题和坐标轴标签
plt.title("正弦曲线图")
plt.xlabel("x轴")
plt.ylabel("y轴")

# 5. 显示图例
plt.legend()

# 6. 显示图形
plt.show()
