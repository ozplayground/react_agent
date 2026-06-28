import os
import pytest
from unittest.mock import patch, MagicMock
from src.datasources import PostgresConnector, OracleConnector, MilvusConnector

def test_postgres_connector_mock_fallback():
    """
    기본 자격 증명(localhost/postgres)이 사용될 때 PostgresConnector가 모의(Mock) 모드로 잘 전환되는지 테스트합니다.
    """
    connector = PostgresConnector()
    connector.connect()
    assert connector.use_mock is True
    
    res = connector.execute_query("SELECT * FROM mock_table")
    assert len(res) == 2
    assert res[0]["username"] == "agent_user"
    connector.close()

@patch("psycopg2.connect")
@patch.dict(os.environ, {"POSTGRES_LIVE_TEST": "true"})
def test_postgres_connector_real_connection(mock_connect):
    """
    사용자 정의 자격 증명이 주어졌을 때 PostgresConnector가 psycopg2 라이브러리를 정상 호출하는지 테스트합니다.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # 모의 커서의 조회 결과 설정
    mock_cursor.description = [("id",), ("name",)]
    mock_cursor.fetchall.return_value = [(999, "Real Postgres Row")]
    
    connector = PostgresConnector()
    # Mock 분기를 타지 않도록 임의의 접속 정보 설정
    connector.host = "production-pg-server.internal"
    connector.password = "super-secret-pw"
    
    connector.connect()
    assert connector.use_mock is False
    
    res = connector.execute_query("SELECT id, name FROM real_table")
    assert res == [{"id": 999, "name": "Real Postgres Row"}]
    connector.close()

def test_oracle_connector_mock_fallback():
    """
    OracleConnector가 기본 자격 증명 감지 시 모의(Mock) 모드로 잘 작동하는지 테스트합니다.
    """
    connector = OracleConnector()
    connector.connect()
    assert connector.use_mock is True
    
    res = connector.execute_query("SELECT * FROM employees")
    assert len(res) == 2
    assert res[0]["FIRST_NAME"] == "Michael"
    connector.close()

@patch("oracledb.connect")
@patch.dict(os.environ, {"ORACLE_LIVE_TEST": "true"})
def test_oracle_connector_real_connection(mock_connect):
    """
    접속 정보가 기본값과 다를 때 OracleConnector가 실제 드라이버 연결을 시도하는지 테스트합니다.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    mock_cursor.description = [("EMPLOYEE_ID",), ("FIRST_NAME",)]
    mock_cursor.fetchall.return_value = [(77, "Pam")]
    
    connector = OracleConnector()
    connector.user = "admin_user"
    connector.password = "secure_oracle_pw"
    
    connector.connect()
    assert connector.use_mock is False
    
    res = connector.execute_query("SELECT EMPLOYEE_ID, FIRST_NAME FROM employees")
    assert res == [{"EMPLOYEE_ID": 77, "FIRST_NAME": "Pam"}]
    connector.close()

def test_milvus_connector_mock_fallback():
    """
    MilvusConnector가 모의(Mock) 검색 결과를 올바르게 변환하는지 테스트합니다.
    """
    connector = MilvusConnector()
    connector.connect()
    assert connector.use_mock is True
    
    res = connector.search_vectors("my_collection", [0.15, -0.42, 0.98])
    assert len(res) == 3
    assert res[0]["id"] == 1001
    assert "LangGraph Documentation" in res[0]["metadata"]["title"]
    connector.close()
