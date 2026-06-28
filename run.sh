#!/usr/bin/env bash

# 오류 발생 시 스크립트 실행 중단
set -e

# 스크립트가 위치한 디렉토리를 루트 경로로 잡고 이동
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

echo "=========================================================="
echo "🤖 ReAct 에이전트 프레임워크 자동화 실행 스크립트"
echo "=========================================================="

# 1. 가상환경 (.venv) 디렉토리 체크 및 복구
if [ ! -d ".venv" ]; then
    echo "ℹ️ 가상환경(.venv)이 존재하지 않아 새로 생성합니다..."
    python3.11 -m venv .venv
    echo "✅ 가상환경 생성 완료."
    
    echo "ℹ️ requirements.txt 기반으로 의존성 패키지를 설치합니다..."
    ./.venv/bin/pip install --upgrade pip
    ./.venv/bin/pip install -r requirements.txt
    echo "✅ 패키지 설치가 완료되었습니다."
fi

# 2. 가상환경 활성화
source .venv/bin/activate

# 3. 입력 인자 파싱 및 실행 분기
ACTION=${1:-dev}

case "$ACTION" in
    test|t)
        echo "🧪 [단위 테스트] Pytest를 사용하여 테스트 코드를 실행합니다..."
        PYTHONPATH=. pytest tests/
        ;;
    dev|d)
        echo "🌐 [개발 서버 구동] Uvicorn 서버를 실행합니다..."
        echo "👉 API 문서 주소: http://localhost:8000/docs"
        uvicorn src.main:app --reload --port 8000
        ;;
    ui|app)
        echo "🎨 [프론트엔드 구동] Streamlit 웹 클라이언트를 실행합니다..."
        echo "👉 웹 앱 주소: http://localhost:8501"
        streamlit run src/app.py --server.port 8501
        ;;
    help|h|*)
        echo "📖 [도움말]"
        echo "사용법: ./run.sh [명령어]"
        echo ""
        echo "명령어 목록:"
        echo "  dev (또는 d)   : FastAPI Uvicorn 개발 서버를 실행합니다 (포트 8000, 기본값)"
        echo "  ui (또는 app)  : Streamlit 웹 어플리케이션을 기동합니다 (포트 8501)"
        echo "  test (또는 t)  : pytest 단위 테스트를 일괄 실행합니다"
        echo "  help (또는 h)  : 이 도움말 메세지를 출력합니다"
        ;;
esac
