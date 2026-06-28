import os
from pymilvus import connections, Collection, utility
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MilvusConnector:
    """
    Milvus 벡터 데이터베이스 연결 및 벡터 검색 작업을 관리합니다.
    연결이 실패하거나 모의 환경인 경우 Mock 응답으로 대체됩니다.
    """
    def __init__(self):
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.use_mock = False
        self.alias = "default"

    def connect(self):
        # 로컬 테스트 환경이거나 플레이스홀더 기본값이 감지되면 Mock 모드로 작동
        if (self.uri == "http://localhost:19530" and not os.environ.get("MILVUS_LIVE_TEST")):
            logger.info("Milvus 커넥터가 모의(Mock) 모드로 초기화되었습니다 (기본 설정 감지).")
            self.use_mock = True
            return

        try:
            connections.connect(
                alias=self.alias,
                uri=self.uri,
                token=self.token
            )
            logger.info("Milvus 벡터 데이터베이스 연결에 성공했습니다.")
        except Exception as e:
            logger.warning(f"Milvus 연결 실패 ({e}). 모의(Mock) 모드로 전환합니다.")
            self.use_mock = True

    def search_vectors(self, collection_name: str, query_vector: list, top_k: int = 3) -> list:
        """
        컬렉션 이름과 쿼리 벡터를 사용하여 Milvus에서 벡터 검색을 수행합니다.
        """
        if self.use_mock:
            logger.info(f"[Mock Milvus] 컬렉션 '{collection_name}' 검색 시뮬레이션 (벡터 크기: {len(query_vector)})")
            # 모의 메타데이터 검색 결과 반환
            return [
                {"id": 1001, "distance": 0.985, "metadata": {"title": "LangGraph Documentation", "category": "AI"}},
                {"id": 1002, "distance": 0.874, "metadata": {"title": "FastAPI Deployment Guide", "category": "DevOps"}},
                {"id": 1003, "distance": 0.762, "metadata": {"title": "Oracle DB administration", "category": "Database"}}
            ]

        try:
            if not utility.has_collection(collection_name, using=self.alias):
                logger.error(f"Milvus 컬렉션 '{collection_name}'이 존재하지 않습니다.")
                return []
            
            collection = Collection(collection_name, using=self.alias)
            collection.load()
            
            # Milvus 일반적인 검색 설정
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["*"]
            )
            
            hits = []
            for hit in results[0]:
                entity_data = hit.entity.to_dict().get("entity", {}) if hasattr(hit, "entity") else {}
                hits.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "metadata": entity_data
                })
            return hits
        except Exception as e:
            logger.error(f"Milvus 벡터 검색 실패: {e}")
            raise e

    def close(self):
        if not self.use_mock:
            try:
                connections.disconnect(self.alias)
                logger.info("Milvus 연결이 해제되었습니다.")
            except Exception:
                pass
            
            
            
            
