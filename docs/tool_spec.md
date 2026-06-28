# 파이썬 도구 정의서 (Tool Specification)

이 문서는 ReAct 에이전트 프레임워크 내부 소스 코드(`src/tools/`)에서 에이전트에게 바인딩되는 파이썬 함수 도구(LangChain Tools)의 작성 규격 및 각 도구의 API 명세를 정의합니다.

## 도구(Tool) 작성 가이드라인

1. **데코레이터**: LangChain의 `@tool` 데코레이터(`from langchain_core.tools import tool`)를 필수 적용해야 합니다.
2. **타입 힌트**: 모든 매개변수에는 명시적인 Python 타입 힌트(예: `query: str`, `top_k: int = 3`)를 설정해야 합니다.
3. **독스트링(Docstring) 스타일**: 구글 스타일 독스트링을 준수하여 **용도 설명**, **인자 명세(Args)** 및 **반환 형식(Returns)**을 명확히 명시해야 합니다. LLM은 이 독스트링을 읽고 도구의 사용 시점과 반환값 파싱 방법을 파악합니다.
4. **에러 처리**: 도구 내부 실행 중 예외(Exception)가 발생할 경우, 크래시를 방지하기 위해 예외를 밖으로 던지지 말고 에러 내용을 명확한 문자열(String) 형태로 포착(catch)하여 에러 사유가 에이전트에 반환되도록 코드를 보호하십시오.

---

## 기본 탑재 도구 명세 (Built-in Tools Spec)

### 1. 로컬 업로드 파일 리더
- **이름**: `read_uploaded_file`
- **인자**: 
  - `file_path: str` (서버 로컬에 저장된 업로드 파일의 절대 경로)
- **반환값 (Returns)**: `str` (파일의 원시 텍스트 내용 전체. 파일 미존재 또는 읽기 에러 시 오류 정보 텍스트 반환)

### 2. Postgres 데이터베이스 쿼리
- **이름**: `query_postgres`
- **인자**: 
  - `query: str` (실행할 유효한 SQL SELECT/DDL/DML 쿼리)
- **반환값 (Returns)**: `str` (SELECT 결과물은 JSON 배열 형식의 문자열 `[{"col": "val"}]` 로 반환하며, DDL/DML 성공 상태는 `[{"status": "success", "message": "..."}]` 형태로 직렬화하여 반환. 쿼리 실패 시 에러 사유 문자열 반환)

### 3. Oracle 데이터베이스 쿼리
- **이름**: `query_oracle`
- **인자**: 
  - `query: str` (실행할 SQL SELECT 쿼리)
- **반환값 (Returns)**: `str` (JSON 배열 형식의 결과 리스트 문자열 반환. 실패 시 에러 사유 문자열 반환)

### 4. Milvus 벡터 DB 검색
- **이름**: `search_milvus`
- **인자**: 
  - `collection_name: str` (검색할 컬렉션 이름)
  - `query_vector: list[float]` (유사도 측정을 위한 쿼리 수치형 벡터)
  - `top_k: int = 3` (반환할 유사 문서 개수)
- **반환값 (Returns)**: `str` (유사 문서들의 id, score 및 메타데이터 필드가 담긴 JSON 배열 문자열 반환)

### 5. 일반 웹 검색
- **이름**: `general_web_search`
- **인자**: 
  - `query: str` (검색어)
- **반환값 (Returns)**: `str` (검색어에 매칭되는 결과 요약문 텍스트 반환)

### 6. 계산기
- **이름**: `calculator`
- **인자**: 
  - `expression: str` (평가할 수학 수식 표현식, 예: '2 * math.pi * 5')
- **반환값 (Returns)**: `str` (수식 연산 결과 수치값의 문자열 반환. 수식 결함이나 실행 실패 시 에러 텍스트 반환)

---

## 데이터 적재 및 스키마 빌더 도구 명세 (Data/DDL Spec Tools)

### 7. 테이블 생성 및 검증
- **이름**: `create_or_alter_table_from_file`
- **인자**:
  - `file_name: str` (업로드한 DDL 스키마 파일의 원본 이름, 예: 'schema.sql' 또는 'schema.json')
  - `file_content: str` (DDL 파일 내부의 원시 텍스트 스트링)
- **반환값 (Returns)**: `str` (테이블 신규 생성/수정 성공 메시지, 또는 스키마 정합성 불일치 시 에이전트 수정을 요청하는 오류 피드백 텍스트 반환)

### 8. 데이터 벌크 적재 (Upsert)
- **이름**: `upsert_data_from_json`
- **인자**:
  - `file_name: str` (업로드할 데이터 JSON 파일의 원본 이름, 예: 'weather_data.json')
  - `file_content: str` (데이터 JSON 파일 내부의 텍스트 본문)
- **설명**: 
  - **PK 자동 식별**: 도구가 DB 메타데이터에서 기본키(PK) 컬럼을 스스로 조회하여 Upsert 충돌 해결 키로 설정하므로, 데이터 JSON 내부의 records에는 `pk_column`과 같은 명시를 완전히 배제하여 전송해야 합니다.
- **반환값 (Returns)**: `str` (성공적으로 적재 완료된 건수 안내 메시지 반환. 테이블 미존재 혹은 제약조건 충돌 시 에러 텍스트 반환)

### 9. 날씨 상세 데이터 조회
- **이름**: `query_weather`
- **인자**:
  - `start_date: str` (조회 시작 일자, 포맷: 'YYYY-MM-DD')
  - `end_date: Optional[str] = None` (조회 종료 일자, 포맷: 'YYYY-MM-DD', 기본값은 시작일과 같음)
  - `condition: Optional[str] = None` (날씨 컨디션 조건 필터, 예: '맑음', '비' 등)
- **반환값 (Returns)**: `str` (조회 조건에 부합하는 날씨 레코드 행들의 JSON 배열 문자열 반환. 조회 실패 시 에러 텍스트 반환)
