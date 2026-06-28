from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from src.config import settings
from src.workflows.state import AgentState
from src.workflows.prompts import get_react_system_prompt
from src.tools import read_uploaded_file, query_postgres, query_oracle, search_milvus, calculator, general_web_search, create_or_alter_table_from_file, upsert_data_from_json, query_weather
from src.utils import get_logger

logger = get_logger(__name__)

# ReAct 에이전트가 활용할 도구 목록 등록
tools = [
    read_uploaded_file,
    query_postgres,
    query_oracle,
    search_milvus,
    calculator,
    general_web_search,
    create_or_alter_table_from_file,
    upsert_data_from_json,
    query_weather
]

# AI 메시지의 tool_calls 요청을 자동으로 수행해주는 표준 LangGraph ToolNode 정의
tool_node = ToolNode(tools)

def get_model():
    """
    설정된 LLM 제공자(LLM_PROVIDER)에 해당하는 모델을 초기화하여 반환합니다.
    """
    provider = settings.llm_provider.lower()
    
    if provider == "gemini":
        api_key = settings.gemini_api_key
        if api_key == "mock-key":
            logger.warning("GEMINI_API_KEY가 설정되지 않았습니다. 테스트 환경이 아니면 모델 호출이 실패할 수 있습니다.")
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model_name,
            temperature=settings.gemini_temperature,
            google_api_key=api_key,
            streaming=True
        )
    elif provider == "local":
        logger.info(f"로컬 OpenAI 호환 모델로 라우팅합니다. Base URL: {settings.local_model_base_url}, 모델명: {settings.local_model_name}")
        llm = ChatOpenAI(
            model=settings.local_model_name,
            temperature=settings.local_model_temperature,
            openai_api_key=settings.local_model_api_key,
            base_url=settings.local_model_base_url,
            streaming=True
        )
    else:  # 기본값은 openai
        api_key = settings.openai_api_key
        if api_key == "mock-key":
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다. 테스트 환경이 아니면 모델 호출이 실패할 수 있습니다.")
        llm = ChatOpenAI(
            model=settings.openai_model_name,
            temperature=settings.openai_temperature,
            openai_api_key=api_key,
            streaming=True
        )
    return llm.bind_tools(tools)

def call_model(state: AgentState):
    """
    대화 기록과 시스템 프롬프트를 함께 엮어서 LLM 모델을 실행하는 노드 함수입니다.
    """
    logger.info("call_model (에이전트) 노드를 실행합니다.")
    messages = state["messages"]
    
    # 대화 기록 시작 지점에 시스템 프롬프트가 존재하는지 확인
    has_system = False
    if messages:
        first_msg = messages[0]
        if isinstance(first_msg, SystemMessage) or (hasattr(first_msg, "type") and first_msg.type == "system"):
            has_system = True
            
    if not has_system:
        # get_react_system_prompt를 활용하여 동적으로 도구 명세 및 코멘트가 포함된 시스템 프롬프트를 컴파일합니다.
        dynamic_system_prompt = get_react_system_prompt(tools)
        formatted_messages = [SystemMessage(content=dynamic_system_prompt)] + list(messages)
    else:
        formatted_messages = list(messages)
        
    # --- 에이전트 동작 추적을 위한 입력 프롬프트 상세 로깅 ---
    logger.info("=" * 80)
    logger.info(">>> [LLM 요청 시작] 입력 메시지 및 프롬프트 상세 이력:")
    for idx, msg in enumerate(formatted_messages):
        msg_type = msg.__class__.__name__
        logger.info(f"    [{idx}] {msg_type}: {repr(msg.content)}")
    logger.info("=" * 80)
        
    model = get_model()
    response = model.invoke(formatted_messages)
    
    # --- 에이전트 동작 추적을 위한 출력 응답 상세 로깅 ---
    logger.info("=" * 80)
    logger.info(f"<<< [LLM 응답 수신] 형식: {response.__class__.__name__}")
    logger.info(f"    내용(Content): {repr(response.content)}")
    if hasattr(response, "tool_calls") and response.tool_calls:
        logger.info(f"    도구 호출 요청(Tool Calls): {response.tool_calls}")
    logger.info("=" * 80)
    
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    """
    조건부 라우팅 로직. 실행할 도구 호출이 남아있다면 'tools' 노드로 이동하고,
    그렇지 않다면 종료(END) 노드로 이동합니다.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"'tools' 노드로 라우팅합니다 (요청된 도구: {[tc['name'] for tc in last_message.tool_calls]})")
        return "tools"
        
    logger.info("요청된 도구 호출이 없습니다. END 노드로 라우팅합니다.")
    return "end"

# StateGraph 인스턴스 생성
workflow = StateGraph(AgentState)

# 에이전트와 도구 실행 노드 추가
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# 시작 노드 설정
workflow.add_edge(START, "agent")

# 조건부 엣지 규칙 등록
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

# 도구 실행 완료 후 다시 에이전트 노드로 루프 백
workflow.add_edge("tools", "agent")

# 실행 가능한 그래프 애플리케이션으로 컴파일
agent_graph = workflow.compile()
