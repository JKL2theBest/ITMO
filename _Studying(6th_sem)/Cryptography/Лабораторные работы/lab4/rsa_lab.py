import random

print("ОТЧЕТ: ПРОГРАММНАЯ РЕАЛИЗАЦИЯ RSA С МОДИФИКАЦИЯМИ")
print("=" * 50)

# БАЗОВЫЕ МАТЕМАТИЧЕСКИЕ ФУНКЦИИ


def extended_gcd(a, b):
    """Расширенный алгоритм Евклида (нужен для поиска приватного ключа d)"""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y


def mod_inverse(e, phi):
    """Поиск мультипликативного обратного (e * d = 1 mod phi)"""
    gcd, x, y = extended_gcd(e, phi)
    if gcd != 1:
        raise Exception("Обратного элемента не существует")
    return x % phi


def is_prime(n, k=5):
    """Тест Миллера-Рабина на простоту"""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits):
    """Генерация простого числа заданной битовой длины"""
    while True:
        num = random.getrandbits(bits)
        # Устанавливаем старший и младший биты в 1 (чтобы число было нечетным и нужной длины)
        num |= (1 << bits - 1) | 1
        if is_prime(num):
            return num


# МОДИФИКАЦИЯ 1: Защита от метода факторизации Ферма
def generate_keypair(bits):
    print(f"\n[Генерация ключей {bits*2} бит...]")
    e = 65537  # Стандартная открытая экспонента

    while True:
        p = generate_prime(bits)
        q = generate_prime(bits)

        # ЗАЩИТА: p и q не должны быть слишком близки друг к другу!
        # Если они близки, модуль N легко раскладывается методом Ферма.
        diff = abs(p - q)
        if diff > (1 << (bits // 2)):  # Разница должна быть существенной
            break
        else:
            print("Сработала защита: p и q слишком близки. Перегенерация...")

    n = p * q
    phi = (p - 1) * (q - 1)
    d = mod_inverse(e, phi)

    print(f"p = {p}")
    print(f"q = {q}")
    print(f"Открытый ключ (e, n): ({e}, {n})")
    print(f"Закрытый ключ d: {d}")

    return ((e, n), (d, n), (p, q))


# МОДИФИКАЦИЯ 2: Быстрое возведение в степень
def fast_mod_exp(base, exp, mod):
    """
    Алгоритм Square-and-Multiply (Возведение в квадрат и умножение).
    Ускоряет вычисление C = M^e mod N.
    """
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1  # Битовый сдвиг (деление на 2)
        base = (base * base) % mod
    return result


def rsa_encrypt(message, pub_key):
    e, n = pub_key
    # Шифруем число: C = M^e mod n
    print("\n[Шифрование]")
    cipher = fast_mod_exp(message, e, n)
    print(f"Исходное сообщение (M): {message}")
    print(f"Шифротекст (C): {cipher}")
    return cipher


# МОДИФИКАЦИЯ 3: Дешифрование с использованием КТО (Китайской теоремы об остатках)
def rsa_decrypt_crt(ciphertext, priv_key, primes):
    """
    Дешифрование M = C^d mod N занимает много времени.
    С помощью КТО мы разбиваем задачу на две маленькие (по модулю p и q),
    что ускоряет процесс примерно в 4 раза.
    """
    d, n = priv_key
    p, q = primes
    print("\n[Дешифрование с помощью КТО (CRT)]")

    # Предварительные вычисления (обычно хранятся в памяти)
    dp = d % (p - 1)
    dq = d % (q - 1)
    q_inv = mod_inverse(q, p)

    # Шаг 1: Возводим в степень по малым модулям
    m1 = fast_mod_exp(ciphertext, dp, p)
    m2 = fast_mod_exp(ciphertext, dq, q)

    # Шаг 2: Собираем результат через КТО
    h = (q_inv * (m1 - m2)) % p
    m = m2 + h * q

    print(f"Восстановленное сообщение (M): {m}")
    return m


# ТЕСТИРОВАНИЕ СИСТЕМЫ

# Генерируем небольшие ключи (по 256 бит каждый -> RSA 512) для наглядности
public, private, prime_factors = generate_keypair(256)

# Исходное сообщение (представлено как число)
msg = 12345678901234567890

# Прогоняем алгоритм
c = rsa_encrypt(msg, public)
m_decrypted = rsa_decrypt_crt(c, private, prime_factors)

if msg == m_decrypted:
    print("\n[УСПЕХ] Асимметричная система работает корректно!")
