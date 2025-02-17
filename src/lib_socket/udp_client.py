import array
import math
import os
import socket
import struct
import time
from array import array

KB = 1024


def wait_ack(sock: socket.socket, timeout: float = 3.0) -> array[int]:
    """
    ack를 기다립니다. 일정 시간동안 응답이 없을 경우 예외를 발생시킵니다.
    Args:
        sock : ack를 받아들일 socket을 지정합니다.
        timeout : ack가 해당 시간동안 없을 경우 예외를 발생시킵니다.

    Returns:
        ack를 받았을 경우 해당 ack에 존재하는 missed_seq_numbers를 반환합니다.

    Raises:
        socket.timeout : 해당 소켓에서 일정 시간동안 응답이 없을 경우 발생합니다.
    """
    sock.settimeout(timeout)

    try:
        packed_data, addr = sock.recvfrom(KB * 32)
        # ACK는 정수의 배열
        result_array = array('i')
        result_array.frombytes(packed_data)
        print(f"ACK전달받음 : {result_array}")
    except socket.timeout:
        raise socket.timeout

    sock.setblocking(False)
    return result_array


def process_ack(sock: socket.socket, client_address: tuple, packet_dict : dict, last_seq_number : int, timeout: float = 0.5) -> array[int]:
    """
    ack를 받아 처리하고, ack가 오지 않을 경우 마지막 chucnk를 재전송합니다. ack를 받을 경우 ack를 반환합니다.

    Args:
        sock : ACK수신 및 마지막 청크 재전송을 위한 소켓입니다.
        client_address : 이를 위한 타켓 네트워크 주소 및 포트입니다.
        packet_dict : ACK를 전달맏지 못할 경우 전송하는데 사용하는 패킷 dict입니다.
        last_seq_number : 현재 전송에서 ACK를 유발하는 마지막 seq_number입니다.
    """
    retry_count = 0
    while True:
        try:
            print(f"ACK를 기다리는 중")
            print(f"받아야 할 seq_number: {last_seq_number}")
            return wait_ack(sock, timeout)
        except socket.timeout:
            retry_count += 1
            if retry_count > 5:
                print(f"재전송 초과됨 횟수 초과됨")
                raise socket.timeout
            print(f"ACK 재전송 seq_number {last_seq_number} | 재전송 : {retry_count}")
            sock.sendto(packet_dict[last_seq_number], client_address)



def resend_dropped_data(sock: socket.socket, dropped_seq_numbers: list[int] | array[int], packet_dict: dict,
                        server_addr: tuple[str, int]):
    """

    """
    for seq_number in dropped_seq_numbers:
        sock.sendto(packet_dict[seq_number], server_addr)


def send_file(filename: str, host: str = 'localhost', port: int = 9999, buffer_size: int = 4096, interval: float = 0.001):
    # 클라이언트 소켓 생성
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (host, port)
    print(f"파일 {filename}을(를) 전송합니다...")
    print(f"서버 주소: {host}:{port}")
    print(f"버퍼 크기: {buffer_size}")

    chunk_size = buffer_size - 8

    losses = []

    try:
        # 파일 존재 확인
        if not os.path.exists(filename):
            raise FileNotFoundError(f"파일 {filename}을(를) 찾을 수 없습니다.")

        # 파일 크기 확인 및 청크 수 계산
        file_size = os.path.getsize(filename)
        total_chunks = math.ceil(file_size / chunk_size)
        print(f"청크 수: {total_chunks}")

        # 파일 정보 전송 (파일명 + 총 청크 수)
        file_info = struct.pack('!II256s', buffer_size, total_chunks, filename.encode()[:256])
        client_socket.sendto(file_info[:512], server_address)

        # 청크를 보관하기 위한 dictionary
        packet_dict = {}
        # 파일 전송 시작

        start_time = time.time()
        with open(filename, 'rb') as f:
            for seq_num in range(total_chunks):
                chunk_data = f.read(chunk_size)

                # SEQ 번호와 청크 크기를 포함하여 패킷 구성
                packet = struct.pack('!II', seq_num, chunk_size) + chunk_data
                packet_dict[seq_num] = packet
                client_socket.sendto(packet, server_address)

                time.sleep(interval)

                # 진행률 출력
                progress = ((seq_num + 1) / total_chunks) * 100
                print(f"\r전송 진행률: {progress:.1f}% 전송한 패킷 {seq_num:d}", end='')

        print(f"\n파일 {filename} 전송")
        print(f"소요시간 {time.time() - start_time}")
        transfer_complete = False

        last_seq_number = len(packet_dict) - 1
        while not transfer_complete:
            try:
                dropped_seq_numbers = process_ack(client_socket, server_address, packet_dict, last_seq_number)
                losses.append(dropped_seq_numbers)
            except socket.timeout:
                losses.append([-1])
                break
            if len(dropped_seq_numbers) == 0:
                print(f"완료된 ACK 전달받음")
                transfer_complete = True
            else:
                last_seq_number = max(dropped_seq_numbers)
                print(f"소실패킷 재전송 dropped_seq_numbers: {dropped_seq_numbers}")
                resend_dropped_data(client_socket, dropped_seq_numbers, packet_dict, server_address)


    # except Exception as e:
    #     print(f"에러 발생: {e}")
    finally:
        client_socket.close()
        return losses
