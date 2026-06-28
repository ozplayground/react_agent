import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # LLM 제공자 제어 변수 ('openai' 또는 'gemini')
    llm_provider: str = Field(default="openai", validation_alias="LLM_PROVIDER")

    # OpenAI 설정 정보
    openai_api_key: str = Field(default="mock-key", validation_alias="OPENAI_API_KEY")
    openai_model_name: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL_NAME")
    openai_temperature: float = Field(default=0.0, validation_alias="OPENAI_TEMPERATURE")

    # Gemini 설정 정보
    gemini_api_key: str = Field(default="mock-key", validation_alias="GEMINI_API_KEY")
    gemini_model_name: str = Field(default="gemini-1.5-flash", validation_alias="GEMINI_MODEL_NAME")
    gemini_temperature: float = Field(default=0.0, validation_alias="GEMINI_TEMPERATURE")

    # 로컬 OpenAI 호환 모델 설정 정보 (LM Studio, Ollama, vLLM 등)
    local_model_api_key: str = Field(default="lm-studio", validation_alias="LOCAL_MODEL_API_KEY")
    local_model_base_url: str = Field(default="http://localhost:1234/v1", validation_alias="LOCAL_MODEL_BASE_URL")
    local_model_name: str = Field(default="meta-llama-3-8b-instruct", validation_alias="LOCAL_MODEL_NAME")
    local_model_temperature: float = Field(default=0.0, validation_alias="LOCAL_MODEL_TEMPERATURE")

    # PostgreSQL 데이터베이스 설정
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="agent_db", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", validation_alias="POSTGRES_PASSWORD")

    # Oracle 데이터베이스 설정
    oracle_user: str = Field(default="system", validation_alias="ORACLE_USER")
    oracle_password: str = Field(default="oracle", validation_alias="ORACLE_PASSWORD")
    oracle_dsn: str = Field(default="localhost:1521/XEPDB1", validation_alias="ORACLE_DSN")

    # Milvus 벡터 데이터베이스 설정
    milvus_uri: str = Field(default="http://localhost:19530", validation_alias="MILVUS_URI")
    milvus_token: str = Field(default="", validation_alias="MILVUS_TOKEN")

    # Pydantic Settings 설정 정보
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# 싱글톤 설정 인스턴스 생성
settings = Settings()
