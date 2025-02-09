from tcp import RawTCPServer

if __name__ == "__main__":
    with RawTCPServer(host='localhost', port=8000) as server:
        server.receive_file()
