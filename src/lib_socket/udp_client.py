import math
import os
import socket
import struct


def send_file(filename, host='localhost', port=9999, buffer_size=2*8192):
    # 클라이언트 소켓 생성
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (host, port)

    try:
        # 파일 존재 확인
        if not os.path.exists(filename):
            raise FileNotFoundError(f"파일 {filename}을(를) 찾을 수 없습니다.")

        # 파일 크기 확인 및 청크 수 계산
        file_size = os.path.getsize(filename)
        total_chunks = math.ceil(file_size / buffer_size)
        print(f"청크 수: {total_chunks}")

        # 파일 정보 전송 (파일명 + 총 청크 수)
        file_info = struct.pack('!256sI', filename.encode(), total_chunks)
        client_socket.sendto(file_info, server_address)

        # 파일 전송 시작
        with open(filename, 'rb') as f:
            for seq_num in range(total_chunks):
                chunk_data = f.read(buffer_size)
                chunk_size = len(chunk_data)

                # SEQ 번호와 청크 크기를 포함하여 패킷 구성
                packet = struct.pack('!II', seq_num, chunk_size) + chunk_data
                client_socket.sendto(packet, server_address)

                # 진행률 출력
                progress = ((seq_num + 1) / total_chunks) * 100
                print(f"\r전송 진행률: {progress:.1f}% 전송중인 패킷 {seq_num:d}", end='')

        print(f"\n파일 {filename} 전송 완료!")

    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        client_socket.close()
