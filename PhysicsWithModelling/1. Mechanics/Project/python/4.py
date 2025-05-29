import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Инициализация параметров
n = 500
steps = 1000  # Число шагов
dh = 0.02
x = np.zeros(n)
y = np.zeros(n)

# Создание фигуры и осей для анимации
fig, axs = plt.subplots(2, 1)

# Настройка осей для анимации
axs[0].set_xlim([-2, 2])
axs[0].set_ylim([-2, 2])
h1 = axs[0].scatter(x, y, color='k') 

# Цикл для анимации
for i in range(steps):
    dx = dh * (2 * np.random.rand(n) - 1)
    dy = dh * (2 * np.random.rand(n) - 1)
    x = x + dx
    y = y + dy
    h1.set_offsets(np.c_[x, y]) 
    plt.pause(0.01) 

# Вычисление расстояния от начала координат R
R = np.sqrt(x**2 + y**2)

# Настройка осей для гистограммы
Rmin = np.min(R); Rmax = np.max(R)
R_values = np.linspace(Rmin, Rmax, 100)
f = R_values / (np.sqrt(2*np.pi*n*dh**2)) * np.exp(-R_values**2 / (2*n*dh**2))  # Теоретическая функция
axs[1].hist(R, bins=30, range=(Rmin, Rmax), density=True) 
axs[1].plot(R_values, f, 'r')  # Распределение Гаусса
axs[1].set_xlim([Rmin, Rmax])
axs[1].set_ylim([0, 1])

plt.tight_layout()
plt.show()
