# File: load_balancer.py
# Jalankan di salah satu server (misalnya server1)

import socket
import threading
import time
import json
import os

# Konfigurasi
SERVER_PORT = 8000
SERVERS = [
    {"host": "IP_SERVER1", "port": 8080, "status": True},
    {"host": "IP_SERVER2", "port": 8080, "status": True},
    {"host": "IP_SERVER3", "port": 8080, "status": True},
    {"host": "IP_SERVER4", "port": 8080, "status": True}
]

# Ganti IP_SERVER1, IP_SERVER2, dll dengan IP sebenarnya dari VM Anda
# Contoh: "192.168.1.101", "192.168.1.102", dst.

# Fungsi untuk memeriksa status server
def check_server_status():
    while True:
        for i, server in enumerate(SERVERS):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((server["host"], server["port"]))
                    s.send(b"STATUS")
                    response = s.recv(1024)
                    if response == b"OK":
                        SERVERS[i]["status"] = True
                    else:
                        SERVERS[i]["status"] = False
            except Exception:
                SERVERS[i]["status"] = False
                
            print(f"Server {server['host']}:{server['port']} status: {'UP' if SERVERS[i]['status'] else 'DOWN'}")
        
        # Tulis status ke file untuk monitoring
        with open("server_status.json", "w") as f:
            json.dump(SERVERS, f)
            
        time.sleep(5)  # Periksa setiap 5 detik

# Fungsi untuk menangani koneksi client
def handle_client(client_socket):
    try:
        # Temukan server aktif
        active_servers = [server for server in SERVERS if server["status"]]
        
        if not active_servers:
            client_socket.send(b"HTTP/1.1 503 Service Unavailable\r\n\r\nSemua server sedang tidak tersedia.")
            client_socket.close()
            return
        
        # Implementasi Round Robin sederhana
        # Baca indeks server terakhir
        last_server_index = 0
        if os.path.exists("last_server.txt"):
            with open("last_server.txt", "r") as f:
                last_server_index = int(f.read().strip())
        
        # Pilih server berikutnya yang aktif
        server_index = (last_server_index + 1) % len(active_servers)
        selected_server = active_servers[server_index]
        
        # Simpan indeks untuk penggunaan berikutnya
        with open("last_server.txt", "w") as f:
            f.write(str(server_index))
        
        # Kirim permintaan ke server yang dipilih
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.connect((selected_server["host"], selected_server["port"]))
            
            # Terima request dari client
            data = client_socket.recv(4096)
            if not data:
                client_socket.close()
                return
                
            # Teruskan request ke server
            server_socket.send(data)
            
            # Terima response dari server
            response = b""
            while True:
                chunk = server_socket.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            # Kirim response ke client
            client_socket.send(response)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Fungsi utama
def main():
    # Mulai thread untuk memeriksa status server
    status_thread = threading.Thread(target=check_server_status, daemon=True)
    status_thread.start()
    
    # Buat socket server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', SERVER_PORT))
    server.listen(5)
    
    print(f"Load balancer listening on port {SERVER_PORT}")
    
    try:
        while True:
            client_socket, client_address = server.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            
            # Buat thread baru untuk menangani koneksi
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down load balancer")
    finally:
        server.close()

if __name__ == "__main__":
    main()