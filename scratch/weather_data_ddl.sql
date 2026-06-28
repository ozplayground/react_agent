-- -----------------------------------------------------
-- 에이전트가 데이터를 분석하여 자동 생성한 테이블 DDL
-- 원천 분석 데이터: weather_data.csv
-- 생성 일자: 2026-06-27
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS weather_data (
    date DATE PRIMARY KEY,
    min_temp DOUBLE PRECISION,
    max_temp DOUBLE PRECISION,
    condition VARCHAR(255),
    precipitation_probability INTEGER,
    precipitation DOUBLE PRECISION,
    snowfall DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction VARCHAR(255)
);

COMMENT ON TABLE weather_data IS 'CSV 파일(weather_data.csv)로부터 동적 생성된 데이터 테이블';
COMMENT ON COLUMN weather_data.date IS 'date 컬럼 (기본키)';
COMMENT ON COLUMN weather_data.min_temp IS 'min_temp 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.max_temp IS 'max_temp 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.condition IS 'condition 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.precipitation_probability IS 'precipitation_probability 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.precipitation IS 'precipitation 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.snowfall IS 'snowfall 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.wind_speed IS 'wind_speed 컬럼 (상세 데이터)';
COMMENT ON COLUMN weather_data.wind_direction IS 'wind_direction 컬럼 (상세 데이터)';
CREATE INDEX IF NOT EXISTS idx_weather_data_condition ON weather_data (condition);