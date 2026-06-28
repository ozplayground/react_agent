import os
import oracledb
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OracleConnector:
    """
    python-oracledb 라이브러리를 사용하여 Oracle 데이터베이스 연결 및 쿼리 실행을 관리합니다.
    연결이 실패하거나 모의 환경인 경우 Mock 응답으로 대체됩니다.
    """
    def __init__(self):
        self.user = settings.oracle_user
        self.password = settings.oracle_password
        self.dsn = settings.oracle_dsn
        self.conn = None
        self.use_mock = False

    def connect(self):
        # 로컬 테스트 환경이거나 플레이스홀더 기본값이 감지되면 Mock 모드로 작동
        if (self.user == "system" and self.password == "oracle" and not os.environ.get("ORACLE_LIVE_TEST")):
            logger.info("Oracle 커넥터가 모의(Mock) 모드로 초기화되었습니다 (기본 설정 감지).")
            self.use_mock = True
            return

        try:
            # Thin 모드로 연결 (기본값)
            self.conn = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            logger.info("Oracle 데이터베이스 연결에 성공했습니다.")
        except Exception as e:
            logger.warning(f"Oracle 연결 실패 ({e}). 모의(Mock) 모드로 전환합니다.")
            self.use_mock = True

    def execute_query(self, query: str) -> list:
        """
        Oracle 쿼리를 실행하고 결과를 반환합니다.
        """
        if self.use_mock or not self.conn:
            logger.info(f"[Mock Oracle] 쿼리 실행 시뮬레이션: '{query}'")
            return [
                {"EMPLOYEE_ID": 201, "FIRST_NAME": "Michael", "LAST_NAME": "Scott", "DEPARTMENT": "Management"},
                {"EMPLOYEE_ID": 202, "FIRST_NAME": "Jim", "LAST_NAME": "Halpert", "DEPARTMENT": "Sales"}
            ]

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                self.conn.commit()
                return [{"status": "success", "message": "성공적으로 명령을 처리했습니다."}]
        except Exception as e:
            logger.error(f"Oracle 쿼리 실행 실패: {e}")
            raise e

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Oracle 연결이 닫혔습니다.")
            self.conn = None
