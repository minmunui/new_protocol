import os

from protocol import BUFFER_SIZE
import logger


def make_new_filename(filepath: str):
    """
    해당 경로에 파일을 저장할 때, 파일을 저장할 수 있는 이름을 반환합니다.
    Args:
        filepath : 판별할 파일 이름
    Returns:
        새로운 파일 이름
    """
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    base_name = name.split('_')[0] if '_' in name else name
    counter = 1

    new_filepath = filepath
    while os.path.exists(new_filepath):
        new_filename = f"{base_name}_{counter}{ext}"
        new_filepath = os.path.join(directory, new_filename)
        counter += 1

    logger.info(f"새로운 파일 이름: {new_filepath}")
    return new_filepath


def flush_receive_buffer(sock):
    # Set socket to non-blocking mode
    sock.setblocking(False)
    print(f"socket을 비웁니다.")
    # Read until buffer is empty
    total = 0
    try:
        while True:
            data = sock.recvfrom(BUFFER_SIZE)
            total += len(data)
    except BlockingIOError:
        pass
    finally:
        print(f"읽은 데이터 크기 {total}")
        # Reset to blocking mode
        sock.setblocking(True)