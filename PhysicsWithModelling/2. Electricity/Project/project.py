import numpy as np
import matplotlib.pyplot as plt

# Константы и параметры
k = 1  # Условная константа кулоновской силы
charge_magnitude = 1  # Модуль заряда (в безразмерной форме)
grid_size = 100 
grid_range = 2.0 
epsilon = 1e-2  # Точность для завершения итераций
max_steps = 5  # Максимальное количество шагов

# Координаты и значения зарядов
charges = [
    {"x": -0.5, "y": -0.5, "q": charge_magnitude},
    {"x": 0.5, "y": -0.5, "q": -charge_magnitude},
    {"x": -0.5, "y": 0.5, "q": -charge_magnitude},
    {"x": 0.5, "y": 0.5, "q": charge_magnitude},
]

x = np.linspace(-grid_range, grid_range, grid_size)
y = np.linspace(-grid_range, grid_range, grid_size)
X, Y = np.meshgrid(x, y)

# Вычисление потенциала (эквипотенциальные поверхности)
phi = np.zeros(X.shape)
for charge in charges:
    dx = X - charge["x"]
    dy = Y - charge["y"]
    r = np.sqrt(dx**2 + dy**2)
    r[r < 0.1] = 0.1
    phi += k * charge["q"] / r

for step in range(max_steps):
    phi_old = phi.copy()
    # Обновление значений потенциала
    for i in range(1, grid_size - 1):
        for j in range(1, grid_size - 1):
            if not any(np.isclose([X[i, j], Y[i, j]], [charge["x"], charge["y"]], atol=0.1).all() for charge in charges):
                phi[i, j] = 0.25 * (phi[i+1, j] + phi[i-1, j] + phi[i, j+1] + phi[i, j-1])
    diff = np.max(np.abs(phi - phi_old))
    print(f"Шаг {step + 1}, изменение потенциала: {diff:.4e}")
    if diff < epsilon:
        print(f"Сходимость достигнута на шаге {step + 1}")
        break
else:
    print("Максимальное количество шагов достигнуто.")

# Вычисление напряженности поля
Ex = np.zeros(X.shape)
Ey = np.zeros(Y.shape)
for charge in charges:
    dx = X - charge["x"]
    dy = Y - charge["y"]
    r = np.sqrt(dx**2 + dy**2)
    r[r < 0.1] = 0.1  # Предотвращение деления на 0
    Ex += k * charge["q"] * dx / r**3
    Ey += k * charge["q"] * dy / r**3

E_magnitude = np.sqrt(Ex**2 + Ey**2)
Ex_normalized = Ex / E_magnitude
Ey_normalized = Ey / E_magnitude

plt.figure(figsize=(8, 6))
plt.contour(X, Y, phi, levels=50, cmap="coolwarm", alpha=0.75)
plt.streamplot(X, Y, Ex_normalized, Ey_normalized, color=E_magnitude, cmap="viridis", density=1)
for charge in charges:
    color = 'red' if charge["q"] > 0 else 'blue'
    plt.plot(charge["x"], charge["y"], 'o', color=color, markersize=10)
plt.title("Силовые линии и эквипотенциальные поверхности")
plt.xlabel("x (безразмерные координаты)")
plt.ylabel("y (безразмерные координаты)")
plt.colorbar(label="Потенциал / Напряженность")
plt.axis("equal")
plt.grid(True)
plt.show()
