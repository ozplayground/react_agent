import json
import os
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from src.workflows import agent_graph
from src.utils import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="ReAct Agent Framework API",
    description="LangChain 및 LangGraph 0.3.3 ReAct 에이전트 워크플로우를 서빙하는 FastAPI 애플리케이션입니다.",
    version="1.0.0"
)

class ChatMessage(BaseModel):
    role: str = Field(..., description="메시지 전송자의 역할: 'user'(사용자) 또는 'assistant'(에이전트)")
    content: str = Field(..., description="메시지 텍스트 내용")

class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자가 입력한 현재 질문 내용")
    file_name: Optional[str] = Field(None, description="업로드된 파일 이름 (예: 'weather_data.csv')")
    file_path: Optional[str] = Field(None, description="서버에 저장된 업로드 파일 절대 경로")
    history: Optional[List[ChatMessage]] = Field(default=[], description="이전 대화 내역 기록")

class ChatResponse(BaseModel):
    response: str = Field(..., description="ReAct 에이전트가 도출한 최종 답변")
    steps: List[str] = Field(..., description="ReAct 추론 루프가 거쳐온 단계별 실행 로그")

@app.on_event("startup")
def startup_event():
    logger.info("FastAPI 애플리케이션 시작 - ReAct 에이전트 프레임워크가 로드되었습니다.")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("FastAPI 애플리케이션 종료 - ReAct 에이전트 프레임워크가 중지되었습니다.")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "description": "ReAct 에이전트 프레임워크 API가 정상 동작 중입니다.",
        "endpoints": {
            "upload": "/upload (POST) - 파일 업로드",
            "chat": "/chat (POST) - 대화 및 적재 실행",
            "chat_stream": "/chat/stream (POST) - 스트리밍 대화 및 적재",
            "docs": "/docs (Swagger UI 문서)"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    일반 동기 방식의 에이전트 호출 엔드포인트입니다.
    업로드된 파일 이름(file_name)과 경로(file_path)가 존재할 경우 에이전트의 대화 컨텍스트에 파일 메타데이터를 주입합니다.
    """
    logger.info(f"일반 채팅 요청 수신: '{payload.message}', 파일명={payload.file_name}")
    
    # 1. 이전 히스토리를 LangChain Message 객체 형태로 변환
    input_messages: List[BaseMessage] = []
    for item in payload.history:
        if item.role == "user":
            input_messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            input_messages.append(AIMessage(content=item.content))
            
    # 2. 업로드 파일 정보가 있을 경우 메시지에 파일 컨텍스트 강제 주입
    user_msg_content = payload.message
    if payload.file_name and payload.file_path:
        user_msg_content = (
            f"[시스템 안내: 사용자가 파일을 성공적으로 업로드하였습니다.\n"
            f"- 업로드 파일명: {payload.file_name}\n"
            f"- 서버 절대 경로: {payload.file_path}]\n\n"
            f"{payload.message}"
        )
            
    input_messages.append(HumanMessage(content=user_msg_content))
    
    try:
        config = {"recursion_limit": 25}
        result = await agent_graph.ainvoke(
            {"messages": input_messages},
            config=config
        )
        
        output_messages = result.get("messages", [])
        if not output_messages:
            raise HTTPException(status_code=500, detail="그래프가 정상 실행되었으나 반환된 메시지가 비어 있습니다.")
            
        final_ai_msg = output_messages[-1]
        final_answer = getattr(final_ai_msg, "content", "응답 내용이 존재하지 않습니다.")
        
        steps = []
        for msg in output_messages:
            msg_type = msg.__class__.__name__
            msg_content = getattr(msg, "content", "")
            tool_info = ""
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_info = f" [도구 호출 요청: {msg.tool_calls}]"
            steps.append(f"{msg_type}: {msg_content}{tool_info}")
            
        return ChatResponse(response=str(final_answer), steps=steps)
        
    except Exception as e:
        logger.error(f"에이전트 그래프 처리 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"에이전트 워크플로우 처리 중 오류 발생: {str(e)}"
        )

@app.post("/chat/stream")
async def chat_stream_endpoint(payload: ChatRequest):
    """
    LangGraph의 비동기 이벤트 스트리밍(astream_events)을 사용한 SSE 방식의 실시간 토큰 및 도구 로그 스트리밍 엔드포인트입니다.
    업로드된 파일 이름(file_name)과 경로(file_path)가 존재할 경우 에이전트의 대화 컨텍스트에 파일 메타데이터를 주입합니다.
    """
    logger.info(f"스트리밍 채팅 요청 수신: '{payload.message}', 파일명={payload.file_name}")
    
    # 1. 이전 히스토리 가공
    input_messages: List[BaseMessage] = []
    for item in payload.history:
        if item.role == "user":
            input_messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            input_messages.append(AIMessage(content=item.content))
            
    # 2. 업로드 파일 정보가 있을 경우 메시지에 파일 컨텍스트 강제 주입
    user_msg_content = payload.message
    if payload.file_name and payload.file_path:
        user_msg_content = (
            f"[시스템 안내: 사용자가 파일을 성공적으로 업로드하였습니다.\n"
            f"- 업로드 파일명: {payload.file_name}\n"
            f"- 서버 절대 경로: {payload.file_path}]\n\n"
            f"{payload.message}"
        )
            
    input_messages.append(HumanMessage(content=user_msg_content))
    config = {"recursion_limit": 25}
    
    # SSE 제너레이터 함수 정의
    async def event_generator():
        try:
            # astream_events(version="v2") API를 기동하여 토큰 및 도구 실행 과정 스트리밍
            async for event in agent_graph.astream_events(
                {"messages": input_messages},
                version="v2",
                config=config
            ):
                kind = event.get("event")
                
                # (A) LLM이 토큰을 생성할 때
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload_data = {
                            "type": "token",
                            "content": chunk.content
                        }
                        yield f"data: {json.dumps(payload_data, ensure_ascii=False)}\n\n"
                        
                # (B) 도구 실행이 시작될 때
                elif kind == "on_tool_start":
                    name = event.get("name")
                    inputs = event.get("data", {}).get("input")
                    payload_data = {
                        "type": "tool_start",
                        "name": name,
                        "args": inputs
                    }
                    yield f"data: {json.dumps(payload_data, ensure_ascii=False)}\n\n"
                    
                # (C) 도구 실행이 끝났을 때
                elif kind == "on_tool_end":
                    name = event.get("name")
                    output = event.get("data", {}).get("output")
                    payload_data = {
                        "type": "tool_end",
                        "name": name,
                        "output": str(output)
                    }
                    yield f"data: {json.dumps(payload_data, ensure_ascii=False)}\n\n"
                
                await asyncio.sleep(0.001)  # 양보
                
        except Exception as e:
            logger.error(f"스트리밍 처리 중 에러 발생: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/upload")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """
    사용자가 기상 CSV 파일 등 데이터 분석 대상 파일을 업로드하는 엔드포인트입니다.
    업로드된 파일은 프로젝트 내 'uploads' 폴더에 보관되며 에이전트가 이를 접근하여 분석할 수 있습니다.
    """
    logger.info(f"파일 업로드 요청 수신: 파일명={file.filename}")
    try:
        # 프로젝트 루트에 uploads 폴더 생성
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        logger.info(f"파일 업로드 완료. 저장 경로: {file_path}")
        return {
            "status": "success",
            "message": f"성공적으로 파일 '{file.filename}'이 업로드되었습니다.",
            "file_name": file.filename,
            "file_path": file_path
        }
    except Exception as e:
        logger.error(f"파일 업로드 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 업로드에 실패했습니다: {str(e)}")
