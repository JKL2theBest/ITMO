import socket
import time
import numpy as np
import matplotlib.pyplot as plt

# Функция для проведения одного теста
def run_test(sock_options, num_tests=500, num_messages=250):
    # Создаем сокет
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Устанавливаем параметры сокета
    for option in sock_options:
        if option == 'SO_REUSEADDR':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        elif option == 'SO_KEEPALIVE':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        elif option == 'TCP_NODELAY':
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    # Подключаемся к серверу
    sock.connect(('127.0.0.1', 8080))
    
    # Массив для хранения временных показателей
    times = []

    for _ in range(num_tests):
        start_time = time.time()
        
        # Отправляем несколько сообщений
        for _ in range(num_messages):
            sock.sendall(b"Test message")
            sock.recv(1024)  # Получаем ответ от сервера
        
        end_time = time.time()
        times.append(end_time - start_time)
    
    sock.close()
    
    # Возвращаем среднее время
    return np.mean(times)

# Функция для проведения теста для всех комбинаций параметров
def test_all_combinations():
    socket_options = [
        [],  # Нет опций
        ['SO_REUSEADDR'],
        ['SO_KEEPALIVE'],
        ['TCP_NODELAY'],
        ['SO_REUSEADDR', 'SO_KEEPALIVE'],
        ['SO_REUSEADDR', 'TCP_NODELAY'],
        ['SO_KEEPALIVE', 'TCP_NODELAY'],
        ['SO_REUSEADDR', 'SO_KEEPALIVE', 'TCP_NODELAY']
    ]
    
    results = []
    
    for options in socket_options:
        avg_time = run_test(options)
        print(f"Тест для {options}: {avg_time * 1000:.2f} ms")
        results.append(avg_time)
    
    return results, [str(opt) for opt in socket_options]

# Функция для построения графика
def plot_results(results, labels):
    plt.figure(figsize=(10, 6))
    plt.bar(labels, [result * 1000 for result in results], color='blue')
    plt.ylabel('Время (мс)')
    plt.title('Среднее время передачи данных для разных настроек сокетов')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    results, labels = test_all_combinations()
    plot_results(results, labels)
