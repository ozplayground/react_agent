import json
import os
import datetime
from typing import Optional
import pandas as pd
import numpy as np
from sqlalchemy import inspect, Table, Column, MetaData, Integer, Float, String, Date, text, select, and_
from sqlalchemy.dialects.postgresql import insert
from langchain_core.tools import tool
from src.datasources import PostgresConnector, OracleConnector, MilvusConnector
from src.utils import get_logger

logger = get_logger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """
    datetime.date 및 datetime.datetime 객체를 JSON 문자열로 직렬화할 수 있게 도와줍니다.
    """
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

@tool
def read_uploaded_file(file_path: str) -> str:
    """
    서버 로컬 디렉토리(uploads 등)에 업로드되어 저장된 파일의 절대 경로(file_path)를 수신하여 파일 전체 내용을 텍스트 문자열로 읽어서 반환합니다.
    에이전트가 사용자가 업로드한 원천 CSV 데이터나 DDL JSON 스키마 파일을 분석하여 다른 도구로 전달하기 전에 파일 내용을 조회할 때 이 도구를 반드시 사용해야 합니다.

    Args:
        file_path (str): 서버에 저장된 업로드 파일의 절대 경로.

    Returns:
        str: 파일의 원시 텍스트 전체 내용. 파일이 존재하지 않거나 읽기 실패 시 오류 메시지를 반환합니다.
    """
    logger.info(f"read_uploaded_file 도구가 호출되었습니다. 경로: '{file_path}'")
    try:
        if not os.path.exists(file_path):
            return f"오류: 지정한 파일 경로 '{file_path}'가 존재하지 않습니다."
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"read_uploaded_file 도구 실행 중 오류 발생: {e}")
        return f"파일을 읽는 중 오류가 발생했습니다: {str(e)}"

@tool
def query_postgres(query: str) -> str:
    """
    PostgreSQL 데이터베이스에서 SQL 쿼리(SELECT, CREATE TABLE, INSERT, ALTER 등)를 실행하고 결과를 JSON 문자열로 반환합니다.
    에이전트가 데이터를 분석하여 생성한 테이블 DDL(생성, 코멘트 지정, 인덱스 생성)을 직접 실행하거나 데이터를 조회할 때 이 도구를 사용합니다.

    Args:
        query (str): 실행할 유효한 SQL 쿼리문.

    Returns:
        str: SELECT 쿼리의 경우 JSON 배열 형식의 결과 리스트(예: '[{"col": "val"}]')를 반환하며, DDL/DML 등 성공 상태는 '[{"status": "success", "message": "..."}]', 실행 실패 시 에러 메시지를 문자열로 반환합니다.
    """
    logger.info(f"query_postgres 도구가 호출되었습니다. 쿼리: '{query}'")
    try:
        connector = PostgresConnector()
        connector.connect()
        results = connector.execute_query(query)
        connector.close()
        return json.dumps(results, cls=DateTimeEncoder, ensure_ascii=False)
    except Exception as e:
        logger.error(f"query_postgres 도구 실행 중 오류 발생: {e}")
        return f"PostgreSQL 쿼리 실행 중 오류가 발생했습니다: {str(e)}"

@tool
def query_oracle(query: str) -> str:
    """
    Oracle 데이터베이스에서 SQL SELECT 쿼리를 실행하고 행 결과를 JSON 문자열로 반환합니다.
    Oracle 데이터베이스에서 전사 사원 목록, 부서 정보, 또는 기업 데이터를 조회할 때 이 도구를 사용합니다.

    Args:
        query (str): 실행할 유효한 SQL SELECT 쿼리문.

    Returns:
        str: JSON 배열 형식의 행 결과 데이터 문자열(예: '[{"EMP_ID": 100, ...}]'). 쿼리 실패 시 에러 메시지를 반환합니다.
    """
    logger.info(f"query_oracle 도구가 호출되었습니다. 쿼리: '{query}'")
    try:
        connector = OracleConnector()
        connector.connect()
        results = connector.execute_query(query)
        connector.close()
        return json.dumps(results, cls=DateTimeEncoder, ensure_ascii=False)
    except Exception as e:
        logger.error(f"query_oracle 도구 실행 중 오류 발생: {e}")
        return f"Oracle 쿼리 실행 중 오류가 발생했습니다: {str(e)}"

@tool
def search_milvus(collection_name: str, query_vector: list[float], top_k: int = 3) -> str:
    """
    Milvus 벡터 데이터베이스의 특정 컬렉션에서 유사도 검색을 수행하고 가장 유사한 결과 및 메타데이터를 JSON 문자열로 반환합니다.
    Milvus 벡터 데이터베이스 컬렉션에서 의미적으로 관련된 지식 문서나 문서 본문을 조회할 때 이 도구를 사용합니다.

    Args:
        collection_name (str): Milvus에 등록된 컬렉션 이름.
        query_vector (list[float]): 검색할 수치형 쿼리 벡터.
        top_k (int, optional): 반환할 상위 결과 개수. 기본값은 3.

    Returns:
        str: 유사 문서의 id, score 및 메타데이터 필드가 포함된 JSON 배열 문자열. 검색 실패 시 에러 메시지를 반환합니다.
    """
    logger.info(f"search_milvus 도구가 호출되었습니다. 컬렉션: '{collection_name}', 벡터 길이: {len(query_vector)}")
    try:
        connector = MilvusConnector()
        connector.connect()
        results = connector.search_vectors(collection_name, query_vector, top_k)
        connector.close()
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"search_milvus 도구 실행 중 오류 발생: {e}")
        return f"Milvus 벡터 검색 중 오류가 발생했습니다: {str(e)}"

@tool
def create_or_alter_table_from_file(file_name: str, file_content: str) -> str:
    """
    업로드된 DDL 파일의 이름과 텍스트 내용(file_content)을 수신하여 PostgreSQL 데이터베이스에 테이블을 생성하거나 스키마 정합성을 검증합니다.
    JSON 형식 스키마 파일(.json)일 경우 DDL에 포함되는 모든 정보(table_name, columns, table_comment, indexes)가 기술되어야 합니다.

    Args:
        file_name (str): 업로드한 스키마 DDL 파일의 이름 (예: 'weather_schema.json' 또는 'schema.sql').
        file_content (str): 업로드한 스키마 파일의 원시 텍스트 내용.

    Returns:
        str: 스키마 생성 성공 안내 결과 메시지(예: '성공적으로... 생성했습니다'), 또는 스키마 정합성 불일치(컬럼 누락) 발생 시 에이전트(LLM)에 알리는 ALTER DDL 지시어 오류 피드백 문자열을 반환합니다.
    """
    logger.info(f"create_or_alter_table_from_file 호출됨: 파일명={file_name}")
    
    connector = PostgresConnector()
    connector.connect()
    
    # 모의(Mock) 환경 대응
    if connector.use_mock:
        logger.info("[Mock Mode] 테이블 생성/수정 업로드 성공 시뮬레이션 수행.")
        connector.close()
        return f"성공적으로 모의(Mock) 환경에서 스키마 파일 '{file_name}' 내용의 업로드 및 테이블 생성을 완료했습니다."
        
    try:
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()
        
        engine = connector.get_engine()
        inspector = inspect(engine)
        
        # 1. SQL DDL 파일 처리 분기
        if ext == ".sql":
            logger.info("업로드된 원시 SQL DDL 내용을 실행합니다.")
            with engine.begin() as conn:
                conn.execute(text(file_content))
            connector.close()
            return f"성공적으로 SQL DDL 파일 '{file_name}' 내용을 업로드하여 데이터베이스에 실행 완료했습니다."
            
        # 2. JSON 스키마 DDL 파일 처리 분기
        elif ext == ".json":
            schema_data = json.loads(file_content)
                
            table_name = schema_data.get("table_name")
            table_comment = schema_data.get("table_comment", "")
            columns = schema_data.get("columns", [])
            indexes = schema_data.get("indexes", [])
            
            if not table_name or not columns:
                connector.close()
                return "오류: 업로드된 JSON 내용에 'table_name' 또는 'columns' 정보가 누락되어 있습니다."
                
            # 테이블 존재 여부 검사
            table_exists = inspector.has_table(table_name)
            
            if not table_exists:
                # 테이블 신규 생성 DDL 조립
                logger.info(f"JSON 사양을 기반으로 테이블 '{table_name}'을 신규 생성합니다.")
                ddl_parts = [f"CREATE TABLE {table_name} ("]
                col_defs = []
                for col in columns:
                    name = col.get("name")
                    col_type = col.get("type", "VARCHAR(255)")
                    pk = col.get("primary_key", False)
                    nullable = col.get("nullable", True)
                    
                    pk_str = " PRIMARY KEY" if pk else ""
                    null_str = " NOT NULL" if not nullable else " NULL"
                    col_defs.append(f"    {name} {col_type}{pk_str}{null_str}")
                    
                ddl_parts.append(",\n".join(col_defs))
                ddl_parts.append(");")
                
                # 코멘트 DDL 추가
                if table_comment:
                    ddl_parts.append(f"COMMENT ON TABLE {table_name} IS '{table_comment}';")
                for col in columns:
                    name = col.get("name")
                    comment = col.get("comment", "")
                    if comment:
                        ddl_parts.append(f"COMMENT ON COLUMN {table_name}.{name} IS '{comment}';")
                        
                # 인덱스 DDL 추가
                for idx in indexes:
                    idx_name = idx.get("name")
                    idx_cols = ", ".join(idx.get("columns", []))
                    if idx_name and idx_cols:
                        ddl_parts.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx_cols});")
                        
                final_ddl = "\n".join(ddl_parts)
                logger.info(f"조립된 DDL 실행:\n{final_ddl}")
                with engine.begin() as conn:
                    conn.execute(text(final_ddl))
                connector.close()
                return f"성공적으로 JSON 스키마 파일 '{file_name}' 내용을 업로드 및 분석하여 테이블 '{table_name}'을 신규 생성했습니다."
            else:
                # 테이블이 존재하므로 컬럼 대조 (Alter 검증 피드백 루프)
                existing_cols = {c["name"]: c for c in inspector.get_columns(table_name)}
                json_col_names = [col.get("name") for col in columns]
                missing_cols = [c for c in json_col_names if c not in existing_cols]
                
                if missing_cols:
                    existing_schema_str = ", ".join([f"{col}: {str(info['type'])}" for col, info in existing_cols.items()])
                    connector.close()
                    return f"테이블 스키마 변경 필요: 기존 테이블 '{table_name}'에 신규 컬럼 {missing_cols}이 누락되어 있습니다. 현재 DB 테이블 스키마는 [{existing_schema_str}] 입니다. 에이전트(LLM)는 이 정보를 바탕으로 누락 컬럼 {missing_cols}를 추가하는 ALTER TABLE DDL 쿼리가 적힌 SQL 파일 또는 누락 컬럼이 보완된 JSON/SQL 파일을 새로 작성 및 업로드하여 이 툴을 재호출하거나 query_postgres로 스키마를 Alter 하십시오."
                
                connector.close()
                return f"테이블 '{table_name}'이 이미 JSON 스키마 명세와 완벽하게 일치하는 상태입니다. DDL 추가 실행이 불필요합니다."
        else:
            connector.close()
            return f"오류: 지원하지 않는 파일 형식 '{ext}' 입니다. DDL 스키마 파일은 .sql 또는 .json 형식이어야 합니다."
            
    except Exception as e:
        logger.error(f"create_or_alter_table_from_file 도구 실행 실패: {e}")
        connector.close()
        return f"테이블 생성 및 검증 중 오류 발생: {str(e)}"

@tool
def upsert_data_from_json(file_name: str, file_content: str) -> str:
    """
    업로드된 JSON 데이터 파일의 이름과 텍스트 내용(file_content)을 수신하여 PostgreSQL 데이터베이스에 데이터를 Upsert 적재합니다.
    JSON 데이터 안에는 'table_name', 'records'(데이터 목록) 정보가 반드시 포함되어야 하며, 기본키(PK) 컬럼은 테이블 정의에서 자동으로 찾아 매핑합니다.
    대상 테이블이 데이터베이스에 미리 생성되어 존재하지 않을 경우 에러를 반환합니다.

    Args:
        file_name (str): 업로드한 데이터 JSON 파일의 이름 (예: 'weather_data.json').
        file_content (str): 업로드한 데이터 JSON 파일의 내용.

    Returns:
        str: 데이터 적재 성공 건수 결과 안내 메시지 (예: '성공적으로 테이블... 212건의 레코드를... 완료했습니다'). 실패 시 에러 사유를 문자열로 반환합니다.
    """
    logger.info(f"upsert_data_from_json 호출됨: 파일명={file_name}")
    
    connector = PostgresConnector()
    connector.connect()
    
    # 모의(Mock) 환경 대응
    if connector.use_mock:
        logger.info("[Mock Mode] 데이터 JSON 업로드 및 적재 성공 시뮬레이션 수행.")
        connector.close()
        return f"성공적으로 모의(Mock) 환경에서 데이터 파일 '{file_name}'의 업로드 및 적재(Upsert) 완료했습니다."
        
    try:
        data = json.loads(file_content)
            
        table_name = data.get("table_name")
        records = data.get("records", [])
        
        if not table_name or not records:
            connector.close()
            return "오류: JSON 데이터에 'table_name' 또는 'records'가 누락되어 있습니다."
            
        engine = connector.get_engine()
        inspector = inspect(engine)
        
        # 2. 테이블 존재 여부 검사
        if not inspector.has_table(table_name):
            connector.close()
            return f"오류: '{table_name}' 테이블이 데이터베이스에 존재하지 않습니다. 먼저 create_or_alter_table_from_file 도구를 호출하여 테이블을 정상 생성한 후에 데이터 적재를 시도해야 합니다."
            
        # 3. 데이터 적재(Upsert) 실행
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = Table(table_name, metadata, autoload_with=engine)
        
        # 테이블의 기본키(PK) 컬럼명 자동 추출
        pk_columns = [key for key in table.primary_key.columns.keys()]
        if not pk_columns:
            connector.close()
            return f"오류: '{table_name}' 테이블에 정의된 기본키(Primary Key)가 존재하지 않습니다. PK가 사전에 생성되어 있어야 Upsert 처리가 작동합니다."
        pk_column = pk_columns[0]
        logger.info(f"테이블 '{table_name}'의 기본키(PK) 컬럼을 자동으로 식별했습니다: '{pk_column}'")
        
        upsert_count = 0
        with engine.begin() as conn:
            for record in records:
                clean_record = {}
                for k, v in record.items():
                    if pd.isna(v):
                        clean_record[k] = None
                    else:
                        clean_record[k] = v
                
                stmt = insert(table).values(clean_record)
                update_dict = {c.name: c for c in stmt.excluded if c.name != pk_column}
                
                # Upsert 문법 적용
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=[pk_column],
                    set_=update_dict
                )
                conn.execute(upsert_stmt)
                upsert_count += 1
                
        connector.close()
        return f"성공적으로 테이블 '{table_name}'에 {upsert_count}건의 레코드를 JSON 데이터 파일 '{file_name}' 기반으로 업로드 및 적재(Upsert) 완료했습니다."
        
    except Exception as e:
        logger.error(f"upsert_data_from_json 도구 실행 실패: {e}")
        connector.close()
        return f"데이터 Upsert 적재 중 오류 발생: {str(e)}"

@tool
def query_weather(start_date: str, end_date: Optional[str] = None, condition: Optional[str] = None) -> str:
    """
    PostgreSQL 데이터베이스의 날씨 상세 데이터 테이블(weather_data)에서 특정 날짜 범위 및 기상 조건 필터를 만족하는 레코드를 조회하여 JSON 문자열로 반환합니다.

    Args:
        start_date (str): 조회 시작 날짜 (포맷: 'YYYY-MM-DD', 예: '2026-06-01').
        end_date (str, optional): 조회 종료 날짜 (포맷: 'YYYY-MM-DD', 예: '2026-06-07'). 지정하지 않으면 시작 날짜 하루만 조회합니다.
        condition (str, optional): 기상 조건 필터 (예: '맑음', '흐림', '비' 등).

    Returns:
        str: 조회된 레코드 행 리스트가 직렬화된 JSON 배열 문자열 (예: '[{"date": "2026-06-01", "min_temp": 15.2, ...}]'). 오류 시 오류 메시지를 반환합니다.
    """
    logger.info(f"query_weather 호출됨: start={start_date}, end={end_date}, condition={condition}")
    
    connector = PostgresConnector()
    connector.connect()
    
    # 모의(Mock) 환경 대응
    if connector.use_mock:
        logger.info("[Mock Mode] 날씨 데이터 조회 시뮬레이션 수행.")
        connector.close()
        return json.dumps([
            {"date": start_date, "min_temp": 15.2, "max_temp": 24.5, "condition": condition or "맑음", "precipitation_probability": 10.0, "precipitation": 0.0, "snowfall": 0.0, "wind_speed": 3.2, "wind_direction": "북서풍"},
            {"date": end_date or start_date, "min_temp": 16.0, "max_temp": 22.0, "condition": condition or "흐림", "precipitation_probability": 30.0, "precipitation": 0.5, "snowfall": 0.0, "wind_speed": 4.5, "wind_direction": "남풍"}
        ], ensure_ascii=False)
        
    try:
        engine = connector.get_engine()
        metadata = MetaData()
        
        inspector = inspect(engine)
        table_name = "weather_data"
        if not inspector.has_table(table_name):
            connector.close()
            return f"오류: '{table_name}' 테이블이 아직 데이터베이스에 존재하지 않습니다. 먼저 파일을 업로드하여 테이블을 생성하십시오."
            
        metadata.reflect(bind=engine)
        table = Table(table_name, metadata, autoload_with=engine)
        
        # SELECT 쿼리 생성
        query = select(table)
        conditions = []
        
        if start_date:
            conditions.append(table.c.date >= start_date)
        if end_date:
            conditions.append(table.c.date <= end_date)
        else:
            conditions.append(table.c.date == start_date)
            
        if condition:
            conditions.append(table.c.condition == condition)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        # 날짜 순 정렬
        query = query.order_by(table.c.date.asc())
        
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = []
            for row in result:
                row_dict = {}
                for idx, col in enumerate(result.keys()):
                    val = row[idx]
                    # Date/Datetime 등 JSON 직렬화 불가 타입 변환
                    if isinstance(val, (pd.Timestamp, np.datetime64, type(pd.to_datetime('2026-01-01').date()))):
                        row_dict[col] = str(val)
                    elif hasattr(val, "isoformat"):
                        row_dict[col] = val.isoformat()
                    else:
                        row_dict[col] = val
                rows.append(row_dict)
                
        connector.close()
        return json.dumps(rows, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"query_weather 실행 실패: {e}")
        connector.close()
        return f"날씨 데이터 조회 중 오류 발생: {str(e)}"
