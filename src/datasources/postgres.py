import os
import psycopg2
from sqlalchemy import create_engine
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PostgresConnector:
    """
    PostgreSQL 데이터베이스 연결 및 쿼리 실행을 관리합니다.
    SQLAlchemy 엔진 및 psycopg2 기본 커넥션을 모두 지원합니다.
    """
    def __init__(self):
        self.host = settings.postgres_host
        self.port = settings.postgres_port
        self.db = settings.postgres_db
        self.user = settings.postgres_user
        self.password = settings.postgres_password
        self.conn = None
        self.use_mock = False
        
        # SQLAlchemy 데이터베이스 URL 포맷팅
        self.db_url = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    def connect(self):
        # POSTGRES_LIVE_TEST 환경변수가 'true'일 경우에만 실제 데이터베이스에 접속 시도
        is_live = os.environ.get("POSTGRES_LIVE_TEST", "").lower() == "true"
        if not is_live:
            logger.info("PostgreSQL 커넥터가 모의(Mock) 모드로 초기화되었습니다 (POSTGRES_LIVE_TEST가 비활성화됨).")
            self.use_mock = True
            return

        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.db,
                user=self.user,
                password=self.password,
                connect_timeout=3
            )
            logger.info("PostgreSQL 데이터베이스 연결에 성공했습니다.")
        except Exception as e:
            logger.warning(f"PostgreSQL 연결 실패 ({e}). 모의(Mock) 모드로 전환합니다.")
            self.use_mock = True

    def get_engine(self):
        """
        SQLAlchemy Engine 인스턴스를 반환합니다.
        """
        logger.info(f"SQLAlchemy 엔진을 생성합니다: {self.host}:{self.port}/{self.db}")
        return create_engine(self.db_url)

    def execute_query(self, query: str) -> list:
        """
        SELECT 쿼리를 실행하고 결과를 딕셔너리 리스트 형태로 반환합니다.
        """
        if self.use_mock or not self.conn:
            logger.info(f"[Mock PostgreSQL] 쿼리 실행 시뮬레이션: '{query}'")
            return [
                {"id": 101, "username": "agent_user", "email": "agent@example.com", "status": "active"},
                {"id": 102, "username": "test_developer", "email": "dev@example.com", "status": "inactive"}
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
            logger.error(f"PostgreSQL 쿼리 실행 실패: {e}")
            raise e

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL 연결이 닫혔습니다.")
            self.conn = None
