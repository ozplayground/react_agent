# 프로젝트 컨텍스트 및 개발 아키텍처 (Project Context & Developer Architecture)

이 문서는 **ReAct 방법론을 적용한 에이전트를 개발하는 애플리케이션 프로젝트**의 전반적인 구조, 아키텍처 제약 조건 및 폴더 레이아웃을 정의하는 개발자용 지침서입니다.

---

## 1. 기술 스택 (Technology Stack)

- **런타임**: Python 3.11
- **웹 프레임워크**: FastAPI (에이전트 서비스 및 API 서빙용)
- **에이전트 오케스트레이션**: LangGraph (v0.3.3)
- **LLM/체인 프레임워크**: LangChain (LangGraph v0.3.3 호환 버전)
- **데이터베이스 커넥터**:
  - PostgreSQL (SQLAlchemy Engine 및 psycopg2-binary 연동)
  - Oracle (python-oracledb Thin 드라이버 연동)
  - Milvus (pymilvus Vector DB 연동)

---

## 2. 디렉토리 구조 (Directory Layout)

모든 애플리케이션의 핵심 소스 코드는 `src/` 디렉토리에 위치하며, 컴포넌트 간 임포트 효율성을 위해 각 하위 패키지에 초기화 파일(`__init__.py`)을 정의합니다.

```text
react_agent/
├── docs/                      # 개발 아키텍처 및 도구 명세 설계서
│   ├── project_context.md     # 본 문서
│   ├── agent_architecture.md  # ReAct 에이전트 오케스트레이션 아키텍처 가이드
│   ├── tool_spec.md           # 에이전트 결합용 파이썬 도구(Tool) 개발 사양서
├── logs/                      # 실행 상태 파일 로그 보관소 (logs/agent.log)
├── uploads/                   # 사용자가 API를 통해 업로드한 파일 보관소
├── src/                       # 메인 소스 디렉토리
│   ├── __init__.py            # 패키지 초기화 파일
│   ├── main.py                # FastAPI 엔트리 포인트 (비동기 SSE 스트리밍 제공)
│   ├── config.py              # Pydantic Settings 기반 환경 설정 로더
│   ├── datasources/           # RDB 및 Vector DB 커넥터 패키지
│   ├── tools/                 # 에이전트 바인딩용 파이썬 도구(Tool) 패키지
│   ├── workflows/             # LangGraph 에이전트 상태 그래프 정의 패키지
│   └── utils/                 # 로거 및 공통 유틸리티 패키지
├── tests/                     # Pytest 기반 단위 테스트 패키지
├── .env                       # 로컬 자격 증명 및 LLM 제공자 제어 변수 파일
├── requirements.txt           # 패키지 의존성 파일
└── run.sh                     # Uvicorn, Streamlit, Pytest 간편 가동 스크립트
```

---

## 3. 아키텍처 제약 조건 (Architectural Constraints)

개발자는 이 애플리케이션을 확장 및 구현할 때 다음 제약 조건을 엄격히 준수해야 합니다.

1. **ReAct 방법론 준수**: 에이전트는 항상 Reasoning-Acting 루프를 통해 작동해야 합니다. 사용자 입력 관찰 -> 생각(Thought) -> 도구 호출(Action) -> 결과 관찰(Observation) -> 생각 -> 최종 답변의 단계를 거쳐야 합니다.
2. **LangGraph 상태 관리**: 에이전트의 대화 상태는 LangGraph `State`를 통해서만 명시적으로 전달되어야 합니다. 글로벌 변수나 인메모리 싱글톤 객체에 대화 상태를 저장하지 마십시오.
3. **별도 파서 미작성**: LangChain/LangGraph의 기본 메시지 표현식 및 도구 호출 기능을 그대로 사용합니다. LLM 응답을 해석하기 위한 커스텀 XML/JSON 파서를 직접 작성하지 마십시오.
4. **환경 변수 격리**: 모든 자격 증명 및 설정은 `pydantic-settings` 모듈을 사용해 `.env` 파일로부터 동적으로 로드해야 합니다.
5. **테스트 가능성**: 모든 컴포넌트는 Mock 객체를 사용하여 테스트 가능해야 합니다. 데이터베이스 래퍼는 테스트 환경이거나 자격 증명이 없는 경우 실제 연결을 맺지 않고 모의 응답을 반환해야 합니다.

---

## 4. LLM 제공자(Provider) 선택 및 환경 변수 설정 규칙

이 애플리케이션은 OpenAI, Google Gemini 및 로컬 OpenAI 호환 모델(LM Studio, Ollama 등)을 동적으로 변경하며 서빙하는 삼중 제공자(Triple LLM Provider) 설정을 지원합니다.

1. **`LLM_PROVIDER` 제어**: 환경 변수 `LLM_PROVIDER`를 통해 사용할 백엔드 모델을 제어합니다. 허용되는 값은 `openai`, `gemini`, `local` 입니다.
2. **제공자별 격리 설정**: 각 LLM 서비스 사양에 필요한 변수명(API 키, 모델명, 온도)을 명확하게 분리하여 `.env`에 정의합니다.
   - 예: `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`, `OPENAI_TEMPERATURE`
   - 예: `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `GEMINI_TEMPERATURE`
   - 예: `LOCAL_MODEL_API_KEY`, `LOCAL_MODEL_BASE_URL`, `LOCAL_MODEL_NAME`, `LOCAL_MODEL_TEMPERATURE`
3. **다이내믹 팩토리 패턴**: `src/workflows/agent.py` 내의 `get_model` 팩토리 메서드는 `LLM_PROVIDER` 값을 읽어 해당하는 Chat Model 객체를 동적으로 생성하고, 바인딩된 파이썬 도구 목록을 탑재하여 반환하도록 구현합니다.

---

## 5. 패키지 초기화 및 모듈 임포트 규칙 (Import Rules)

1. **`__init__.py` 활용**: 각 하위 패키지 디렉토리는 자신들의 초기화 파일(`__init__.py`)을 갖고, 외부로 노출할 대표 클래스 및 함수들을 `__all__` 리스트에 정의해야 합니다.
2. **패키지 수준 임포트**: 패키지 경계를 넘나드는 임포트를 할 경우, 개별 모듈 파이썬 파일로부터 직접 임포트하지 말고 패키지 디렉토리 수준에서 임포트해야 합니다.
   - *올바른 예*: `from src.datasources import PostgresConnector`
   - *올바르지 않은 예*: `from src.datasources.postgres import PostgresConnector`
3. **절대경로 규칙 및 순환 참조 예방**:
   - 프로젝트 내 모든 파이썬 파일의 임포트는 반드시 **절대경로(Absolute Import)**를 사용해야 합니다. 상대 경로의 사용은 금지됩니다.
   - 순환 참조(Circular Dependency)를 방지하기 위해 패키지 내부 서브모듈 간에 임포트할 때는 개별 모듈 파이썬 파일 수준(예: `from src.workflows.state import AgentState`)으로 직접 지목하여 임포트하여 모듈 적재 오버헤드와 임포트 루프를 차단합니다.
