from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    ReAct 에이전트의 컨텍스트를 나타내는 상태 정의입니다.
    
    'messages' 키는 내장된 add_messages 리듀서를 사용하여
    대화에 오고 간 모든 메시지(대화 기록)를 누적하여 관리합니다.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
