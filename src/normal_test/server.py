# server.py
import argparse
import socket
import os
import json
import threading


class TCPFileServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"서버가 {self.host}:{self.port}에서 시작되었습니다.")

        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"클라이언트 {client_address} 연결됨")

                # 각 클라이언트를 별도의 스레드에서 처리
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.start()

            except Exception as e:
                print(f"연결 수락 중 오류 발생: {e}")
                break

        self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        try:
            # 파일 정보 수신
            file_info_data = client_socket.recv(1024).decode()
            file_info = json.loads(file_info_data)
            filename = file_info['filename']
            filesize = file_info['filesize']

            print(f"파일 {filename} ({filesize} bytes) 수신 시작...")

            # 파일 수신 준비 완료 메시지 전송
            client_socket.send("READY".encode())

            # 파일 수신
            received_size = 0
            with open(f"received_{filename}", 'wb') as file:
                while received_size < filesize:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    file.write(data)
                    received_size += len(data)

                    # 진행률 출력
                    progress = (received_size / filesize) * 100
                    print(f"진행률: {progress:.2f}%")

            print(f"파일 {filename} 수신 완료!")
            client_socket.send("SUCCESS".encode())

        except Exception as e:
            print(f"파일 수신 중 오류 발생: {e}")
            client_socket.send("ERROR".encode())

        finally:
            client_socket.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--host", type=str, default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=9999)
    args = parser.parse_args()

    tcp_server = TCPFileServer(args.host, args.port)
    tcp_server.start()