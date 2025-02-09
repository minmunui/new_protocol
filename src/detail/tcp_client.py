import argparse

from tcp import TCPFileClient

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, default="./input/file")
    args = parser.parse_args()

    file_name = args.file

    with TCPFileClient(host='localhost', port=8000) as client:
        client.send_file(file_name)
