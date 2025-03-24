import logging
import os

# 로그 디렉토리 생성
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 기본 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 파일 핸들러 추가 (로그 파일 저장)
log_file = os.path.join(log_dir, "app.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 콘솔 핸들러 추가 (터미널에 로그 출력)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# 로그 포맷 설정
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# 핸들러 추가 (중복 추가 방지)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)