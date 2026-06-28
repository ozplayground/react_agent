import os
import json

# 실제 PostgreSQL 연결을 강제 활성화합니다.
os.environ["POSTGRES_LIVE_TEST"] = "true"

from src.tools.db_tools import query_postgres, create_or_alter_table_from_file, upsert_data_from_json, query_weather

print("======================================================================")
print("🔍 2026년 1월 ~ 7월 대용량 날씨 데이터 업로드 및 복합 기간 쿼리 검증")
print("======================================================================")

table_name = "weather_data"
schema_json_path = "/Users/wonyoung/workspace/react_agent/scratch/weather_schema.json"
data_json_path = "/Users/wonyoung/workspace/react_agent/scratch/weather_data.json"

# 0. 기존 테이블 삭제
print("0. 기존 테이블 삭제 (Drop Table)...")
query_postgres.invoke({"query": f"DROP TABLE IF EXISTS {table_name} CASCADE;"})
print("-" * 70)


# 1단계: 스키마 JSON 파일 로드 (만약 파일이 없으면 새로 생성)
print("1. 스키마 JSON 명세 확인...")
schema_def = {
    "table_name": table_name,
    "table_comment": "날씨 데이터 분석을 통해 생성된 기상 상세 테이블 (2026년 1월~7월 일별 데이터 포함)",
    "columns": [
        {"name": "date", "type": "DATE", "primary_key": True, "nullable": False, "comment": "date 컬럼 (기본키)"},
        {"name": "min_temp", "type": "DOUBLE PRECISION", "primary_key": False, "nullable": True, "comment": "min_temp 컬럼 (기상 정보 상세 데이터)"},
        {"name": "max_temp", "type": "DOUBLE PRECISION", "primary_key": False, "nullable": True, "comment": "max_temp 컬럼 (기상 정보 상세 데이터)"},
        {"name": "condition", "type": "VARCHAR(255)", "primary_key": False, "nullable": True, "comment": "condition 컬럼 (기상 정보 상세 데이터)"},
        {"name": "precipitation_probability", "type": "INTEGER", "primary_key": False, "nullable": True, "comment": "precipitation_probability 컬럼 (기상 정보 상세 데이터)"},
        {"name": "precipitation", "type": "DOUBLE PRECISION", "primary_key": False, "nullable": True, "comment": "precipitation 컬럼 (기상 정보 상세 데이터)"},
        {"name": "snowfall", "type": "DOUBLE PRECISION", "primary_key": False, "nullable": True, "comment": "snowfall 컬럼 (기상 정보 상세 데이터)"},
        {"name": "wind_speed", "type": "DOUBLE PRECISION", "primary_key": False, "nullable": True, "comment": "wind_speed 컬럼 (기상 정보 상세 데이터)"},
        {"name": "wind_direction", "type": "VARCHAR(255)", "primary_key": False, "nullable": True, "comment": "wind_direction 컬럼 (기상 정보 상세 데이터)"}
    ],
    "indexes": [
        {"name": f"idx_{table_name}_condition", "columns": ["condition"]}
    ]
}

with open(schema_json_path, "w", encoding="utf-8") as f:
    json.dump(schema_def, f, indent=2, ensure_ascii=False)
schema_json_content = json.dumps(schema_def, ensure_ascii=False, indent=2)


# 2단계: 테이블 생성 도구를 호출하여 테이블 및 코멘트/인덱스 생성
print("2. create_or_alter_table_from_file 도구 호출 (파일명 및 내용 업로드)...")
result_ddl = create_or_alter_table_from_file.invoke({
    "file_name": "weather_schema.json",
    "file_content": schema_json_content
})
print("👉 테이블 생성 결과:", result_ddl)
print("-" * 70)


# 3단계: 생성된 212일간의 날씨 데이터 파일(weather_data.json)을 로드하여 업로드 적재
print("3. weather_data.json (2026년 1월~7월 일별 데이터) 로드 및 upsert_data_from_json 호출...")
with open(data_json_path, "r", encoding="utf-8") as f:
    data_content = f.read()
    
# 데이터 내용 파싱 확인을 위해 카운트 획득
parsed_data = json.loads(data_content)
print(f"👉 로드한 데이터 레코드 수: {len(parsed_data.get('records', []))}건 (2026년 1월 1일 ~ 7월 31일 일별)")

result_upload = upsert_data_from_json.invoke({
    "file_name": "weather_data.json",
    "file_content": data_content
})
print("👉 데이터 적재 결과:", result_upload)
print("-" * 70)


# 4단계: 스키마 불일치 피드백 루프 검증 (인위적으로 wind_direction 컬럼 DROP)
print("4. DB 테이블에서 wind_direction 컬럼을 제거하여 스키마 불일치 유발...")
query_postgres.invoke({"query": f"ALTER TABLE {table_name} DROP COLUMN wind_direction;"})

print("\n테이블 생성/수정 도구를 호출하여 누락 컬럼 감지 피드백 반환 여부 검증...")
result_scenario_2 = create_or_alter_table_from_file.invoke({
    "file_name": "weather_schema.json",
    "file_content": schema_json_content
})
print("\n🔥 도구의 반환 피드백:")
print(result_scenario_2)
print("-" * 70)


# 5단계: 피드백 수신 후 ALTER TABLE DDL 실행 복구 및 재적재
print("5. 에이전트가 피드백을 받아 ALTER TABLE 및 코멘트 추가 실행...")
alter_query = f"""
ALTER TABLE {table_name} ADD COLUMN wind_direction VARCHAR(255);
COMMENT ON COLUMN {table_name}.wind_direction IS 'wind_direction 컬럼 (기상 정보 상세 데이터)';
"""
query_postgres.invoke({"query": alter_query})

print("\n스키마 복구 후 데이터 재적재 도구(upsert_data_from_json) 호출...")
result_scenario_3 = upsert_data_from_json.invoke({
    "file_name": "weather_data.json",
    "file_content": data_content
})
print("👉 적재 결과:", result_scenario_3)
print("-" * 70)


# 6. 최종 다계절 기상 조회 테스트
print("6. 다계절 날씨 데이터 조회 테스트")

print("\n(1) [겨울 시즌 조회] 2026년 1월에 적설량(snowfall)이 있는 날 기상 관측...")
winter_query = """
SELECT date, min_temp, max_temp, condition, snowfall 
FROM weather_data 
WHERE date BETWEEN '2026-01-01' AND '2026-02-28' AND snowfall > 0.0
ORDER BY date ASC 
LIMIT 5;
"""
res_winter = query_postgres.invoke({"query": winter_query})
print("👉 겨울 눈 온 날 결과:")
print(json.dumps(json.loads(res_winter), indent=2, ensure_ascii=False))

print("\n(2) [여름 시즌 조회] 2026년 7월에 강수량(precipitation)이 15mm 이상 내린 날 조회...")
summer_query = """
SELECT date, min_temp, max_temp, condition, precipitation 
FROM weather_data 
WHERE date BETWEEN '2026-07-01' AND '2026-07-31' AND precipitation >= 15.0
ORDER BY date ASC 
LIMIT 5;
"""
res_summer = query_postgres.invoke({"query": summer_query})
print("👉 여름 폭우/비 온 날 결과:")
print(json.dumps(json.loads(res_summer), indent=2, ensure_ascii=False))

print("\n(3) query_weather 도구를 사용하여 2026년 6월 15일 ~ 2026-06-20 비 온 날 조회...")
res_tool = query_weather.invoke({
    "start_date": "2026-06-15",
    "end_date": "2026-06-20",
    "condition": "비"
})
print("👉 query_weather 도구 조회 결과:")
print(json.dumps(json.loads(res_tool), indent=2, ensure_ascii=False))
print("======================================================================")
