import argparse
import json
import os
import socket


class TCPFileClient:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port

    def send_file(self, filename):
        try:
            # 파일 존재 확인
            if not os.path.exists(filename):
                raise FileNotFoundError(f"파일 {filename}을(를) 찾을 수 없습니다.")

            # 소켓 생성 및 연결
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))

            # 파일 정보 전송
            filesize = os.path.getsize(filename)
            file_info = {
                'filename': os.path.basename(filename),
                'filesize': filesize
            }
            client_socket.send(json.dumps(file_info).encode())

            # 서버 준비 응답 대기
            response = client_socket.recv(1024).decode()
            if response != "READY":
                raise Exception("서버가 준비되지 않았습니다.")

            # 파일 전송
            sent_size = 0
            with open(filename, 'rb') as file:
                while True:
                    data = file.read(4096)
                    if not data:
                        break
                    client_socket.send(data)
                    sent_size += len(data)

                    # 진행률 출력
                    progress = (sent_size / filesize) * 100
                    print(f"진행률: {progress:.2f}%")

            # 전송 완료 확인
            response = client_socket.recv(1024).decode()
            if response == "SUCCESS":
                print(f"파일 {filename} 전송 완료!")
            else:
                print("파일 전송 실패")

        except Exception as e:
            print(f"에러 발생: {e}")

        finally:
            client_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--host", type=str, default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, defulat=9999)
    parser.add_argument("-f", "--filename", type=str, required=True)


    args = parser.parse_args()
    tcp_client = TCPFileClient(host=args.host, port=args.port)
    tcp_client.send_file(filename=args.filename)