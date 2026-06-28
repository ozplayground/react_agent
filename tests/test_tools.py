import os
import json
import pytest
from src.tools import (
    read_uploaded_file,
    query_postgres,
    query_oracle,
    search_milvus,
    calculator,
    general_web_search,
    create_or_alter_table_from_file,
    upsert_data_from_json,
    query_weather
)

def test_query_postgres_tool():
    """
    query_postgres 도구가 호출되었을 때 결과의 반환 형태 및 내용을 검증합니다.
    """
    res = query_postgres.invoke({"query": "SELECT * FROM users;"})
    assert isinstance(res, str)
    data = json.loads(res)
    assert len(data) > 0
    assert data[0]["username"] == "agent_user"

def test_query_oracle_tool():
    """
    query_oracle 도구의 호출을 검증합니다.
    """
    res = query_oracle.invoke({"query": "SELECT * FROM departments;"})
    assert isinstance(res, str)
    data = json.loads(res)
    assert len(data) > 0
    assert data[0]["FIRST_NAME"] == "Michael"

def test_search_milvus_tool():
    """
    search_milvus 도구의 호출을 검증합니다.
    """
    res = search_milvus.invoke({
        "collection_name": "ai_documents",
        "query_vector": [0.1, 0.2, 0.3],
        "top_k": 2
    })
    assert isinstance(res, str)
    data = json.loads(res)
    assert len(data) == 3
    assert data[0]["id"] == 1001

def test_calculator_tool_valid():
    """
    올바른 수학 식이 전달되었을 때 계산기 도구가 정확한 연산을 수행하는지 검증합니다.
    """
    res = calculator.invoke({"expression": "2**8 - 5"})
    assert res == "251"
    
    res = calculator.invoke({"expression": "math.sqrt(16) * 10"})
    assert res == "40.0"

def test_calculator_tool_error():
    """
    잘못된 수학 식이나 정의되지 않은 변수 접근 시 계산기 도구가 에러 메시지를 잘 반환하는지 검증합니다.
    """
    res = calculator.invoke({"expression": "some_undefined_variable * 5"})
    assert "수학 식 평가 중 오류가 발생했습니다" in res

def test_general_web_search_tool():
    """
    특정 키워드 쿼리에 대해 알맞은 모의 응답이 반환되는지 검증합니다.
    """
    res_weather = general_web_search.invoke({"query": "오늘 날씨 어때?"})
    assert "화창하며" in res_weather
    
    res_lg = general_web_search.invoke({"query": "Tell me about langgraph"})
    assert "LangGraph" in res_lg
    
    res_other = general_web_search.invoke({"query": "42가 무엇인가요?"})
    assert "검색 결과" in res_other

def test_create_or_alter_table_from_file_tool_mock():
    """
    create_or_alter_table_from_file 도구가 mock 모드에서 성공 메시지를 올바르게 반환하는지 테스트합니다.
    """
    res = create_or_alter_table_from_file.invoke({
        "file_name": "weather_schema.json",
        "file_content": "{}"
    })
    assert "성공적으로" in res
    assert "weather_schema.json" in res

def test_upsert_data_from_json_tool_mock():
    """
    upsert_data_from_json 도구가 mock 모드에서 성공 메시지를 올바르게 반환하는지 테스트합니다.
    """
    res = upsert_data_from_json.invoke({
        "file_name": "weather_data.json",
        "file_content": "{}"
    })
    assert "성공적으로" in res
    assert "weather_data.json" in res

def test_query_weather_tool_mock():
    """
    query_weather 도구가 mock 모드에서 날씨 JSON 데이터를 정상적으로 리턴하는지 테스트합니다.
    """
    res = query_weather.invoke({
        "start_date": "2026-06-01",
        "end_date": "2026-06-02",
        "condition": "맑음"
    })
    assert isinstance(res, str)
    data = json.loads(res)
    assert len(data) > 0
    assert data[0]["date"] == "2026-06-01"

def test_read_uploaded_file_tool(tmp_path):
    """
    read_uploaded_file 도구가 주어진 경로의 파일 내용을 정확히 문자열로 읽는지 검증합니다.
    """
    test_file = tmp_path / "test_file.txt"
    test_content = "Hello, world! This is a test upload content."
    test_file.write_text(test_content, encoding="utf-8")
    
    res = read_uploaded_file.invoke({"file_path": str(test_file)})
    assert res == test_content
    
    # 존재하지 않는 경로 테스트
    res_error = read_uploaded_file.invoke({"file_path": "/invalid/path/to/file.txt"})
    assert "오류:" in res_error
