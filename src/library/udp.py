import socket


class LibraryUDPServer:
    def __init__(self, host='127.0.0.1', port=9998):
        self.host = host
        self.port = port
        # DGRAM의 경우 UDP를 사용할 수 있게 함
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        self.running = False

    def start(self):
        self.running = True
        print(f"UDP 서버가 {self.host}:{self.port}에서 시작되었습니다.")

        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                message = data.decode('utf-8')
                print(f"UDP 수신 ({addr}): {message}")

                response = f"UDP 서버 응답: {message}"
                self.server_socket.sendto(response.encode('utf-8'), addr)
            except Exception as e:
                print(f"UDP 데이터 처리 중 오류 발생: {e}")

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("UDP 서버가 종료되었습니다.")
