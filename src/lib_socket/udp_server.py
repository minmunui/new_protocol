import array
import socket
import os
import struct
import time
from pathlib import Path

from buffer_monitor import BufferMonitor, peek_buffer

BUFFER_SIZE = 1024 * 1024 * 1024  # 1GB

def send_ack(missed_seqs : list[int], sock : socket.socket, target_address : tuple):
    arr = array.array('i', missed_seqs)
    packed = arr.tobytes()
    print(f"전송할 패킷정보 크기 {len(packed)}")
    sock.sendto(packed, target_address)

def flush_receive_buffer(sock):
    # Set socket to non-blocking mode
    sock.setblocking(False)
    print(f"socket을 비웁니다.")
    # Read until buffer is empty
    try:
        while True:
            data = sock.recvfrom(BUFFER_SIZE)
            print(f"비운 데이터 {data}")
    except BlockingIOError:
        pass
    finally:
        # Reset to blocking mode
        sock.setblocking(True)

def start_server(host='localhost', port=9999, buffer_size=4096, target_dir="received"):
    # 서버 소켓 생성
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    # monitor = BufferMonitor(server_socket)
    # monitor.start_monitoring()

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)

    print(f"서버가 {host}:{port}에서 시작되었습니다...")
    print(f"파일을 받을 디렉터리: {target_dir}")
    print(f"버퍼 크기: {buffer_size}")

    while True:
        flush_receive_buffer(server_socket)
        # 파일 정보는 항상 고정된 크기로 받기
        data, client_address = server_socket.recvfrom(512)  # 초기 정보는 작은 크기로 받음
        filename, total_chunks = struct.unpack('!256sI', data[:260])
        filename = filename.decode().strip('\x00')
        print(f"파일 {filename}을(를) 받기 시작합니다... (총 {total_chunks}개 청크)")

        # 이후 데이터 수신할 때는 지정된 버퍼 크기 사용
        chunks = {}
        start_time = time.time()
        timeout = 10

        last_seq_num = total_chunks - 1

        while len(chunks) < total_chunks:
            try:
                # 실제 데이터 수신 시에는 buffer_size 사용
                last_signal_time = time.time()

                # remaining_buffer = peek_buffer(server_socket, BUFFER_SIZE)
                # if remaining_buffer > 0:
                #     print(f"처리 후 버퍼에 {remaining_buffer} 바이트 남음")
                data, _ = server_socket.recvfrom(buffer_size)

                seq_num, chunk_size = struct.unpack('!II', data[:8])
                chunk_data = data[8:8 + chunk_size]

                # print(f"받은 청크 (길이{len(chunk_data)}) : {chunk_data}")

                chunks[seq_num] = chunk_data

                # 진행률 출력
                progress = (len(chunks) / total_chunks) * 100
                print(f"\r수신 진행률: {progress:.1f}% seq_num: {seq_num} / {last_seq_num}", end="")

                # 마지막 청크인지 체크
                if seq_num == last_seq_num:

                    received_seqs = set(chunks.keys())
                    all_seqs = set(range(total_chunks))
                    missed_seqs = list(all_seqs - received_seqs)
                    print(f"마지막 청크 도달 seq_num = {seq_num}")

                    print(f"분실된 패킷 : {missed_seqs}")
                    if len(missed_seqs) > 0:
                        last_seq_num = max(missed_seqs)
                        print(f"새로운 last_seq = {last_seq_num}")

                    send_ack(missed_seqs, server_socket, client_address)
                # 타임아웃 체크
                if time.time() - last_signal_time > timeout:
                    raise TimeoutError("파일 수신 시간 초과")

            except (struct.error, IndexError) as e:
                print(f"\n패킷 손상: {e}")
                continue
        print()
        transfer_end_time = time.time()
        transfer_elapsed_time = transfer_end_time - start_time
        print(f"transfer_elapsed_time\t{transfer_elapsed_time}")

        print("\n모든 청크 수신 완료. 파일 재조합 시작...")

        file_path = f"{target_dir}/{filename}"

        # 이미 존재하는 파일은 _dup를 붙임
        is_exist = True
        while is_exist:
            if os.path.exists(file_path):
                print(f"이미 존재하는 파일 : {file_path}")
                file_path = file_path.split('.')
                file_path = "".join(file_path[:-1]) + "_dup." + file_path[-1]
                print(f"파일이름 변경 -> {file_path}")
            else:
                is_exist = False

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # 파일 재조합
        with open(file_path, 'wb') as f:
            for i in range(total_chunks):
                # print(f"{i}번째 청크 조합중\n{chunks[i]}", end='')
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
        print(f"저장 경로 {file_path}")


# 사용 예시
if __name__ == "__main__":
    pass
