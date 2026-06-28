# react_agent

이 파일은 `react_agent` 프로젝트에서 작업하는 AI 코딩 에이전트(Claude Code, Antigravity 등)의 **행동 기준**을 정의한다. 프로젝트 구조 파악보다 **무엇을 해야 하고, 무엇을 하면 안 되며, 언제 멈춰야 하는지**를 우선적으로 숙지한다.

---

## 작업 전 필수 확인 (Agent Onboarding Checklist)

작업을 시작하기 전 아래 항목을 **순서대로** 확인한다. 확인되지 않은 항목이 있으면 사용자에게 질문한 후 진행한다.

### 1. 환경 파악
- [ ] `src/` 디렉토리 구조를 파악했는가?
- [ ] `.env` 파일의 `LLM_PROVIDER` 값을 확인했는가?
- [ ] `requirements.txt` 에서 현재 설치된 패키지 버전을 확인했는가? (LangGraph v0.3.3 호환 여부)
- [ ] `./run.sh test` 를 실행해 작업 시작 전 기존 테스트가 모두 통과하는 상태인지 확인했는가?

### 2. 작업 범위 및 영향 분석
- [ ] 이 작업이 직접 변경하는 파일 목록을 파악했는가?
- [ ] 직접 변경 외에 **연쇄적으로 영향을 받는 파일**이 있는지 확인했는가?
  - Tool 변경 → `src/workflows/agent.py` tools 리스트, `tests/`, `docs/tool_spec.md`
  - AgentState 변경 → StateGraph 노드/엣지 전체, 관련 테스트
  - DB 커넥터 변경 → 해당 커넥터를 호출하는 Tool 전체
  - `config.py` 변경 → 환경변수를 참조하는 모든 모듈
- [ ] 변경 대상 파일이 테스트 필수 대상인지 판단했는가?
- [ ] 작업 완료 후 동기화가 필요한 `docs/` 파일과 `README.md` 를 미리 파악했는가?

### 3. 즉시 중단 조건 사전 점검
아래 항목 중 하나라도 해당하면 작업을 시작하지 않고 사용자에게 먼저 확인한다.
- [ ] 기존 Tool의 함수 시그니처(파라미터명, 타입, 반환 포맷)를 변경해야 하는가?
- [ ] `AgentState` 구조를 변경해야 하는가?
- [ ] StateGraph의 노드 또는 엣지 로직(`should_continue`)을 변경해야 하는가?
- [ ] 새로운 DB 커넥터를 추가해야 하는가?
- [ ] `.env` 에 새 환경변수를 추가해야 하는가?
- [ ] 기존 테스트 케이스를 삭제하거나 수정해야 하는가?

### 4. 의존성 및 충돌 확인
- [ ] 변경하려는 Tool이 다른 Tool의 출력을 입력으로 받는 체인 관계인지 확인했는가?
  - 예: `read_uploaded_file` → `create_or_alter_table_from_file` → `upsert_data_from_json`
- [ ] 변경 대상 모듈이 `__init__.py` 의 `__all__` 에 공개된 인터페이스인지 확인했는가?
- [ ] 동일한 기능을 수행하는 기존 Tool이나 유틸리티가 이미 존재하지 않는지 확인했는가?
- [ ] 추가하려는 패키지가 `requirements.txt` 에 이미 있는지, LangGraph v0.3.3 과 호환되는지 확인했는가?

---

## 즉시 중단하고 사용자에게 확인해야 하는 상황

다음 상황에서는 **임의로 판단하지 말고 반드시 멈추고 확인**한다.

- 기존 Tool의 함수 시그니처(파라미터명, 타입, 반환 포맷)를 변경하려 할 때
- `AgentState` 구조를 변경하려 할 때
- 새로운 DB 커넥터를 추가하려 할 때
- `.env` 에 새 환경변수를 추가해야 할 때
- `src/workflows/agent.py`의 StateGraph 엣지 로직을 변경하려 할 때
- 기존 테스트 케이스를 삭제하거나 수정하려 할 때

---

## 절대 하지 말아야 할 것 (Hard Rules)

위반 시 전체 파이프라인이 깨진다.

| 금지 행동 | 이유 |
|---|---|
| 글로벌 변수 / 싱글톤에 대화 상태 저장 | AgentState가 유일한 상태 채널 |
| LLM 응답에 커스텀 XML/JSON 파서 작성 | LangChain tool_calls 처리 기능과 충돌 |
| 상대경로 import 사용 (`from .state import ...`) | 패키지 간 순환참조 유발 |
| DB 커넥터에서 예외 throw | 에이전트 루프 크래시 — 반드시 문자열로 반환 |
| Tool 반환값을 str 이외 타입으로 변경 | LangGraph ToolMessage 직렬화 오류 |
| 시스템 프롬프트를 캐싱하거나 정적 고정 | 매 agent 노드 호출 시 동적 렌더링 필수 |
| 코드 내 자격증명 하드코딩 | `.env` + pydantic-settings 통해서만 로드 |

---

## 프로젝트 구조

```
react_agent/
├── docs/                        # 설계 문서 — 코드 변경 시 에이전트가 동기화 책임
│   ├── project_context.md       # 프로젝트 구조 및 아키텍처 제약
│   ├── agent_architecture.md    # ReAct StateGraph 설계
│   └── tool_spec.md             # Tool API 명세
├── logs/agent.log               # 런타임 로그
├── uploads/                     # 사용자 업로드 파일 보관소
├── src/
│   ├── main.py                  # FastAPI 엔트리, SSE 스트리밍 라우터
│   ├── config.py                # pydantic-settings 기반 .env 로더
│   ├── workflows/
│   │   ├── agent.py             # StateGraph, get_model 팩토리, should_continue 엣지
│   │   └── state.py             # AgentState 정의
│   ├── tools/                   # @tool 함수 모음
│   ├── datasources/             # DB 커넥터 (Postgres / Oracle / Milvus)
│   └── utils/                   # 로거 등 공통 유틸
├── tests/                       # Pytest 단위 테스트
├── .env                         # 자격증명 및 Provider 제어 (git 제외)
├── requirements.txt
└── run.sh                       # serve / ui / test 통합 스크립트
```

**`docs/` 하위 파일은 코드와 항상 동기화되어야 한다. 관련 코드를 변경한 에이전트가 직접 업데이트한다.**

| 변경 내용 | 업데이트할 docs 파일 |
|---|---|
| Tool 추가 / 인터페이스 변경 | `tool_spec.md` |
| StateGraph 노드/엣지 변경, AgentState 변경 | `agent_architecture.md` |
| 디렉토리 구조, Provider, Import 규칙 변경 | `project_context.md` |
| API 엔드포인트, 환경변수, DB 커넥터 변경 | `project_context.md` + `README.md` |

---

## 기술 스택

| 구분 | 내용 |
|---|---|
| 런타임 | Python 3.11 |
| 웹 프레임워크 | FastAPI + Uvicorn (비동기 SSE 스트리밍) |
| 에이전트 오케스트레이션 | LangGraph v0.3.3 |
| LLM 프레임워크 | LangChain (LangGraph v0.3.3 호환) |
| DB — RDB | PostgreSQL (SQLAlchemy + psycopg2-binary) |
| DB — RDB | Oracle (python-oracledb Thin 드라이버) |
| DB — Vector | Milvus (pymilvus) |

---

## 실행 명령어

```bash
./run.sh serve    # FastAPI 기동 (Uvicorn)
./run.sh ui       # Streamlit UI 기동
./run.sh test     # Pytest 전체 실행
```

---

## LLM Provider

`.env`의 `LLM_PROVIDER` = `openai` | `gemini` | `local` 으로 런타임에 동적 전환.

```dotenv
LLM_PROVIDER=openai

OPENAI_API_KEY=...
OPENAI_MODEL_NAME=gpt-4o
OPENAI_TEMPERATURE=0.0

GEMINI_API_KEY=...
GEMINI_MODEL_NAME=gemini-1.5-pro
GEMINI_TEMPERATURE=0.0

LOCAL_MODEL_API_KEY=...
LOCAL_MODEL_BASE_URL=http://localhost:1234/v1
LOCAL_MODEL_NAME=llama-3
LOCAL_MODEL_TEMPERATURE=0.0
```

`src/workflows/agent.py`의 `get_model()` 팩토리가 Provider 값을 읽어 Chat Model을 생성하고 `.bind_tools(tools)` 로 도구를 탑재한다. **새 Provider 추가는 이 팩토리 함수만 수정한다.**

---

## ReAct 루프 구조

에이전트는 반드시 아래 루프로 동작해야 한다. 단계 생략 및 직접 답변 생성 숏컷 금지.

```
Observe(사용자 입력)
  → Thought(추론, agent 노드)
    → Action(tool 호출, tools 노드)
      → Observation(ToolMessage 수신)
        → Thought → Action → ... (반복)
          → Final Answer (tool_calls 없을 때 END)
```

### StateGraph 흐름

```
[agent 노드] ── should_continue ──► tool_calls 있음 ──► [tools 노드] ──┐
     ▲                                                                   │
     └───────────────────────────────────────────────────────────────────┘
                              tool_calls 없음 ──► END
```

### AgentState

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
# SystemMessage → HumanMessage → AIMessage → ToolMessage 순으로 누적
```

### 핵심 규칙

- **agent 노드**: 매 호출마다 `get_react_system_prompt(tools)` 로 시스템 프롬프트 동적 렌더링 후 messages 앞에 삽입
- **tools 노드**: `AIMessage.tool_calls` 의 도구를 실행하고 결과를 `ToolMessage` 로 상태에 추가
- **should_continue**: `last_message.tool_calls` 존재 여부로 분기
- **Streaming**: `astream_events(version="v2")` → SSE → Streamlit. 커스텀 파서 금지

---

## Import 규칙

### 절대경로 전용
```python
# ✅
from src.datasources import PostgresConnector
from src.workflows.state import AgentState

# ❌ 상대경로 금지
from .state import AgentState

# ❌ 패키지 간 이동 시 모듈 직접 지목 금지
from src.datasources.postgres import PostgresConnector
```

### 규칙 요약
- 패키지 **간** 이동 → 패키지 레벨 import (`from src.datasources import ...`)
- 패키지 **내부** 서브모듈 간 → 모듈 레벨 직접 지목 (`from src.workflows.state import ...`)
- 각 패키지 `__init__.py` 에 `__all__` 로 공개 인터페이스 명시

---

## Tool 작성 규칙

### 필수 사항
- `@tool` 데코레이터 (`from langchain_core.tools import tool`)
- 모든 파라미터에 타입 힌트 (예: `query: str`, `top_k: int = 3`)
- 구글 스타일 Docstring — **LLM이 이 내용을 읽고 호출 여부와 파라미터를 판단한다**
- 반환값은 항상 `str`. 예외는 반드시 `try-except` 로 캡처 후 에러 문자열 반환

```python
@tool
def tool_name(param: str, optional: int = 3) -> str:
    """[필수] 이 한 줄 설명으로 LLM이 도구 호출 여부를 판단한다.

    Args:
        param: 파라미터 설명
        optional: 파라미터 설명 (기본값: 3)

    Returns:
        성공: JSON 직렬화 문자열
        실패: "Error: <사유>" 형태의 에러 문자열
    """
    try:
        return result
    except Exception as e:
        return f"Error: {e}"
```

### 신규 Tool 추가 절차
1. `src/tools/` 하위에 파일 생성
2. `src/tools/__init__.py` 의 `__all__` 에 등록
3. `src/workflows/agent.py` 의 tools 리스트에 추가
4. 단위 테스트 작성 → `./run.sh test` 전체 통과 확인
5. `docs/tool_spec.md` 명세 업데이트
6. `README.md` 갱신
7. Tool이 새로운 DB 커넥터나 외부 서비스를 사용하면 `docs/project_context.md` 도 업데이트

---

## Built-in Tool 명세

### `read_uploaded_file`
서버 로컬에 저장된 업로드 파일을 읽어 원시 텍스트로 반환한다.
- `file_path: str` — 파일 절대 경로
- 반환: 파일 원시 텍스트 전체 / 미존재 또는 읽기 실패 시 에러 문자열

### `query_postgres`
PostgreSQL에 SQL을 실행하고 결과를 반환한다. SELECT / DDL / DML 모두 지원.
- `query: str` — 실행할 SQL
- 반환:
  - SELECT 성공: `[{"col": "val", ...}]` (JSON 배열 문자열)
  - DDL/DML 성공: `[{"status": "success", "message": "..."}]`
  - 실패: 에러 사유 문자열

### `query_oracle`
Oracle DB에 SELECT 쿼리를 실행한다.
- `query: str` — 실행할 SQL SELECT
- 반환: JSON 배열 문자열 / 실패 시 에러 문자열

### `search_milvus`
Milvus 벡터 DB에서 유사도 검색을 수행한다.
- `collection_name: str` — 검색할 컬렉션 이름
- `query_vector: list[float]` — 쿼리 벡터
- `top_k: int = 3` — 반환할 유사 문서 수
- 반환: `id`, `score`, 메타데이터가 담긴 JSON 배열 문자열

### `general_web_search`
인터넷 검색을 수행하고 결과 요약을 반환한다.
- `query: str` — 검색어
- 반환: 검색 결과 요약 텍스트

### `calculator`
수학 수식을 평가한다.
- `expression: str` — 수식 문자열 (예: `'2 * math.pi * 5'`)
- 반환: 연산 결과 문자열 / 수식 오류 시 에러 문자열

### `create_or_alter_table_from_file`
DDL 스키마 파일을 기반으로 DB 테이블을 생성하거나 컬럼을 추가한다.
- `file_name: str` — 스키마 파일 원본 이름 (예: `'schema.sql'`)
- `file_content: str` — 스키마 파일 원시 텍스트
- 반환: 성공 메시지 / 스키마 정합성 불일치 시 Alter 요청 피드백 문자열
- **동작**: 테이블 미존재 시 자동 생성, 존재 시 컬럼 대조 후 누락 컬럼 Alter 피드백 반환

### `upsert_data_from_json`
JSON 데이터를 DB 테이블에 벌크 Upsert한다.
- `file_name: str` — 데이터 JSON 파일 이름 (예: `'weather_data.json'`)
- `file_content: str` — JSON 파일 텍스트
- **중요**: PK 컬럼은 도구가 DB 메타데이터에서 자동 조회한다. `records` 내에 `pk_column` 키를 별도 명시하지 않는다.
- 반환: 적재 완료 건수 메시지 / 테이블 미존재 또는 제약 조건 충돌 시 에러 문자열

### `query_weather`
날씨 데이터를 기간과 조건으로 조회한다.
- `start_date: str` — 조회 시작일 (`'YYYY-MM-DD'`)
- `end_date: Optional[str] = None` — 조회 종료일 (`'YYYY-MM-DD'`, 기본값: 시작일과 동일)
- `condition: Optional[str] = None` — 날씨 조건 필터 (예: `'맑음'`, `'비'`)
- 반환: JSON 배열 문자열 / 조회 실패 시 에러 문자열

---

## CSV → DB 적재 시 에이전트 행동 순서

사용자가 CSV 업로드 및 DB 적재를 요청하면 **반드시 아래 순서**로 tool chain을 실행한다. 순서를 바꾸거나 단계를 건너뛰지 않는다.

```
Step 1. read_uploaded_file(file_path)
        → CSV 파싱, 컬럼 구조 및 데이터 타입 파악

Step 2. create_or_alter_table_from_file(file_name, ddl_content)
        → 성공: Step 3으로 진행
        → 피드백 반환(스키마 불일치): DDL 교정 후 Step 2 재호출 (Self-Correction)

Step 3. upsert_data_from_json(file_name, json_records)
        → PK는 도구가 자동 조회, records에 pk_column 명시 금지
        → 성공: 적재 완료 메시지 사용자에게 전달
        → 실패: 에러 내용 분석 후 원인 교정 및 재시도
```

---

## DB 커넥터 정책

| 클래스 | 드라이버 | 환경변수 prefix |
|---|---|---|
| `PostgresConnector` | SQLAlchemy + psycopg2-binary | `POSTGRES_` |
| `OracleConnector` | python-oracledb Thin | `ORACLE_` |
| `MilvusConnector` | pymilvus | `MILVUS_` |

**Mock Fallback**: `ENV=test` 또는 환경변수 미설정 시 세 커넥터 모두 실제 연결 없이 Mock 응답 반환. 예외 발생 금지.

**Self-Correction**: 도구가 에러 문자열을 반환하면 에이전트는 이를 Observation으로 인식하고 DDL 교정, 파라미터 수정, 대체 도구 재호출로 스스로 복구한다. 에러를 사용자에게 그대로 노출하기 전에 최소 1회 자체 복구를 시도한다.

---

## 테스트 정책

| 변경 대상 | 테스트 |
|---|---|
| `src/workflows/*`, `src/tools/*`, `src/datasources/*` | **필수 실행** |
| `src/main.py`, `src/config.py` | **필수 실행** |
| `README.md`, `docs/*`, `.gitignore`, `.env` 주석 등 | 생략 가능 |

코드 로직이 **1줄이라도** 변경되면 `./run.sh test` 실행 후 전체 통과를 확인하고 작업을 완료한다.

---

## 작업 완료 기준 (Definition of Done)

에이전트는 다음 조건이 **모두** 충족될 때만 작업이 완료된 것으로 판단한다. 하나라도 미완료면 작업을 계속한다.

### 1. 코드 품질
- [ ] 구현 코드가 Hard Rules를 단 하나도 위반하지 않는다
- [ ] 코드 변경이 있었다면 `./run.sh test` 전체 통과 확인

### 2. 문서 동기화
아래 표에서 해당하는 항목을 모두 완료한다.

| 변경 내용 | 완료해야 할 문서 업데이트 |
|---|---|
| Tool 추가 또는 인터페이스 변경 | `docs/tool_spec.md` |
| StateGraph 노드/엣지 변경 | `docs/agent_architecture.md` |
| AgentState 구조 변경 | `docs/agent_architecture.md` |
| 디렉토리 구조 변경 | `docs/project_context.md` |
| LLM Provider 또는 환경변수 변경 | `docs/project_context.md` |
| Import 규칙 변경 | `docs/project_context.md` |
| DB 커넥터 추가 또는 인터페이스 변경 | `docs/project_context.md` |
| API 엔드포인트 추가 또는 변경 | `README.md` |
| 신규 Tool 추가 | `README.md` + `docs/tool_spec.md` |
| 환경변수 추가 또는 삭제 | `README.md` + `docs/project_context.md` |
| 실행 명령어 변경 | `README.md` |

### 3. 사용자 요청 검증
- [ ] 사용자가 요청한 모든 항목이 반영되었다
- [ ] 사용자가 명시하지 않았지만 연쇄 영향을 받는 파일을 확인하고 처리했다
- [ ] 즉시 중단 조건에 해당하는 사항이 있었다면 사용자에게 확인을 받았다