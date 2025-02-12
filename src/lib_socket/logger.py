import logging
import sys
from datetime import datetime
import os

def setup_logger(log_level=logging.INFO, log_file=None):
    """
    로깅 설정을 초기화

    Args:
        log_level: 로깅 레벨
        log_file: 로그파일 경로, 없을 경우 콘솔에만 출력
    """

