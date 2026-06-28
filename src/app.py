import streamlit as st
import requests
import json
import os
import re
import pandas as pd

# Streamlit 앱 페이지 설정 (Aesthetic Dark Theme 및 탭 타이틀 정의)
st.set_page_config(
    page_title="ReAct Agent Web Client",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 커스텀 CSS 스타일 주입 (Premium look)
st.markdown("""
<style>
    .reportview-container {
        background: #1e1e2e;
    }
    .sidebar .sidebar-content {
        background: #252538;
    }
    h1 {
        color: #f38ba8;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
    }
    .stAlert {
        border-radius: 8px;
    }
    /* 스크롤바 디자인 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1e1e2e;
    }
    ::-webkit-scrollbar-thumb {
        background: #585b70;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

FASTAPI_URL = "http://localhost:8000"

st.title("🤖 ReAct AI 에이전트 통합 웹 클라이언트")
st.caption("FastAPI 백엔드 서버 및 LangGraph 0.3.3 ReAct 엔진과 실시간 SSE 스트리밍으로 상호작용합니다.")

# 1. 세션 상태 (Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

def render_message_with_charts(text_content: str):
    """
    메시지 텍스트 본문에서 ```chart 와 ``` 사이의 JSON 블록을 감지하여
    차트 데이터를 파싱하고, 원본 JSON 블록은 텍스트에서 은닉한 채
    Streamlit의 라인 차트 혹은 바 차트로 세련되게 변환 렌더링합니다.
    """
    chart_pattern = re.compile(r"```chart\s*(.*?)\s*```", re.DOTALL)
    matches = list(chart_pattern.finditer(text_content))
    
    if not matches:
        st.markdown(text_content)
        return
        
    # 차트 JSON 블록들을 숨기고 일반 마크다운만 분리 추출
    last_idx = 0
    clean_text_parts = []
    
    for match in matches:
        start, end = match.span()
        clean_text_parts.append(text_content[last_idx:start])
        last_idx = end
        
    clean_text = "".join(clean_text_parts) + text_content[last_idx:]
    st.markdown(clean_text)
    
    # 추출한 각 차트 정보 렌더링
    for match in matches:
        json_str = match.group(1)
        try:
            chart_spec = json.loads(json_str)
            chart_type = chart_spec.get("chart_type", "line").lower()
            title = chart_spec.get("title", "데이터 시각화 그래프")
            x_axis = chart_spec.get("x_axis", "date")
            y_axes = chart_spec.get("y_axes", [])
            data_records = chart_spec.get("data", [])
            
            if not data_records:
                continue
                
            # Pandas DataFrame으로 가공
            df = pd.DataFrame(data_records)
            
            # Y축 데이터 컬럼을 모두 숫자형으로 안전하게 강제 캐스팅
            for col in y_axes:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            st.markdown(f"##### 📊 {title}")
            
            # 차트 유형에 맞게 렌더링
            if chart_type == "bar":
                st.bar_chart(df, x=x_axis, y=y_axes)
            else:
                st.line_chart(df, x=x_axis, y=y_axes)
                
        except Exception as e:
            # 파싱 실패 시 백업으로 원시 JSON 코드 블록 노출
            st.warning(f"⚠️ 차트 시각화 데이터 변환 중 오류가 발생했습니다: {e}")
            st.code(match.group(0), language="json")

# 2. 사이드바 구성 (파일 업로드 및 상태 표시)
with st.sidebar:
    st.header("📁 파일 업로드 센터")
    st.markdown("데이터 분석을 위한 기상 CSV/JSON 파일을 서버에 전송합니다.")
    
    # 드래그 앤 드롭 파일 업로더
    uploaded_file = st.file_uploader(
        "분석할 데이터 파일 선택",
        type=["csv", "json", "sql"],
        help="사용자가 올린 데이터는 에이전트 추론 루프에서 자동으로 읽혀 테이블 생성 및 데이터 적재에 사용됩니다."
    )
    
    if uploaded_file is not None:
        if (st.session_state.uploaded_file is None or 
            st.session_state.uploaded_file["file_name"] != uploaded_file.name):
            
            with st.spinner("서버로 파일을 전송 중..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{FASTAPI_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        st.session_state.uploaded_file = {
                            "file_name": res_data["file_name"],
                            "file_path": res_data["file_path"]
                        }
                        st.success("✅ 파일 업로드 및 물리 경로 등록 완료!")
                    else:
                        st.error(f"❌ 업로드 실패 (HTTP {response.status_code})")
                except Exception as e:
                    st.error(f"❌ 백엔드 서버 연결 오류: {str(e)}")
    else:
        st.session_state.uploaded_file = None
        
    st.markdown("---")
    st.subheader("💡 활성화된 파일 컨텍스트")
    if st.session_state.uploaded_file:
        st.info(
            f"📄 **파일명**: `{st.session_state.uploaded_file['file_name']}`\n\n"
            f"📂 **서버 경로**: \n`{st.session_state.uploaded_file['file_path']}`"
        )
        if st.button("파일 바인딩 해제"):
            st.session_state.uploaded_file = None
            st.rerun()
    else:
        st.warning("바인딩된 업로드 파일이 없습니다.")
        
    st.markdown("---")
    if st.button("💬 대화 초기화 (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

# 3. 대화창 영역 렌더링 (동적 차트 빌더 적용)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_message_with_charts(msg["content"])

# 4. 사용자 질문 입력 및 SSE 스트리밍 처리
if user_query := st.chat_input("에이전트에게 내릴 명령이나 질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
        
    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        response_placeholder = st.empty()
        
        history_payload = []
        for m in st.session_state.messages[:-1]:
            history_payload.append({
                "role": m["role"],
                "content": m["content"]
            })
            
        payload = {
            "message": user_query,
            "history": history_payload
        }
        
        if st.session_state.uploaded_file:
            payload["file_name"] = st.session_state.uploaded_file["file_name"]
            payload["file_path"] = st.session_state.uploaded_file["file_path"]
            
        thought_logs = []
        final_answer = ""
        
        with st.spinner("에이전트 추론 기동 중..."):
            try:
                response = requests.post(
                    f"{FASTAPI_URL}/chat/stream",
                    json=payload,
                    stream=True
                )
                
                if response.status_code != 200:
                    st.error(f"서버 에러가 발생했습니다. (HTTP {response.status_code})")
                else:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode("utf-8")
                            if decoded_line.startswith("data: "):
                                data_json_str = decoded_line[6:]
                                try:
                                    chunk = json.loads(data_json_str)
                                    
                                    if chunk.get("type") == "error":
                                        st.error(f"에이전트 내부 오류: {chunk.get('content')}")
                                        break
                                        
                                    elif chunk.get("type") == "token":
                                        final_answer += chunk.get("content", "")
                                        response_placeholder.markdown(final_answer)
                                        
                                    elif chunk.get("type") == "tool_start":
                                        name = chunk.get("name")
                                        args = chunk.get("args", {})
                                        args_str = json.dumps(args, ensure_ascii=False)
                                        log_entry = (
                                            f"🧠 **[에이전트 추론]** 도구 `{name}` 호출을 위한 인자 설정 중...\n"
                                            f"🔧 **[도구 호출 대기]** `{name}`\n"
                                            f"- 입력 매개변수: `{args_str}`"
                                        )
                                        thought_logs.append(log_entry)
                                        
                                    elif chunk.get("type") == "tool_end":
                                        name = chunk.get("name")
                                        output = chunk.get("output", "")
                                        log_entry = (
                                            f"⚙️ **[도구 실행 완료]** `{name}`\n"
                                            f"📥 **[실행 결과 반환]**\n```json\n{output}\n```"
                                        )
                                        thought_logs.append(log_entry)
                                                    
                                    if thought_logs:
                                        with progress_placeholder.container():
                                            with st.expander("🧠 **에이전트 추론 및 도구 실행 과정 (상세 로그)**", expanded=True):
                                                for log in thought_logs:
                                                    st.markdown(log)
                                                    
                                except Exception as parse_err:
                                    pass
                                    
                # 스트리밍 완료 후: 임시 홀더를 비우고 정밀 차트가 포함된 최종 카드 출력 및 히스토리 등록
                if final_answer:
                    response_placeholder.empty()
                    with st.container():
                        render_message_with_charts(final_answer)
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
                elif thought_logs and not final_answer:
                    fallback_ans = "요청하신 도구 실행 작업을 정상 완료했습니다."
                    response_placeholder.empty()
                    st.markdown(fallback_ans)
                    st.session_state.messages.append({"role": "assistant", "content": fallback_ans})
                    
            except Exception as conn_err:
                st.error(f"서버와 연결을 맺는 중 오류가 발생했습니다: {str(conn_err)}")
