import socket
import time

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 8080))
    server_socket.listen(5)
    
    print("Server started...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        
        # Обработка сообщений
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            client_socket.sendall(data)
        
        client_socket.close()

if __name__ == "__main__":
    run_server()
