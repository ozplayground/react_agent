# ReAct 에이전트 프레임워크 (FastAPI, LangChain, LangGraph 0.3.3)

이 프로젝트는 **Python 3.11**, **FastAPI**, **LangChain**, 그리고 **LangGraph v0.3.3**을 기반으로 설계된 재사용 가능한 **ReAct (Reasoning and Acting) 방법론** 기반의 AI 에이전트 프레임워크입니다.

기본적으로 데이터베이스(PostgreSQL, Oracle) 및 벡터 데이터베이스(Milvus) 연결 유틸리티와 연동되어 작동하며, OpenAI 및 Google Gemini 두 가지 LLM 제공자를 환경 변수 설정을 통해 동적으로 바꾸어가며 사용할 수 있습니다.

---

## 🌟 주요 기능 및 아키텍처 특징

1. **ReAct 추론 루프**: LangGraph 0.3.3을 활용해 사용자 입력 -> 생각(Thought) -> 도구 호출(Action) -> 결과 관찰(Observation) -> 생각 -> 최종 응답으로 이어지는 상태 그래프 워크플로우를 완벽하게 오케스트레이션합니다.
2. **삼중 LLM 제공자(Triple LLM Provider) 지원**: `.env` 설정에 따라 OpenAI(`ChatOpenAI`), Google Gemini(`ChatGoogleGenerativeAI`), 그리고 로컬 OpenAI 호환 모델(LM Studio, Ollama, vLLM 등)을 유연하게 전환하여 실행합니다.
3. **Streamlit 웹 UI 클라이언트 탑재**: 사용자 친화적인 Streamlit 기반 프론트엔드를 제공하여 파일 드래그 앤 드롭 업로드 및 실시간 추론 스트리밍 대화를 마우스 클릭 몇 번으로 제어 가능합니다.
4. **실시간 스트리밍 엔드포인트**: FastAPI의 SSE(Server-Sent Events)를 활용해 LangGraph 노드 업데이트 과정을 실시간으로 스트리밍하는 `/chat/stream` 엔드포인트를 제공합니다.
5. **사용자 파일 업로드 서비스 (`/upload`)**: HTTP Multipart Form을 통해 기상 데이터 등 원천 데이터 파일을 서버(`uploads/` 폴더)에 업로드하는 API를 제공합니다.
5. **에이전트 업로드 파일 연동 및 컨텍스트 주입**:
   - 사용자가 파일을 업로드한 뒤 `/chat` 이나 `/chat/stream` API를 호출할 때 파일명과 서버 저장 절대 경로(`file_name`, `file_path`)를 페이로드에 동봉할 수 있습니다.
   - FastAPI는 이 파일 정보를 탐지하여 에이전트의 대화 시작 스레드에 강제 시스템 지침 메타데이터로 변환해 주입하며, 에이전트(LLM)가 해당 업로드 파일을 곧바로 파싱 분석할 수 있도록 결합합니다.
6. **지능형 스키마 빌드 및 데이터 생성(적재) 도구 분리**:
   - **`read_uploaded_file`**: 사용자가 업로드하여 서버에 존재하나 에이전트 대화 스레드 상에 텍스트 본문이 없는 파일의 원시 텍스트를 절대 경로(`file_path`)를 기반으로 읽어와 에이전트에게 공급합니다.
   - **`create_or_alter_table_from_file`**: SQL DDL 파일(.sql)이나 테이블/컬럼 코멘트 및 인덱스가 선언된 스키마 JSON 파일(.json)의 이름과 내용을 직접 업로드(DML/DDL 전송)받아 테이블을 생성하고 검증합니다. 기존 DB 구조 대비 신규 컬럼 누락 시 에이전트에게 변경 요청 피드백을 전달하는 Alter 피드백 루프를 작동시킵니다.
   - **`upsert_data_from_json`**: 가공된 데이터 JSON 파일의 명칭과 내용을 업로드받아 벌크 Upsert 적재를 대행합니다. 기본키 컬럼 정보는 DB 스키마 메타데이터로부터 **도구 내에서 자동으로 추출 식별**하므로 JSON 데이터에 별도의 PK 명시가 불필요합니다.
7. **동작 추적 파일 로깅**: 모든 프롬프트 이력, LLM 원시 응답값, 도구 실행 로그가 `%project_root%/logs/agent.log` 경로에 한글 인코딩을 고려하여 영구 기록됩니다.
8. **자동 실행 쉘 스크립트 (`run.sh`)**: 가상환경 구축부터 라이브러리 설치, 서버 실행 및 테스트 일괄 기동을 지원하는 원클릭 스크립트를 내장했습니다.

---

## 📂 디렉토리 구조

```text
react_agent/
├── docs/                      # 하네스 엔지니어링 설계 가이드라인 문서
│   ├── project_context.md     # 아키텍처 규칙, import 규칙 및 폴더 레이아웃
│   ├── agent_architecture.md  # ReAct 에이전트 오케스트레이션 아키텍처 가이드
│   ├── tool_spec.md           # 파이썬 데코레이터 기반 에이전트 도구(Tool) 개발 사양서
├── logs/                      # 파일 로거 출력 폴더
│   └── agent.log              # LLM 요청 프롬프트와 응답 등이 기록되는 파일
├── uploads/                   # 사용자가 API를 통해 업로드한 파일 보관소
├── src/                       # 메인 소스코드 패키지
│   ├── __init__.py            # 패키지 초기화 파일
│   ├── main.py                # FastAPI 웹 애플리케이션 서비스 엔트리 포인트
│   ├── config.py              # Pydantic Settings 환경 설정 검증 및 로더
│   ├── datasources/           # DB 및 Vector DB 드라이버 래퍼
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   ├── oracle.py
│   │   └── milvus.py
│   ├── tools/                 # 에이전트 도구(Tool) 구현체
│   │   ├── __init__.py
│   │   ├── db_tools.py        # DDL 스키마 관리, DML 데이터 적재 및 날씨 조회 도구
│   │   └── general_tools.py
│   ├── workflows/             # LangGraph 상태 및 노드 오케스트레이션
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── state.py
│   │   └── prompts.py
│   └── utils/                 # 공통 헬퍼 기능
│       ├── __init__.py
│       └── logger.py
├── tests/                     # pytest 단위 테스트 패키지
│   ├── __init__.py
│   ├── test_datasources.py
│   ├── test_tools.py
│   └── test_workflows.py
├── .env                       # 환경 변수 설정 파일
├── requirements.txt           # 패키지 종속성 정의 목록
├── run.sh                     # 실행 자동화 쉘 스크립트
└── README.md                  # 프로젝트 안내서 (본 파일)
```

---

## 🚀 시작하기 및 실행 방법

### 1. 환경 설정 (.env)
프로젝트 루트 디렉토리에 `.env` 파일을 작성하고 사용할 제공자를 지정합니다.
```env
# 사용할 LLM 제공자 지정: 'openai', 'gemini' 또는 'local'
LLM_PROVIDER=openai

# OpenAI API 및 모델 설정
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.0

# Gemini API 및 모델 설정
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL_NAME=gemini-1.5-flash
GEMINI_TEMPERATURE=0.0

# 로컬 OpenAI 호환 모델 설정 (LM Studio, Ollama, vLLM 등)
LOCAL_MODEL_API_KEY=lm-studio
LOCAL_MODEL_BASE_URL=http://localhost:1234/v1
LOCAL_MODEL_NAME=meta-llama-3-8b-instruct
LOCAL_MODEL_TEMPERATURE=0.0
```

### 2. 실행 쉘 스크립트를 통한 간편 가동
```bash
# [개발 서버 구동] 포트 8000번에서 uvicorn 백엔드 서버 실행 (자동 패키지 설치 포함)
./run.sh dev   # 또는 간단히 ./run.sh

# [프론트엔드 구동] 포트 8501번에서 Streamlit 웹 애플리케이션 실행
./run.sh ui    # 또는 ./run.sh app

# [단위 테스트 실행] pytest를 활용해 전체 테스트 일괄 기동
./run.sh test  # 또는 간단히 ./run.sh t
```

---

## 📖 공통 API 요청 규격 (ChatRequest Schema)

이 프로젝트의 대화형 API 엔드포인트인 `/chat` (동기식)과 `/chat/stream` (실시간 SSE 스트리밍)은 **완전히 동일한 Pydantic `ChatRequest` 스키마 페이로드**를 입력으로 소비합니다. 파일 업로드 연동 여부 및 이전 대화 내역에 따라 아래 필드들을 자유롭게 조합하여 동일한 형태로 호출이 가능합니다.

| 필드명 | 데이터 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `message` | `string` | **필수** | 에이전트에게 내릴 현재 명령 혹은 질문 내용 (예: `"날씨 데이터를 적재해줘"`) |
| `file_name` | `string` | 선택 | 업로드한 파일의 원본 이름 (예: `"weather_data.csv"`) |
| `file_path` | `string` | 선택 | 백엔드 서버에 복사 저장된 업로드 파일의 절대 경로 |
| `history` | `array[object]` | 선택 | 이전 대화 내역 목록. 대화 컨텍스트 유지용이며 `{"role": "user"\|"assistant", "content": "..."}` 구조의 객체 배열로 구성합니다. |

---

## 💬 API 연동 시나리오 가이드 (CURL 실증)

아래 순서에 따라 사용자가 실제로 데이터 CSV 파일을 업로드하고, 에이전트가 이를 분석해 테이블을 생성 및 적재하는 시나리오를 연동 테스트할 수 있습니다.

### 1단계: CSV 데이터 파일 업로드 (`/upload`)
데이터 대상인 CSV 파일을 FastAPI 서버에 멀티파트로 전송(Upload)합니다.
```bash
curl -X POST "http://localhost:8000/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/weather_data.csv"
```
*성공 시 반환되는 `file_name` 과 `file_path` 메타데이터를 확인하십시오.*

### 2단계: 파일 정보를 포함한 스트리밍 대화 요청 (`/chat/stream`)
업로드 완료 후, 파일명과 저장 경로를 대화 요청 페이로드에 실어 전송합니다. 에이전트(LLM)는 이 메타데이터를 인지해 분석 및 스키마 생성을 자율적으로 처리합니다.
```bash
curl -N -X POST "http://localhost:8000/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "방금 내가 업로드한 기상 정보 CSV 데이터를 분석해서 스키마를 생성하고 테이블을 구축한 뒤 데이터를 모두 upsert 적재해줘.",
       "file_name": "weather_data.csv",
       "file_path": "/Users/wonyoung/workspace/react_agent/uploads/weather_data.csv",
       "history": []
     }'
```
*에이전트가 스키마 JSON 파일을 업로드하여 테이블을 생성하고(`create_or_alter_table_from_file`), 데이터 레코드를 가공해 적재(`upsert_data_from_json`)하는 ReAct 루프가 화면에 스트리밍 출력됩니다.*

### 3단계: 적재된 날씨 조회 요청 (`/chat`)
적재 완료 후, DB 기상 상태 조회를 에이전트에게 묻습니다.
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "2026년 7월에 폭우가 내려 비 온 날 3일간의 상세 기상 정보를 DB에서 조회해서 알려줘.",
       "history": []
     }'
```

---

## 🧪 테스트 실행 방법

이 프로젝트는 Mock 데이터를 활용하여 외부 DB 서버 및 LLM API 키 없이도 로컬 환경에서 100% 완전한 단위 테스트 수행을 보장합니다.

```bash
# run.sh 활용
./run.sh test

# 또는 직접 가동 시
PYTHONPATH=. pytest tests/
```
- **테스트 커버리지 목록**: DB 커넥터 및 Mock 폴백 검증(`test_datasources.py`), DDL/DML 도구 분리 및 PK 자동 감지/바인딩 검증(`test_tools.py`), 동기/스트리밍/제미나이 다이내믹 라우팅 워크플로우 검증(`test_workflows.py`).
