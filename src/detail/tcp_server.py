from tcp import TCPFileServer

if __name__ == "__main__":
    with TCPFileServer(host='localhost', port=8000) as server:
        server.receive_file()
