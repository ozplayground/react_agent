import logging
import os
import sys

def get_logger(name: str) -> logging.Logger:
    """
    구조화된 로그를 표준 출력(stdout) 및 %project_root%/logs/agent.log 파일에 기록하는 로거를 반환합니다.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 로그 메시지 포맷 설정
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 1. 표준 출력 스트림 핸들러
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)
        
        # 2. 파일 로그 핸들러 (%project_root%/logs/agent.log)
        try:
            # 파일 경로 역추적: src/utils/logger.py -> src/utils -> src -> project_root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            project_root = os.path.dirname(src_dir)
            
            logs_dir = os.path.join(project_root, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            log_filepath = os.path.join(logs_dir, "agent.log")
            file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # 파일 로거 생성 실패 시 콘솔에 에러 내용 출력
            print(f"파일 로거 초기화 실패: {e}", file=sys.stderr)
            
    return logger
