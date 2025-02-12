import array
import math
import os
import socket
import struct
import time
from array import array

KB_1 = 1024


def receive_ACK(sock: socket.socket) -> array[int]:
    packed_data, addr = sock.recvfrom(KB_1 * 8)
    # ACK는 정수의 배열
    result_array = array.array('i')
    result_array.frombytes(packed_data)
    return result_array


def resend_dropped_data(sock: socket.socket, dropped_seq_numbers: list[int] | array[int], packet_dict: dict,
                        server_addr: tuple[str, int]):
    """

    """
    for seq_number in dropped_seq_numbers:
        sock.sendto(packet_dict[seq_number], server_addr)


def send_file(filename: str, host: str = 'localhost', port: int = 9999, buffer_size: int = 4096):
    # 클라이언트 소켓 생성
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (host, port)
    print(f"파일 {filename}을(를) 전송합니다...")
    print(f"서버 주소: {host}:{port}")
    print(f"버퍼 크기: {buffer_size}")

    try:
        # 파일 존재 확인
        if not os.path.exists(filename):
            raise FileNotFoundError(f"파일 {filename}을(를) 찾을 수 없습니다.")

        # 파일 크기 확인 및 청크 수 계산
        file_size = os.path.getsize(filename)
        total_chunks = math.ceil(file_size / buffer_size)
        print(f"청크 수: {total_chunks}")

        # 파일 정보 전송 (파일명 + 총 청크 수)
        file_info = struct.pack('!256sI', filename.encode()[:256], total_chunks)
        client_socket.sendto(file_info[:512], server_address)

        # 청크를 보관하기 위한 dictionary
        packet_dict = {}
        # 파일 전송 시작
        with open(filename, 'rb') as f:
            for seq_num in range(total_chunks):
                chunk_data = f.read(buffer_size)
                chunk_size = len(chunk_data)

                # SEQ 번호와 청크 크기를 포함하여 패킷 구성
                packet = struct.pack('!II', seq_num, chunk_size) + chunk_data
                packet_dict[seq_num] = packet
                client_socket.sendto(packet, server_address)

                time.sleep(0.02)

                # 진행률 출력
                progress = ((seq_num + 1) / total_chunks) * 100
                print(f"\r전송 진행률: {progress:.1f}% 전송한 패킷 {seq_num:d}", end='')

        print(f"\n파일 {filename} 전송 완료!")

        transfer_complete = False
        while not transfer_complete:
            dropped_seq_numbers = receive_ACK(client_socket)
            if len(dropped_seq_numbers) == 0:
                transfer_complete = True
            else:
                resend_dropped_data(client_socket, dropped_seq_numbers, packet_dict, server_address)


    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        client_socket.close()
