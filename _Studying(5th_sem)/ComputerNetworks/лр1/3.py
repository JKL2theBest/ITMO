import numpy as np
import matplotlib.pyplot as plt
import itertools

# --- Исходные данные и скремблирование ---

# Исходное полное сообщение в бинарном виде (14 байт)
binary_message = (
    "11010001" "11110011" "11110101" "11100000"
    "11101101" "11101010" "11110011" "11101011"
    "11101000" "11100101" "11100010" "00100000"
    "11001100" "00101110"
)

# Функция скремблирования: Bi = Ai ⊕ B(i-3) ⊕ B(i-5)
def scramble(message):
    scrambled_list = []
    for i in range(len(message)):
        input_bit = int(message[i])
        prev_bit_3 = scrambled_list[i - 3] if i >= 3 else 0
        prev_bit_5 = scrambled_list[i - 5] if i >= 5 else 0
        output_bit = input_bit ^ prev_bit_3 ^ prev_bit_5
        scrambled_list.append(output_bit)
    return ''.join(map(str, scrambled_list))

# Выполняем скремблирование
scrambled_message = scramble(binary_message)
print("--- РЕЗУЛЬТАТ СКРЕМБЛИРОВАНИЯ ---")
print("Бинарная последовательность:")
print(scrambled_message)
print("-" * 40)

# --- Построение графиков и расчеты ---

# Параметры сигнала
C = 1e9
T_bit = 1 / C

# Берем первые 4 байта (32 бита) для графиков
first4_bytes_scrambled = scrambled_message[:32]

# Вспомогательная функция для графиков
def plot_signal(time, signal, title, bits=None):
    plt.figure(figsize=(14, 3))
    plt.step(time, signal, where='post', linewidth=1.5)
    plt.ylim(-1.5, 1.5)
    plt.xlim(time[0], time[-1])
    plt.title(title)
    plt.xlabel('Время (нс)')
    plt.ylabel('Уровень сигнала')
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    if bits is not None:
        T_ns = T_bit * 1e9
        for i, b in enumerate(bits):
            plt.text((i + 0.5) * T_ns, 1.2, b, ha='center', va='bottom', fontsize=8, color='blue')
    plt.show()

# --- 1. Манчестерский код ---
manchester = []
for bit in first4_bytes_scrambled:
    manchester.extend([-1, 1] if bit == '1' else [1, -1])
t_m = np.cumsum([0] + [T_bit / 2] * len(first4_bytes_scrambled) * 2)[1:] * 1e9
plot_signal(t_m, manchester, "Манчестер (скремблированный код)", bits=first4_bytes_scrambled)

f_v_man, f_n_man = C, C / 2
print(f"Манчестер (скрембл.): f_в={f_v_man/1e6:.1f} МГц, f_н={f_n_man/1e6:.1f} МГц, S={(f_v_man - f_n_man)/1e6:.1f} МГц")
print("-" * 40)

# --- 2. AMI код ---
ami = []
last = -1
for bit in first4_bytes_scrambled:
    if bit == '0':
        ami.append(0)
    else:
        last *= -1
        ami.append(last)
t_ami = np.linspace(0, len(first4_bytes_scrambled) * T_bit, len(first4_bytes_scrambled) + 1) * 1e9
plot_signal(t_ami, [ami[0]] + ami, "AMI (скремблированный код)", bits=first4_bytes_scrambled)

# Ищем самую длинную серию нулей во ВСЕЙ последовательности
N_scrambled = max(len(list(g)) for k, g in itertools.groupby(scrambled_message) if k == '0')

f_v_ami = C / 2
f_n_ami = C / (2 * N_scrambled)
S_ami = f_v_ami - f_n_ami
print(f"AMI (скрембл., N={N_scrambled}): f_в={f_v_ami/1e6:.1f} МГц, f_н={f_n_ami/1e6:.1f} МГц, S={S_ami/1e6:.1f} МГц")
print("-" * 40)