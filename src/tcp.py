import socket
import time
import os
import struct
import json
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
            bool: 전송 성공 여부를 반환합니다.
        """
        logger.info(f"TCP로 전송 시작 - 파일: {filename}")

        try:
            # 소켓 생성 및 연결
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            # 파일 크기 및 이름 정보 구성
            filesize = os.path.getsize(filename)
            file_info = {
                "filename": os.path.basename(filename),
                "filesize": filesize
            }

            # 헤더 정보를 JSON으로 변환 후 전송
            file_info_json = json.dumps(file_info).encode('utf-8')
            header = struct.pack('!I', len(file_info_json))
            sock.sendall(header)
            sock.sendall(file_info_json)

            # 파일 데이터 전송
            bytes_sent = 0
            with open(filename, 'rb') as file:
                while True:
                    data = file.read(buffer_size)
                    if not data:
                        break
                    sock.sendall(data)
                    bytes_sent += len(data)
                    logger.debug(f"전송 중: {bytes_sent}/{filesize} 바이트 ({bytes_sent / filesize * 100:.2f}%)")
                    time.sleep(interval)

            # 전송 완료 확인
            logger.info(f"파일 전송 완료: {filename} ({filesize} 바이트)")

            # 서버로부터 수신 확인 메시지 받기
            response = sock.recv(1024).decode('utf-8')
            logger.info(f"서버 응답: {response}")

            sock.close()
            return True

        except Exception as e:
            logger.error(f"파일 전송 중 오류 발생: {e}")
            return False

    def start_server(self, host: str, port: int, target_dir: str = "received"):
        """
        서버를 시작하는 함수입니다. 클라이언트로부터 파일을 받아서 저장합니다.

        Args:
            host (str): 서버의 주소입니다.
            port (int): 서버의 포트입니다.
            target_dir (str): 파일을 저장할 디렉토리입니다.
        """
        logger.info(f"TCP로 서버 시작 - {host}:{port}")

        # 저장 디렉토리 확인 및 생성
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            logger.info(f"디렉토리 생성: {target_dir}")

        # 소켓 생성 및 바인딩
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)

        logger.info(f"서버가 {host}:{port}에서 실행 중입니다. 클라이언트 연결 대기 중...")

        try:
            while True:
                conn, addr = sock.accept()
                logger.info(f"클라이언트가 연결되었습니다: {addr}")

                try:
                    # 헤더 사이즈 수신 (4바이트 정수)
                    header = conn.recv(4)
                    if not header or len(header) != 4:
                        logger.error("유효하지 않은 헤더를 수신했습니다.")
                        conn.close()
                        continue

                    # 헤더 사이즈 추출
                    header_size = struct.unpack('!I', header)[0]

                    # 파일 정보 수신
                    file_info_json = conn.recv(header_size).decode('utf-8')
                    file_info = json.loads(file_info_json)

                    filename = file_info["filename"]
                    filesize = file_info["filesize"]

                    # 파일 저장 경로
                    filepath = os.path.join(target_dir, filename)

                    logger.info(f"파일 수신 시작: {filename} (크기: {filesize} 바이트)")

                    # 파일 수신 및 저장
                    received_size = 0
                    with open(filepath, 'wb') as file:
                        while received_size < filesize:
                            # 남은 데이터 크기 계산
                            to_read = min(BUFFER_SIZE, filesize - received_size)

                            # 데이터 수신
                            data = conn.recv(to_read)
                            if not data:
                                break

                            # 파일에 쓰기
                            file.write(data)
                            received_size += len(data)

                            # 진행 상황 로깅
                            if received_size % (BUFFER_SIZE * 10) == 0 or received_size == filesize:
                                logger.debug(
                                    f"수신 중: {received_size}/{filesize} 바이트 ({received_size / filesize * 100:.2f}%)")

                    # 파일 수신 완료 확인
                    if received_size == filesize:
                        logger.info(f"파일 '{filename}'을(를) 성공적으로 수신했습니다. ({filesize} 바이트)")
                        conn.send("파일 수신 완료".encode('utf-8'))
                    else:
                        logger.warning(f"파일 '{filename}'의 수신이 불완전합니다. (예상: {filesize}, 실제: {received_size})")
                        conn.send("파일 수신 불완전".encode('utf-8'))

                except Exception as e:
                    logger.error(f"파일 수신 중 오류 발생: {e}")
                    conn.send(f"오류: {str(e)}".encode('utf-8'))

                finally:
                    conn.close()

        except KeyboardInterrupt:
            logger.info("서버를 종료합니다.")

        finally:
            sock.close()