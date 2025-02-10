import socket
import os
import struct
import time
from pathlib import Path

BUFFER_SIZE = 1024 * 1024 * 512  # 1GB


def flush_receive_buffer(sock, buffer_size=BUFFER_SIZE):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)


def start_server(host='localhost', port=9999, buffer_size=4096, target_dir="received"):
    # 서버 소켓 생성
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
    flush_receive_buffer(server_socket)

    print(f"서버가 {host}:{port}에서 시작되었습니다...")
    print(f"파일을 받을 디렉터리: {target_dir}")
    print(f"버퍼 크기: {buffer_size}")

    while True:
        # 파일 정보는 항상 고정된 크기로 받기
        data, client_address = server_socket.recvfrom(512)  # 초기 정보는 작은 크기로 받음
        filename, total_chunks = struct.unpack('!256sI', data[:260])
        filename = filename.decode().strip('\x00')
        print(f"파일 {filename}을(를) 받기 시작합니다... (총 {total_chunks}개 청크)")

        # 이후 데이터 수신할 때는 지정된 버퍼 크기 사용
        chunks = {}
        start_time = time.time()
        timeout = 10

        while len(chunks) < total_chunks:
            try:
                # 실제 데이터 수신 시에는 buffer_size 사용
                data, _ = server_socket.recvfrom(buffer_size)
                seq_num, chunk_size = struct.unpack('!II', data[:8])
                chunk_data = data[8:8 + chunk_size]

                chunks[seq_num] = chunk_data

                # 진행률 출력
                progress = (len(chunks) / total_chunks) * 100
                print(f"\r수신 진행률: {progress:.1f}% seq_num: {seq_num}")

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
