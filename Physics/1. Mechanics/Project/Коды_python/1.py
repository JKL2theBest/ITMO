import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

n = 500  # Число частиц
dh = .02  # Параметр случайного распределения

# Задание вектор-столбцов координат точек
y = np.arange(1, n+1)
x = np.zeros(n)

fig, ax = plt.subplots()
ax.set_xlim([-2, 2])
ax.set_ylim([0, n+1])
h, = ax.plot(x, y, 'k.')  # Вывод начального положения точек

# Флаг для управления паузой
is_paused = False

def update(frame):
    global x
    if not is_paused:
        x = x + dh * (2 * np.random.rand(n) - 1)  # Случайные смещения x-координаты каждой точки
        h.set_xdata(x)  # Смена координат точек на рисунке
    return h,

def onClick(event):
    global is_paused
    is_paused ^= True

fig.canvas.mpl_connect('button_press_event', onClick)

ani = animation.FuncAnimation(fig, update, frames=range(1000), interval=50, blit=True)  

plt.show()
