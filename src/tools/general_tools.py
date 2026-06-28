import math
from langchain_core.tools import tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

@tool
def calculator(expression: str) -> str:
    """
    안전한 Python 내장 표현식 평가기(eval)를 활용하여 전달받은 수학 계산 수식을 실행하고 그 결과를 문자열로 반환합니다.
    사칙연산, 거듭제곱 및 삼각함수 등 수학 연산이 요구될 때 이 도구를 사용합니다.

    Args:
        expression (str): 평가할 파이썬 수학 표현식 (예: '2 * 3.14 * 10' 또는 'math.sqrt(144)').

    Returns:
        str: 수식 연산의 수치 결과값 문자열 (예: '251', '40.0'). 잘못된 수식이나 실행 오류 발생 시 에러 메시지를 반환합니다.
    """
    logger.info(f"calculator 도구가 호출되었습니다. 식: '{expression}'")
    try:
        # 안전한 eval 환경을 구성하기 위해 기본적인 수학 함수들만 포함
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        allowed_names["math"] = math
        # __import__ 와 같은 위험한 빌트인 접근 차단
        val = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(val)
    except Exception as e:
        logger.error(f"calculator 도구 실행 중 오류 발생: {e}")
        return f"수학 식 평가 중 오류가 발생했습니다: {str(e)}. 올바른 숫자와 연산자를 사용했는지 확인하세요."

@tool
def general_web_search(query: str) -> str:
    """
    인터넷 모의 검색 엔진을 통해 지정한 질의어(query)에 대한 검색 결과를 모방하여 관련 상세 정보를 JSON 문자열로 반환합니다.
    에이전트가 데이터베이스에 존재하지 않는 일반적인 사실이나 인터넷 정보를 검색하고자 할 때 이 도구를 사용합니다.

    Args:
        query (str): 검색 포털에 던질 질의어.

    Returns:
        str: 검색어에 따라 매칭되는 뉴스, 시황 정보 또는 가상 요약문이 포함된 텍스트/JSON 직렬화 문자열을 반환합니다.
    """
    logger.info(f"general_web_search 도구가 호출되었습니다. 쿼리: '{query}'")
    query_lower = query.lower()
    
    # 키워드에 따라 모의 검색 결과 반환
    if "weather" in query_lower or "날씨" in query_lower:
        return "검색 결과: 오늘의 날씨는 화창하며 기온은 22°C (71.6°F), 습도는 45%입니다."
    elif "stock" in query_lower or "주식" in query_lower or "시장" in query_lower:
        return "검색 결과: 오늘 주식 시장은 상승 마감했습니다. 기술주가 상승을 주도하며 나스닥 지수가 1.2% 상승했습니다."
    elif "langgraph" in query_lower or "랭그래프" in query_lower:
        return "검색 결과: LangGraph는 LLM을 이용해 상태 제어가 가능한 다중 행위자(multi-actor) 애플리케이션을 빌드하기 위한 라이브러리로, LangChain 위에서 구현되었습니다. 0.3.3 버전에서는 유효성 검증과 실행 성능이 대폭 강화되었습니다."
    else:
        return f"'{query}'에 대한 검색 결과: 온라인 커뮤니티에서 활발한 논의가 관찰되고 있으며 전반적으로 긍정적인 반응이 우세합니다. 특별한 비상 사태나 긴급 뉴스는 감지되지 않았습니다."
