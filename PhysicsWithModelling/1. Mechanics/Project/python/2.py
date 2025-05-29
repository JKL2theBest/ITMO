import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Инициализация параметров
n = 500
dh = 0.02
y = np.arange(1, n+1)
x = np.zeros(n)

# Создание фигуры и осей для анимации
fig, axs = plt.subplots(2, 1)

# Настройка осей для анимации
axs[0].set_xlim([-2, 2])
axs[0].set_ylim([0, n+1])
h1, = axs[0].plot(x, y, 'k.') 

# Настройка осей для гистограммы
xmin = -2; xmax = 2
x_values = np.linspace(xmin, xmax, 100)
f = norm.pdf(x_values, 0, np.sqrt(n*dh**2))  # Теоретическая функция
axs[1].plot(x_values, f, 'r')  # Распределение Гаусса
h2 = axs[1].hist(x, bins=30, range=(xmin, xmax), density=True)  # Инициализация гистограммы
axs[1].set_xlim([xmin, xmax])
axs[1].set_ylim([0, 1])

# Флаг для управления паузой
is_paused = False

def onClick(event):
    global is_paused
    is_paused ^= True

fig.canvas.mpl_connect('button_press_event', onClick)

# Бесконечный цикл для анимации
while True:
    if not is_paused:
        x = x + dh * (2 * np.random.rand(n) - 1)
        h1.set_xdata(x)  # Обновление координат точек на рисунке
        axs[1].cla()  # Очистка осей гистограммы
        axs[1].plot(x_values, f, 'r')  # Распределение Гаусса
        axs[1].hist(x, bins=30, range=(xmin, xmax), density=True)  # Обновление данных гистограммы
        axs[1].set_xlim([xmin, xmax])
        axs[1].set_ylim([0, 1])
    plt.pause(0.01)  
