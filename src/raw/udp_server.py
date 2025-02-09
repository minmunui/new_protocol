from udp import RawUDPServer

if __name__ == "__main__":
    with RawUDPServer(host='localhost', port=8000) as server:
        server.receive_file()
