import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Инициализация параметров
n = 500
dh = 0.02
y = np.arange(1, n+1)
x = np.zeros(n)

# Массивы для хранения среднего и среднего квадратичного смещения
mean_disp = np.zeros(n)
mean_sq_disp = np.zeros(n)

# Цикл для анимации
for i in range(n):
    x = x + dh * (2 * np.random.rand(n) - 1)
    mean_disp[i] = np.mean(x)  # Среднее смещение
    mean_sq_disp[i] = np.mean(x**2)  # Среднее квадратичное смещение

# Вычисление коэффициентов аппроксимирующих прямых
p1 = linregress(np.arange(n), mean_disp)
p2 = linregress(np.arange(n), mean_sq_disp)

# Построение графиков
fig, axs = plt.subplots(2, 1)

axs[0].plot(np.arange(n), mean_disp, 'b')
axs[0].plot(np.arange(n), p1.intercept + p1.slope*np.arange(n), 'r--')
axs[0].set_title('Среднее смещение')
axs[0].set_xlabel('Шаги')
axs[0].set_ylabel('<x>')

axs[1].plot(np.arange(n), mean_sq_disp, 'b')
axs[1].plot(np.arange(n), p2.intercept + p2.slope*np.arange(n), 'r--')
axs[1].set_title('Среднее квадратичное смещение')
axs[1].set_xlabel('Шаги')
axs[1].set_ylabel('<x^2>')

plt.tight_layout()
plt.show()
