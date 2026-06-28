import os
import pytest

# 테스트 러너 기동 시, 데이터베이스 라이브 접속 변수들을 강제로 비활성화(false)합니다.
# 이를 통해 로컬 PC에 실제 DB 서버가 기동 중이더라도 단위 테스트는 항상 일관되게 Mock 모드로 통과합니다.
os.environ["POSTGRES_LIVE_TEST"] = "false"
os.environ["ORACLE_LIVE_TEST"] = "false"
os.environ["MILVUS_LIVE_TEST"] = "false"
