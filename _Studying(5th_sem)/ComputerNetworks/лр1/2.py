import numpy as np
import matplotlib.pyplot as plt

# --- Входные данные и таблица 4B/5B ---
hex_message = "D1F3F5E0"
table_4b5b = {
    "0000": "11110",
    "0001": "01001",
    "0010": "10100",
    "0011": "10101",
    "0100": "01010",
    "0101": "01011",
    "0110": "01110",
    "0111": "01111",
    "1000": "10010",
    "1001": "10011",
    "1010": "10110",
    "1011": "10111",
    "1100": "11010",
    "1101": "11011",
    "1110": "11100",
    "1111": "11101",
}


# --- Функции кодирования ---
def hex_to_bin(hex_msg):
    return "".join([bin(int(c, 16))[2:].zfill(4) for c in hex_msg])


def encode_4b5b(binary_msg):
    return "".join(
        table_4b5b[binary_msg[i : i + 4]] for i in range(0, len(binary_msg), 4)
    )


# --- Основной процесс кодирования ---
binary_message = hex_to_bin(hex_message)
encoded_message = encode_4b5b(binary_message)
print("Исходное (bin):", binary_message)
print("4B/5B закодированное (bin):", encoded_message)
print("-" * 30)

# --- Параметры сигнала ---
C = 1e9  # Исходная скорость передачи данных
C_prime = C * (5 / 4)  # <<< ИСПРАВЛЕНО: Требуемая тактовая частота передатчика
T_bit_prime = 1 / C_prime


# --- Вспомогательные функции для графиков (без изменений) ---
def plot_signal(time, signal, title, bits=None):
    plt.figure(figsize=(14, 3))
    plt.step(time, signal, where="post", linewidth=1.5)
    plt.ylim(-1.5, 1.5)
    plt.xlim(time[0], time[-1])
    plt.title(title)
    plt.xlabel("Время (нс)")
    plt.ylabel("Уровень сигнала")
    plt.grid(True, which="both", linestyle="--", alpha=0.7)
    if bits is not None:
        for i, b in enumerate(bits):
            T_ns = T_bit_prime * 1e9
            plt.text(
                (i + 0.5) * T_ns,
                1.2,
                b,
                ha="center",
                va="bottom",
                fontsize=7,
                color="blue",
            )
    plt.show()


def make_time(len_signal, step):
    return np.cumsum([0] + [step] * len_signal)[1:]


# --- Манчестер ---
manchester = [-1, 1] * len(encoded_message)
for i, bit in enumerate(encoded_message):
    if bit == "0":
        manchester[2 * i : 2 * i + 2] = [1, -1]
t_m = make_time(len(encoded_message) * 2, T_bit_prime / 2) * 1e9
plot_signal(t_m, manchester, "Манчестер (4B/5B)", bits=encoded_message)

# <<< ИСПРАВЛЕНО: Расчет частот для Манчестера с учетом C_prime
f_v, f_n = C_prime, C_prime / 2
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(
    f"Манчестер (4B/5B): f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц"
)
print("-" * 30)


# --- AMI ---
ami = []
last = -1
for bit in encoded_message:
    if bit == "0":
        ami.append(0)
    else:
        last *= -1
        ami.append(last)
t_ami = (
    np.linspace(0, len(encoded_message) * T_bit_prime, len(encoded_message) + 1) * 1e9
)
plot_signal(t_ami, [ami[0]] + ami, "AMI (4B/5B)", bits=encoded_message)

# <<< ИСПРАВЛЕНО: Расчет частот для AMI с учетом C_prime и свойства 4B/5B (N=3)
N_4b5b = 3  # Гарантированное максимальное число нулей подряд
f_v = C_prime / 2
f_n = C_prime / (2 * N_4b5b)
f_sr = (f_v + f_n) / 2
S = f_v - f_n
print(
    f"AMI (4B/5B, N={N_4b5b}): f_в={f_v/1e6:.1f} МГц, f_н={f_n/1e6:.1f} МГц, f_ср={f_sr/1e6:.1f} МГц, S={S/1e6:.1f} МГц"
)
print("-" * 30)
