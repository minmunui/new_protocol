import argparse
import datetime
import time

from udp_server import start_server
from udp_client import send_file

def program(filename: str, host: str = 'localhost', port: int = 9999, buffer_size: int = 4096):
    start_buffer_size_coef = 4
    end_buffer_size_coef = 16

    iterate_num = 50

    start_interval = 0.0001
    end_interval = 0.001
    interval_of_interval = 0.0001

    interval = start_interval

    str_time_now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


    log_name = str_time_now + "itvl" + str(start_interval) + '-' + str(end_interval) + "bfr" + str(start_buffer_size_coef) + "-" + str(end_buffer_size_coef)
    with open(log_name, 'w', encoding='utf-8') as file:
        file.write(f"{log_name}\n")
        while interval <= end_interval:
            buffer_size_coef = start_buffer_size_coef
            while buffer_size_coef <= end_buffer_size_coef:
                file.write(f"Buffer Size : {buffer_size_coef}\t Interval : {interval}\n")
                for i in range(iterate_num):
                    losses = send_file(filename, host, port, 1024 * buffer_size_coef, interval)
                    time.sleep(5)
                    file.write(f"Iteration : {i+1}\n")
                    for loss in losses:
                        volume_lossed = len(loss) * buffer_size_coef * 4
                        file.write(f"LOSS : {volume_lossed}\n")
                        file.write(f"{loss}\n")
                    file.write("\n")

                buffer_size_coef *= 2

        interval += interval_of_interval
    file.write("\n")
    end_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file.write(f"end : {end_time}\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="./input/file")
    parser.add_argument("-c", "--client", type=bool, default=False)
    parser.add_argument("-t", "--target", type=str, default="localhost")
    parser.add_argument("-p", "--port", type=int, default=9999)
    parser.add_argument("-b", "--buffer_size", type=int, default=1)
    parser.add_argument("-d", "--developer", type=bool, default=False)

    args = parser.parse_args()

    host = args.target
    port = args.port
    is_client = args.client

    is_developer = args.developer
    file_name = args.file

    if is_developer:
        program(file_name, host=host, port=port, buffer_size=4096 * args.buffer_size)

    if is_client:
        send_file(file_name, host=host, port=port, buffer_size=4096 * args.buffer_size, interval=0.0001)

    else:
        start_server(host=host, port=port, buffer_size=4096 * args.buffer_size)

