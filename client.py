import socket

# Koneksi ke load balancer (misalnya IP load balancer = 127.0.0.1)
HOST = '127.0.0.1'
PORT = 8080

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b'Hello, server!')
        data = s.recv(1024)

    print('Dari server:', data.decode())
except Exception as e:
    print(f"Gagal koneksi ke load balancer: {e}")
