import socket
import time

import logger
from protocol import Protocol, BUFFER_SIZE


class TCP(Protocol):
    def send_file(self, filename: str, host: str, port: int, buffer_size: int, interval: float = 0.0):
        """
        파일을 전송하는 함수입니다. 파일을 읽어서 buffer_size만큼 읽어서 전송합니다.

        Args:
            filename (str): 전송할 파일 이름입니다.
            host (str): 전송할 서버의 주소입니다.
            port (int): 전송할 서버의 포트입니다.
            buffer_size (int): 파일을 읽어올 때 사용할 버퍼의 크기입니다.
            interval (float): 전송 간격입니다.

        Returns:
            list: 손실된 패킷의 seq_number를 반환합니다.
        """
        logger.info(f"TCP로 전송 시작")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        with open(filename, 'rb') as file:
            while True:
                data = file.read(buffer_size)
                if not data:
                    break
                sock.sendall(data)
                time.sleep(interval)

        sock.close()

    def start_server(self, host: str, port: int, target_dir: str):
        """
        서버를 시작하는 함수입니다. 클라이언트로부터 파일을 받아서 저장합니다.

        Args:
            host (str): 서버의 주소입니다.
            port (int): 서버의 포트입니다.
            target_dir (str): 파일을 저장할 디렉토리입니다.
        """
        logger.info(f"TCP로 서버 시작")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(1)

        while True:
            conn, addr = sock.accept()
            with conn:
                logger.info(f"연결됨 {addr}")
                while True:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    with open(target_dir, 'ab') as file:
                        file.write(data)

        sock.close()