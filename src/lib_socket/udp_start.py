import argparse

from udp_server import start_server
from udp_client import send_file

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="./input/file")
    parser.add_argument("-c", "--client", type=bool, default=False)

    args = parser.parse_args()

    is_client = args.client

    if is_client:
        file_name = args.file
        send_file(file_name)

    else:
        start_server()
