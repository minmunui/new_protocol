import socket  # 네트워크 통신을 위한 소켓 라이브러리
import os  # 파일 및 경로 조작을 위한 라이브러리
import json  # JSON 데이터 처리를 위한 라이브러리
import signal  # 시스템 시그널 처리를 위한 라이브러리
import sys  # 시스템 함수 및 파라미터 사용을 위한 라이브러리


class UDPFileServer:
    """
    UDP 프로토콜을 사용하여 파일을 수신하는 서버 클래스
    """

    def __init__(self, host='localhost', port=8000, chunk_size=65527):
        """
        UDP 파일 서버 초기화

        Args:
            host (str): 서버 호스트 주소
            port (int): 서버 포트 번호
            chunk_size (int): 파일 청크 크기 (바이트)
        """
        # UDP 소켓 생성 (SOCK_DGRAM은 UDP를 의미)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (host, port)
        self.chunk_size = chunk_size
        # 소켓을 주소에 바인딩
        self.server_socket.bind(self.server_address)
        # 수신된 파일 청크를 저장할 딕셔너리
        self.received_chunks = {}
        # 서버 실행 상태 플래그
        self.running = True

        # Ctrl+C (SIGINT) 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        시그널 처리 함수 (Ctrl+C 입력 시 호출)
        """
        print('\n\n서버 종료 신호를 받았습니다. 안전하게 종료합니다...')
        self.running = False
        self.close()
        sys.exit(0)

    def receive_file(self):
        print(f"파일 수신 대기 중... ({self.server_address})")

        while True:
            try:
                # 메타데이터 또는 파일 청크 수신
                data, client_address = self.server_socket.recvfrom(65507)

                # 처음 4바이트가 0xFFFFFFFF인 경우 메타데이터로 처리
                if data[:4] == b'\xFF\xFF\xFF\xFF':
                    try:
                        # 메타데이터는 UTF-8로 디코딩 (4바이트 이후의 데이터만)
                        metadata = json.loads(data[4:].decode('utf-8'))
                        filename = metadata['filename']
                        total_chunks = metadata['total_chunks']
                        print(f"\n새로운 파일 수신 시작: {filename}")
                        print(f"예상 청크 수: {total_chunks}")

                        self.received_chunks = {
                            'filename': filename,
                            'total_chunks': total_chunks,
                            'chunks': {},
                            'client_address': client_address
                        }

                        # 메타데이터 수신 확인 응답
                        response = b'\xFF\xFF\xFF\xFF' + json.dumps({'type': 'metadata_ack'}).encode()
                        self.server_socket.sendto(response, client_address)
                        continue
                    except json.JSONDecodeError:
                        print("메타데이터 디코딩 실패")
                        continue

                # 파일 청크 처리
                chunk_num = int.from_bytes(data[:4], 'big')
                chunk_data = data[4:]

                if chunk_num not in self.received_chunks['chunks']:
                    self.received_chunks['chunks'][chunk_num] = chunk_data
                    print(f"\r청크 수신 중: {len(self.received_chunks['chunks'])}/{self.received_chunks['total_chunks']}",
                          end='')

                # 청크 수신 확인 응답
                ack = chunk_num.to_bytes(4, 'big')
                self.server_socket.sendto(ack, client_address)

                # 모든 청크를 받았는지 확인
                if len(self.received_chunks['chunks']) == self.received_chunks['total_chunks']:
                    self._save_file()
                    print(f"\n파일 저장 완료: {self.received_chunks['filename']}")
                    self.received_chunks = {}

            except Exception as e:
                print(f"\n에러 발생: {e}")
                continue

    def _save_file(self):
        """
        수신된 청크들을 하나의 파일로 저장하는 메서드
        """
        filename = "received_" + self.received_chunks['filename']
        with open(filename, 'wb') as f:
            # 청크 번호 순서대로 파일 작성
            for i in range(self.received_chunks['total_chunks']):
                f.write(self.received_chunks['chunks'][i])

    def close(self):
        """
        서버 소켓을 안전하게 종료하는 메서드
        """
        try:
            if hasattr(self, 'server_socket'):
                self.server_socket.close()
                print('서버 소켓이 정상적으로 종료되었습니다.')
        except Exception as e:
            print(f'서버 종료 중 에러 발생: {e}')

    # Context manager 메서드들
    def __enter__(self):
        """
        Context manager 진입 메서드
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager 종료 메서드
        서버 종료 시 자동으로 리소스 정리
        """
        self.close()


class UDPFileClient:
    """
    UDP 프로토콜을 사용하여 파일을 전송하는 클라이언트 클래스
    """

    def __init__(self, host='localhost', port=12345, chunk_size=8192):
        """
        UDP 파일 클라이언트 초기화

        Args:
            host (str): 서버 호스트 주소
            port (int): 서버 포트 번호
            chunk_size (int): 파일 청크 크기 (바이트)
        """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (host, port)
        self.chunk_size = chunk_size
        self.client_socket.settimeout(1.0)  # 소켓 타임아웃 설정
        self.running = True

        # Ctrl+C 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        시그널 처리 함수 (Ctrl+C 입력 시 호출)
        """
        print('\n\n클라이언트 종료 신호를 받았습니다. 안전하게 종료합니다...')
        self.running = False
        self.close()
        sys.exit(0)

    def send_file(self, filename):
        if not os.path.exists(filename):
            print(f"파일을 찾을 수 없습니다: {filename}")
            return False

        file_size = os.path.getsize(filename)
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size

        print(f"파일 전송 시작: {filename}")
        print(f"파일 크기: {file_size} bytes")
        print(f"총 청크 수: {total_chunks}")

        # 메타데이터 전송 (특별한 헤더 추가)
        metadata = {
            'filename': os.path.basename(filename),
            'total_chunks': total_chunks
        }
        metadata_packet = b'\xFF\xFF\xFF\xFF' + json.dumps(metadata).encode()
        if not self._send_with_retry(metadata_packet):
            return False

        # 파일 청크 전송
        with open(filename, 'rb') as f:
            for chunk_num in range(total_chunks):
                chunk_data = f.read(self.chunk_size)
                packet = chunk_num.to_bytes(4, 'big') + chunk_data

                if not self._send_with_retry(packet, chunk_num):
                    print(f"\n청크 {chunk_num} 전송 실패")
                    return False

                print(f"\r전송 진행률: {chunk_num + 1}/{total_chunks}", end='')

        print("\n파일 전송 완료!")
        return True

    def _send_with_retry(self, data, chunk_num=None, max_retries=5):
        retries = 0
        while retries < max_retries:
            try:
                self.client_socket.sendto(data, self.server_address)
                response, _ = self.client_socket.recvfrom(65507)

                if chunk_num is not None:
                    # 파일 청크 전송의 경우
                    received_chunk_num = int.from_bytes(response, 'big')
                    if received_chunk_num == chunk_num:
                        return True
                else:
                    # 메타데이터 전송의 경우
                    if response[:4] == b'\xFF\xFF\xFF\xFF':
                        try:
                            response_data = json.loads(response[4:].decode())
                            if response_data.get('type') == 'metadata_ack':
                                return True
                        except json.JSONDecodeError:
                            pass

            except socket.timeout:
                retries += 1
                print(f"\n재시도 중... ({retries}/{max_retries})")
                continue

        return False

    def close(self):
        """
        클라이언트 소켓을 안전하게 종료하는 메서드
        """
        try:
            if hasattr(self, 'client_socket'):
                self.client_socket.close()
                print('클라이언트 소켓이 정상적으로 종료되었습니다.')
        except Exception as e:
            print(f'클라이언트 종료 중 에러 발생: {e}')

    def __enter__(self):
        """Context manager 진입 메서드"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 메서드"""
        self.close()
