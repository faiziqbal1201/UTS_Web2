# File: web_server.py
# Jalankan di setiap server (server1, server2, server3, server4)

import socket
import threading
import os
import time

# Konfigurasi
SERVER_PORT = 8080
WEB_ROOT = "/var/www/html"  # Direktori root untuk file web

# Fungsi untuk membaca file
def read_file(path):
    try:
        with open(path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        return None

# Fungsi untuk menguraikan request HTTP
def parse_request(request):
    lines = request.decode('utf-8').split('\r\n')
    if not lines:
        return None
    
    request_line = lines[0].split()
    if len(request_line) < 2:
        return None
    
    method, path = request_line[0], request_line[1]
    
    # Tangani path
    if path == '/':
        path = '/index.html'
    
    return method, path

# Fungsi untuk menangani koneksi client
def handle_client(client_socket):
    try:
        # Terima request dari client
        request_data = client_socket.recv(4096)
        
        # Jika request adalah perintah khusus untuk cek status
        if request_data == b"STATUS":
            client_socket.send(b"OK")
            client_socket.close()
            return
        
        # Parse request
        request_info = parse_request(request_data)
        if not request_info:
            # Kirim error 400 - Bad Request
            response = b"HTTP/1.1 400 Bad Request\r\n\r\n<h1>400 Bad Request</h1>"
            client_socket.send(response)
            return
        
        method, path = request_info
        
        # Gabungkan dengan root directory
        file_path = os.path.join(WEB_ROOT, path.lstrip('/'))
        
        # Baca file
        content = read_file(file_path)
        
        if content is None:
            # Kirim error 404 - Not Found
            response = b"HTTP/1.1 404 Not Found\r\n\r\n<h1>404 Not Found</h1>"
        else:
            # Tentukan content type berdasarkan ekstensi file
            content_type = "text/html"  # Default
            if file_path.endswith('.css'):
                content_type = "text/css"
            elif file_path.endswith('.js'):
                content_type = "application/javascript"
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                content_type = "image/jpeg"
            elif file_path.endswith('.png'):
                content_type = "image/png"
            
            # Kirim response
            response = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n".encode()
            response += content
        
        client_socket.send(response)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Fungsi utama
def main():
    # Buat socket server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', SERVER_PORT))
    server.listen(5)
    
    hostname = socket.gethostname()
    server_ip = socket.gethostbyname(hostname)
    print(f"Web server running on {server_ip}:{SERVER_PORT}")
    
    # Buat direktori root jika belum ada
    os.makedirs(WEB_ROOT, exist_ok=True)
    
    # Buat file index.html jika belum ada
    index_path = os.path.join(WEB_ROOT, "index.html")
    if not os.path.exists(index_path):
        with open(index_path, 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Server {hostname}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                </style>
            </head>
            <body>
                <h1>Selamat Datang di Server {hostname}</h1>
                <p>Ini adalah halaman web yang dijalankan pada server {hostname} dengan IP {server_ip}.</p>
                <p>Waktu server: <span id="server-time">{time.strftime('%Y-%m-%d %H:%M:%S')}</span></p>
            </body>
            </html>
            """)
    
    try:
        while True:
            client_socket, client_address = server.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            
            # Buat thread baru untuk menangani koneksi
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down web server")
    finally:
        server.close()

if __name__ == "__main__":
    main()