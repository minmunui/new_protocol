import socket
import os
import json
import signal
import sys
from tqdm import tqdm  # 진행률 표시를 위한 라이브러리


class TCPFileServer:
    def __init__(self, host='localhost', port=8000, chunk_size=8192):
        # TCP 소켓 생성
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (host, port)
        self.chunk_size = chunk_size
        # 소켓 옵션 설정: 주소 재사용 가능
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.server_address)
        self.running = True

        # Ctrl+C 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print('\n서버 종료 중...')
        self.running = False
        self.close()
        sys.exit(0)

    def receive_file(self, file_path='./'):
        self.server_socket.listen(1)  # 연결 대기
        print(f"파일 수신 대기 중... ({self.server_address})")

        while self.running:
            try:
                # 클라이언트 연결 수락
                client_socket, addr = self.server_socket.accept()
                print(f"\n클라이언트 연결됨: {addr}")

                try:
                    # 헤더 크기(4바이트) 수신
                    header_size_data = self._receive_exactly(client_socket, 4)
                    header_size = int.from_bytes(header_size_data, 'big')

                    # 헤더(JSON) 수신
                    header_data = self._receive_exactly(client_socket, header_size)
                    header = json.loads(header_data.decode('utf-8'))

                    filename = f"received_{header['filename']}"
                    file_size = header['file_size']
                    print(f"\n파일 수신 시작: {filename}")
                    print(f"파일 크기: {file_size} bytes")

                    # 파일 수신
                    with open(filename, 'wb') as f:
                        received_size = 0
                        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True)

                        while received_size < file_size:
                            # 남은 크기 계산
                            remaining = file_size - received_size
                            chunk_size = min(self.chunk_size, remaining)

                            # 데이터 수신
                            chunk = self._receive_exactly(client_socket, chunk_size)
                            if not chunk:
                                break

                            f.write(chunk)
                            received_size += len(chunk)
                            progress_bar.update(len(chunk))

                        progress_bar.close()

                    print(f"\n파일 저장 완료: {filename}")
                    # 성공 응답 전송
                    client_socket.send(b'SUCCESS')

                except Exception as e:
                    print(f"파일 수신 중 에러 발생: {e}")
                    try:
                        client_socket.send(b'ERROR')
                    except:
                        pass
                finally:
                    client_socket.close()

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"에러 발생: {e}")
                continue

    def _receive_exactly(self, sock, n):
        """정확히 n 바이트를 수신하는 메서드"""
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def close(self):
        try:
            self.server_socket.close()
            print('서버가 종료되었습니다.')
        except Exception as e:
            print(f'서버 종료 중 에러 발생: {e}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class TCPFileClient:
    def __init__(self, host='localhost', port=8000, chunk_size=8192):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (host, port)
        self.chunk_size = chunk_size
        self.running = True

        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print('\n클라이언트 종료 중...')
        self.running = False
        self.close()
        sys.exit(0)

    def send_file(self, filename):
        if not self.running:
            return False

        if not os.path.exists(filename):
            print(f"파일을 찾을 수 없습니다: {filename}")
            return False

        try:
            # 서버 연결
            print(f"서버 연결 중... {self.server_address}")
            self.client_socket.connect(self.server_address)

            # 파일 정보 준비
            file_size = os.path.getsize(filename)
            header = {
                'filename': os.path.basename(filename),
                'file_size': file_size
            }

            # 헤더 전송
            header_data = json.dumps(header).encode('utf-8')
            header_size = len(header_data)
            self.client_socket.send(header_size.to_bytes(4, 'big'))
            self.client_socket.send(header_data)

            # 파일 전송
            with open(filename, 'rb') as f:
                progress_bar = tqdm(total=file_size, unit='B', unit_scale=True)
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    self.client_socket.send(chunk)
                    progress_bar.update(len(chunk))
                progress_bar.close()

            # 전송 결과 확인
            response = self.client_socket.recv(7)
            success = response == b'SUCCESS'

            if success:
                print("\n파일 전송 완료!")
            else:
                print("\n파일 전송 실패!")

            return success

        except Exception as e:
            print(f"파일 전송 중 에러 발생: {e}")
            return False
        finally:
            self.close()

    def close(self):
        try:
            self.client_socket.close()
            print('클라이언트가 종료되었습니다.')
        except Exception as e:
            print(f'클라이언트 종료 중 에러 발생: {e}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
