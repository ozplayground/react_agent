# 에이전트 설계 및 아키텍처 가이드 (Agent Design & Architecture Guide)

이 문서는 이 애플리케이션의 핵심인 **ReAct 방법론 기반 AI 에이전트의 소프트웨어 구조 및 상태 제어 그래프(State Graph) 디자인**을 정의하는 개발자용 설계서입니다.

---

## 1. 에이전트 워크플로우 아키텍처 개요

이 애플리케이션은 사용자의 질문이나 파일 처리 명령을 수신하여 다음과 같은 파이프라인 구조를 거쳐 비동기 토큰 스트리밍으로 최종 출력합니다:

```text
[Streamlit UI 클라이언트]
       │ (1) HTTP POST /chat/stream (Payload: ChatRequest)
       ▼
[FastAPI 백엔드 라우터] (main.py)
       │ (2) LLM_PROVIDER 검사 및 동적 모델 팩토리 호출 (get_model)
       ▼
[LangGraph ReAct 그래프 엔진] (agent.py)
       │ (3) astream_events(version="v2") 기동
       ▼
[사용자 응답 스트리밍 방출] ──► (SSE Chunk) ──► [Streamlit UI 렌더러]
```

---

## 2. LangGraph 상태 그래프 디자인 (State Graph Design)

에이전트의 두뇌 역할을 담당하는 LangGraph는 `StateGraph`를 통해 **노드(Node)와 엣지(Edge)의 오케스트레이션**을 수행합니다.

### (1) 그래프 상태 (`AgentState`)
- **타입**: `TypedDict`
- **구조**: `messages: Annotated[Sequence[BaseMessage], add_messages]`
- **역할**: 대화 시작부터 끝까지 오가는 모든 메시지(SystemMessage, HumanMessage, AIMessage, ToolMessage)의 상태를 누적 추적합니다.

### (2) 노드 및 엣지 라우팅 설계
- **`agent` 노드**: 
  - 현재 상태의 메시지 목록을 LLM에 전달하여 추론을 실행합니다.
  - 이 노드 기동 시점에 `get_react_system_prompt(tools)`를 호출하여 동적으로 렌더링된 최신 시스템 프롬프트가 대화 시작 부분에 동적으로 삽입됩니다.
- **`tools` 노드**:
  - LLM이 반환한 `AIMessage` 내부에 `tool_calls`가 있을 때 활성화되며, 해당하는 파이썬 도구를 매핑 매개변수와 함께 호출하고 실행 결과를 `ToolMessage`로 생성해 상태에 추가합니다.
- **엣지 (`should_continue`)**:
  - `agent` 노드의 출력 메시지를 검사하여 분기 제어를 처리합니다.
  - `tool_calls`가 감지되면 -> `tools` 노드로 연결 (Action 단계로 진행).
  - `tool_calls`가 없으면 -> `END`로 연결하여 대화를 최종 종료하고 답변 반환.

---

## 3. 대용량 CSV 파일 업로드 및 데이터베이스 적재 워크플로우

사용자가 데이터 파일(CSV) 업로드를 통해 테이블 생성 및 Upsert 적재를 요청할 경우, 에이전트는 애플리케이션 내부의 도구 체인을 다음 단계 순서로 조합해 실행하도록 유도됩니다.

```text
[1단계: 원천 파일 분석] 
  read_uploaded_file(file_path) 호출 ──► CSV 문자열 파싱 
       │
       ▼
[2단계: 테이블 설계 및 검증]
  컬럼 타입 결정 및 DDL 스키마 JSON 설계 
  ──► create_or_alter_table_from_file(file_name, file_content) 호출
       │
       ├─► (테이블 미존재 시) 신규 생성 DDL 자동 실행
       └─► (테이블 존재 시) 컬럼 대조 후 누락이 발견되면 Alter 피드백 반환
       │
       ▼
[3단계: 벌크 데이터 적재]
  CSV 데이터 레코드를 JSON 객체 리스트로 전격 가공
  ──► upsert_data_from_json(file_name, file_content) 호출
  ──► DB 메타데이터에서 PK(기본키) 자동 검색 후 ON CONFLICT 벌크 Upsert 처리
```

---

## 4. 에러 복구력 및 점진적 기능 저하 (Resilience & Fallback)

1. **도구 오류 캡처 정책**: 
   - 데이터베이스 접속 끊김, 잘못된 쿼리 또는 타입 불일치 등의 예외가 발생하더라도 파이썬 프로그램이 크래시되지 않도록 각 도구 내부에서 `try-except`로 오류를 문자열로 전환해 반환하도록 설계합니다.
   - 반환된 에러 메시지를 수신한 에이전트(LLM)는 이를 `Observation`으로 인식하여 DDL을 교정하거나, 파라미터를 수정하거나, 대체 도구를 재호출하여 스스로 문제를 복구(Self-Correction)합니다.
2. **Mocking 데이터베이스 폴백**:
   - 로컬 개발 환경이나 DB 자격 증명이 누락된 테스트 환경에서는 `PostgresConnector`, `OracleConnector`, `MilvusConnector`가 예외를 유발하지 않고, 모의 응답(Mock Response)을 제공해 전체 파이프라인의 테스트 가능성을 100% 보장합니다.
