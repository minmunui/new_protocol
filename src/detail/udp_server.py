from udp import UDPFileServer

if __name__ == "__main__":
    with UDPFileServer(host='localhost', port=8000) as server:
        server.receive_file()
