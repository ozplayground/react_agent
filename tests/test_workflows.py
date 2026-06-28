import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.workflows import agent_graph

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI.invoke")
async def test_react_agent_workflow_full_loop(mock_invoke):
    """
    LangGraph의 전체 ReAct 추론 주기를 시뮬레이션 및 검증합니다:
    - 1단계: 사용자가 수학 문제를 질문합니다. 에이전트는 'calculator' 도구를 호출하기로 판단합니다.
    - 2단계: 모의 도구 실행 노드가 실행되어 계산 결과("579")를 도출합니다.
    - 3단계: 에이전트는 도구 실행 결과를 보고 최종 정답 메시지를 구성하여 반환합니다.
    """
    # 1회차 모델 호출 결과 모킹: 도구 호출 요청을 담은 AI 메시지
    mock_ai_msg_with_tool = AIMessage(
        content="123 + 456 계산을 수행하기 위해 계산기 도구를 호출하겠습니다.",
        tool_calls=[{
            "name": "calculator",
            "args": {"expression": "123 + 456"},
            "id": "call_mock_id_001",
            "type": "tool_call"
        }]
    )
    
    # 2회차 모델 호출 결과 모킹: 최종 정답을 담은 AI 메시지
    mock_ai_msg_final = AIMessage(
        content="123 + 456의 계산 결과는 579입니다."
    )
    
    # 순차적 호출 결과 등록
    mock_invoke.side_effect = [mock_ai_msg_with_tool, mock_ai_msg_final]
    
    # 초기 질문 주입
    initial_state = {
        "messages": [HumanMessage(content="123 + 456을 계산해줘.")]
    }
    
    # 비동기로 컴파일된 LangGraph 실행
    result = await agent_graph.ainvoke(initial_state, config={"recursion_limit": 5})
    
    # 상태 메시지 누적 이력 검증
    messages = result["messages"]
    # 예상 누적 메시지:
    # 1. HumanMessage (사용자 질문)
    # 2. AIMessage (추론 및 도구 호출 요청)
    # 3. ToolMessage (계산기 도구 실행 결과, 즉 "579")
    # 4. AIMessage (최종 답변)
    assert len(messages) == 4
    
    # 객체 타입 및 내용 검증
    assert isinstance(messages[0], HumanMessage)
    
    assert isinstance(messages[1], AIMessage)
    assert len(messages[1].tool_calls) == 1
    assert messages[1].tool_calls[0]["name"] == "calculator"
    assert messages[1].tool_calls[0]["args"]["expression"] == "123 + 456"
    
    assert isinstance(messages[2], ToolMessage)
    assert messages[2].content == "579"
    
    assert isinstance(messages[3], AIMessage)
    assert "579" in messages[3].content
    
    # LLM invoke가 총 2번 정상적으로 가동되었는지 확인
    assert mock_invoke.call_count == 2

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI.invoke")
async def test_react_agent_workflow_streaming(mock_invoke):
    """
    astream을 활용해 ReAct 그래프의 노드 업데이트 스트리밍 출력을 검증합니다.
    """
    mock_ai_msg_final = AIMessage(
        content="날씨는 오늘 아주 맑고 화창합니다."
    )
    mock_invoke.return_value = mock_ai_msg_final
    
    initial_state = {
        "messages": [HumanMessage(content="오늘 날씨 어때?")]
    }
    
    chunks = []
    async for chunk in agent_graph.astream(initial_state, config={"recursion_limit": 5}, stream_mode="updates"):
        chunks.append(chunk)
        
    # chunks 리스트가 하나 이상의 노드 업데이트를 가지고 있는지 확인
    assert len(chunks) > 0
    assert "agent" in chunks[0]
    assert "messages" in chunks[0]["agent"]
    assert chunks[0]["agent"]["messages"][0].content == "날씨는 오늘 아주 맑고 화창합니다."

@pytest.mark.asyncio
@patch("langchain_google_genai.ChatGoogleGenerativeAI.invoke")
async def test_react_agent_workflow_gemini_provider(mock_invoke):
    """
    LLM_PROVIDER가 'gemini'로 설정되었을 때 ChatGoogleGenerativeAI를 정상적으로 거치며
    ReAct 워크플로우가 실행되는지 검증합니다.
    """
    from src.config import settings
    # llm_provider 설정을 임시로 gemini로 변경
    original_provider = settings.llm_provider
    settings.llm_provider = "gemini"
    
    try:
        mock_ai_msg = AIMessage(
            content="Gemini 모델을 통한 최종 응답입니다."
        )
        mock_invoke.return_value = mock_ai_msg
        
        initial_state = {
            "messages": [HumanMessage(content="안녕하세요")]
        }
        
        result = await agent_graph.ainvoke(initial_state, config={"recursion_limit": 5})
        messages = result["messages"]
        
        assert len(messages) == 2  # HumanMessage + AIMessage
        assert messages[1].content == "Gemini 모델을 통한 최종 응답입니다."
        mock_invoke.assert_called_once()
        
    finally:
        # 설정 원상복구
        settings.llm_provider = original_provider

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI.invoke")
async def test_react_agent_workflow_local_provider(mock_invoke):
    """
    LLM_PROVIDER가 'local'로 설정되었을 때 base_url이 바인딩된 ChatOpenAI를 정상적으로 거치며
    ReAct 워크플로우가 실행되는지 검증합니다.
    """
    from src.config import settings
    original_provider = settings.llm_provider
    settings.llm_provider = "local"
    
    try:
        mock_ai_msg = AIMessage(
            content="Local 모델을 통한 최종 응답입니다."
        )
        mock_invoke.return_value = mock_ai_msg
        
        initial_state = {
            "messages": [HumanMessage(content="로컬 모델 테스트")]
        }
        
        result = await agent_graph.ainvoke(initial_state, config={"recursion_limit": 5})
        messages = result["messages"]
        
        assert len(messages) == 2  # HumanMessage + AIMessage
        assert messages[1].content == "Local 모델을 통한 최종 응답입니다."
        mock_invoke.assert_called_once()
        
    finally:
        settings.llm_provider = original_provider



