import numpy as np
import matplotlib.pyplot as plt
import itertools

# Функция для поиска самой длинной последовательности одинаковых битов
def find_longest_run(bits_string):
    return max(len(list(g)) for k, g in itertools.groupby(bits_string))

# Первые 4 байта исходного сообщения
data_bytes = [0xD1, 0xF3, 0xF5, 0xE0]

# Перевод в двоичный вид
data_bits = ''.join(f'{byte:08b}' for byte in data_bytes)
print("Бинарное представление:", data_bits)
print("-" * 30)

# Параметры
C = 1e9  # пропускная способность канала, Гц
T_bit = 1 / C  # длительность одного бита, с

# --- Вспомогательные функции для графиков (без изменений) ---
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
        for i, b in enumerate(bits):
            T_ns = T_bit * 1e9
            plt.text((i + 0.5) * T_ns, 1.2, b, ha='center', va='bottom', fontsize=8, color='blue')
    plt.show()

def make_time(len_signal, step):
    return np.cumsum([0] + [step] * len_signal)[1:]

# 1. Манчестерский код
manchester = []
for bit in data_bits:
    manchester.extend([-1, 1] if bit == '1' else [1, -1])
t_m = make_time(len(data_bits) * 2, T_bit / 2) * 1e9
plot_signal(t_m, manchester, "Манчестерский код", bits=data_bits)

f_v, f_n = C, C / 2
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(f"Манчестер: f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц")
print("-" * 30)

# 2. NRZ
nrz = [1 if b == '1' else -1 for b in data_bits]
t_nrz = np.linspace(0, len(data_bits) * T_bit, len(data_bits) + 1) * 1e9
plot_signal(t_nrz, [nrz[0]] + nrz, "NRZ код", bits=data_bits)

# <<< ИСПРАВЛЕНО: Расчет f_н на основе реальных данных (N=5)
N_nrz = find_longest_run(data_bits) # N=5 для '00000'
f_v = C / 2
f_n = C / (2 * N_nrz)
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(f"NRZ (N={N_nrz}): f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц")
print("-" * 30)


# 3. RZ
rz = []
for bit in data_bits:
    rz.extend([1, 0] if bit == '1' else [-1, 0])
t_rz = make_time(len(data_bits) * 2, T_bit / 2) * 1e9
plot_signal(t_rz, rz, "RZ код", bits=data_bits)

f_v, f_n = C, C / 4
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(f"RZ: f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц")
print("-" * 30)

# 4. AMI
ami = []
last = -1
for bit in data_bits:
    if bit == '0':
        ami.append(0)
    else:
        last *= -1
        ami.append(last)
t_ami = np.linspace(0, len(data_bits) * T_bit, len(data_bits) + 1) * 1e9
plot_signal(t_ami, [ami[0]] + ami, "AMI код", bits=data_bits)

# <<< ИСПРАВЛЕНО: Расчет f_н на основе самой длинной серии нулей (N=5)
N_ami = max(len(list(g)) for k, g in itertools.groupby(data_bits) if k == '0')
f_v = C / 2
f_n = C / (2 * N_ami)
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(f"AMI (N={N_ami}): f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц")
print("-" * 30)

# 5. NRZI
nrzi = []
prev = 1
for bit in data_bits:
    if bit == '1':
        prev *= -1
    nrzi.append(prev)
t_nrzi = np.linspace(0, len(data_bits) * T_bit, len(data_bits) + 1) * 1e9
plot_signal(t_nrzi, [nrzi[0]] + nrzi, "NRZI код", bits=data_bits)

# <<< ИСПРАВЛЕНО: Расчет f_н на основе самой длинной серии нулей (N=5)
N_nrzi = max(len(list(g)) for k, g in itertools.groupby(data_bits) if k == '0')
f_v = C / 2
f_n = C / (2 * N_nrzi)
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(f"NRZI (N={N_nrzi}): f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц")
print("-" * 30)