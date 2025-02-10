import socket
import os
import struct
import time
from pathlib import Path


def start_server(host='localhost', port=9999, buffer_size=2 * 8192, target_dir="received"):
    # 서버 소켓 생성
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"서버가 {host}:{port}에서 시작되었습니다...")

    while True:
        # 클라이언트로부터 파일 정보 받기
        data, client_address = server_socket.recvfrom(buffer_size)
        filename, total_chunks = struct.unpack('!256sI', data[:260])
        filename = filename.decode().strip('\x00')
        print(f"파일 {filename}을(를) 받기 시작합니다... (총 {total_chunks}개 청크)")

        # 청크를 저장할 딕셔너리 초기화
        chunks = {}
        start_time = time.time()
        timeout = 10  # 10초 타임아웃

        # 청크 수신
        while len(chunks) < total_chunks:
            try:
                data, _ = server_socket.recvfrom(buffer_size + 8)  # SEQ 번호(4바이트) + 청크 크기(4바이트) + 데이터
                seq_num, chunk_size = struct.unpack('!II', data[:8])
                chunk_data = data[8:8 + chunk_size]

                chunks[seq_num] = chunk_data

                # 진행률 출력
                progress = (len(chunks) / total_chunks) * 100
                print(f"\r수신 진행률: {progress:.1f}%", end='')

                # 타임아웃 체크
                if time.time() - start_time > timeout:
                    raise TimeoutError("파일 수신 시간 초과")

            except (struct.error, IndexError) as e:
                print(f"\n패킷 손상: {e}")
                continue

        transfer_end_time = time.time()
        transfer_elapsed_time = transfer_end_time - start_time
        print(f"transfer_elapsed_time\t{transfer_elapsed_time}")

        print("\n모든 청크 수신 완료. 파일 재조합 시작...")

        file_path = f"{target_dir}/{filename}"

        # 이미 존재하는 파일은 _dup를 붙임
        is_exist = True
        while is_exist:
            if os.path.exists(file_path):
                file_path = file_path.split('.')
                file_path = "".join(file_path[:-1]) + "_dup." + file_path[-1]
            else:
                is_exist = False

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # 파일 재조합
        with open(file_path, 'wb') as f:
            for i in range(total_chunks):
                if i in chunks:
                    f.write(chunks[i])
                else:
                    print(f"경고: 청크 {i} 유실")

        total_end_time = time.time()
        total_elapsed_time = total_end_time - start_time
        file_size = os.path.getsize(file_path)
        print(f"measured_transfer_speed\t{file_size / transfer_elapsed_time}")
        print(f"measured_total_speed\t{file_size / total_elapsed_time}")
        print(f"파일 {filename} 수신 완료!")


# 사용 예시
if __name__ == "__main__":
    pass
