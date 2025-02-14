import argparse

from udp_server import start_server
from udp_client import send_file

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="./input/file")
    parser.add_argument("-c", "--client", type=bool, default=False)
    parser.add_argument("-t", "--target", type=str, default="localhost")
    parser.add_argument("-p", "--port", type=int, default=9999)
    parser.add_argument("-b", "--buffer_size", type=int, default=1)

    args = parser.parse_args()

    host = args.target
    port = args.port
    is_client = args.client

    if is_client:
        file_name = args.file
        send_file(file_name, host=host, port=port, buffer_size=4096 * args.buffer_size)

    else:
        start_server(host=host, port=port)
