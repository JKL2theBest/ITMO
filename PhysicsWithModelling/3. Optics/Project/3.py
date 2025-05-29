import numpy as np
import matplotlib.pyplot as plt
from math import ceil

# --- Глобальные параметры ---
I0 = 1.0
r_max = 2e-3
grid_size = 4000           # Размер изображения
N = 1000                  # Точек по радиусу для I(r)

λ_values = [400e-9, 550e-9, 700e-9]  # Фиолет, зелёный, красный
R_values = [0.5, 2.0, 10.0]

x = np.linspace(-r_max, r_max, grid_size)
y = np.linspace(-r_max, r_max, grid_size)
X, Y = np.meshgrid(x, y)
r_grid = np.sqrt(X**2 + Y**2)

def compute_intensity(λ, R):
    d = r_grid**2 / (2 * R)
    delta = 2 * d + λ / 2
    return I0 * np.cos(np.pi * delta / λ) ** 2

# --- График I(r) для разных λ ---
r = np.linspace(0, r_max, N)
fig1, ax1 = plt.subplots(figsize=(8, 5))
colors = ['purple', 'green', 'red']
for λ, color in zip(λ_values, colors):
    d = r**2 / (2 * R_values[1])  # фиксированный R = 1.0
    delta = 2 * d + λ / 2
    I = I0 * np.cos(np.pi * delta / λ) ** 2
    ax1.plot(r * 1e3, I, label=f"λ = {int(λ*1e9)} нм", color=color)

ax1.set_title("Распределение интенсивности I(r) при разных λ")
ax1.set_xlabel("Радиус r, мм")
ax1.set_ylabel("Интенсивность")
ax1.grid(True)
ax1.legend()

# --- 2D изображения колец Ньютона ---
fig2, axes = plt.subplots(len(λ_values), len(R_values),
                          figsize=(5 * len(R_values), 5 * len(λ_values)),
                          constrained_layout=True)

for i, λ in enumerate(λ_values):
    for j, R in enumerate(R_values):
        I_grid = compute_intensity(λ, R)
        ax = axes[i][j] if len(λ_values) > 1 else axes[j]
        im = ax.imshow(I_grid, cmap='gray',
                       extent=[-r_max * 1e3, r_max * 1e3, -r_max * 1e3, r_max * 1e3])
        ax.set_title(f"λ = {int(λ*1e9)} нм, R = {R:.1f} м")
        ax.set_xlabel("x, мм")
        ax.set_ylabel("y, мм")

plt.suptitle("Интерференционные картины при разных λ и R", fontsize=16)
plt.show()
