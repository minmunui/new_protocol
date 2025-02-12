import socket
import threading
import time

def peek_buffer(sock, buffer_size):
    try:
        # 데이터를 실제로 읽지 않고 확인만 함
        data = sock.recv(buffer_size, socket.MSG_PEEK)
        print(f"버퍼 데이터 크기: {len(data)} 바이트")
        # 처음 몇 바이트만 출력
        print(f"데이터 미리보기: {data[:20]}")
        return len(data)
    except socket.error as e:
        print(f"버퍼 확인 중 에러: {e}")
        return 0

class BufferMonitor:
    def __init__(self, sock):
        self.sock = sock
        self.running = False
        self.monitor_thread = None

    def start_monitoring(self, interval=0.1):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor(self):
        while self.running:
            buffer_size = peek_buffer(self.sock)
            if buffer_size > 0:
                print(f"현재 버퍼 크기: {buffer_size}")
            time.sleep(0.1)  # 모니터링 간격