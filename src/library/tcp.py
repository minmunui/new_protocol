import socket
import threading


class TCPServer:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        # INET은 IPv4를 의미 SOCK_STREAM은 TCP를 의미
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Socket의 옵션을 설정
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []

    def start(self):
        self.server_socket.bind((self.host, self.port))
        # TCP의 경우 LISTEN이 필요, UDP의 경우 필요없음
        self.server_socket.listen(5)
        print(f"TCP 서버가 {self.host}:{self.port}에서 시작되었습니다.")

        while True:
            client_socket, addr = self.server_socket.accept()
            self.clients.append(client_socket)
            print(f"TCP 클라이언트가 연결되었습니다: {addr}")

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, addr)
            )
            client_thread.start()

    def handle_client(self, client_socket, addr):
        try:
            while True:
                # 최대로 받을 데이터
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode('utf-8')
                print(f"TCP 수신 ({addr}): {message}")

                response = f"TCP 서버 응답: {message}"
                client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"TCP 클라이언트 처리 중 오류 발생: {e}")
        finally:
            self.clients.remove(client_socket)
            client_socket.close()
            print(f"TCP 클라이언트 연결이 종료되었습니다: {addr}")

    def stop(self):
        for client in self.clients:
            client.close()
        self.server_socket.close()
        print("TCP 서버가 종료되었습니다.")


class TCPClient:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"TCP 서버에 연결되었습니다: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"TCP 서버 연결 실패: {e}")
            return False

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(f"TCP 서버 응답: {response}")
            return response
        except Exception as e:
            print(f"TCP 메시지 송수신 중 오류 발생: {e}")
            return None

    def disconnect(self):
        self.client_socket.close()
        print("TCP 서버와의 연결이 종료되었습니다.")
