"""
OpenSearch service for full-text and vector search
"""
from opensearchpy import OpenSearch, helpers
import structlog
from config import settings
from typing import List, Dict, Any

logger = structlog.get_logger()


class OpenSearchService:
    """OpenSearch service wrapper"""

    def __init__(self):
        self.client = OpenSearch(
            hosts=[settings.OPENSEARCH_URL],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        self.indices = {
            "events": "events",
            "signals": "signals",
            "companies": "companies"
        }

    async def initialize_indices(self):
        """Create OpenSearch indices with mappings"""
        # Events index
        if not self.client.indices.exists(index=self.indices["events"]):
            self.client.indices.create(
                index=self.indices["events"],
                body={
                    "mappings": {
                        "properties": {
                            "company_id": {"type": "integer"},
                            "event_type": {"type": "keyword"},
                            "url": {"type": "keyword"},
                            "title": {"type": "text"},
                            "text": {"type": "text"},
                            "timestamp": {"type": "date"},
                            "language": {"type": "keyword"},
                            "features": {"type": "object"},
                            "embedding": {"type": "knn_vector", "dimension": 768}
                        }
                    }
                }
            )
            logger.info("Created events index")

        # Signals index
        if not self.client.indices.exists(index=self.indices["signals"]):
            self.client.indices.create(
                index=self.indices["signals"],
                body={
                    "mappings": {
                        "properties": {
                            "company_id": {"type": "integer"},
                            "company_name": {"type": "text"},
                            "product_id": {"type": "keyword"},
                            "kind": {"type": "keyword"},
                            "score": {"type": "float"},
                            "confidence": {"type": "float"},
                            "timestamp_start": {"type": "date"},
                            "explanation": {"type": "text"},
                            "evidence": {"type": "nested"},
                            "is_active": {"type": "boolean"},
                            "actioned": {"type": "boolean"}
                        }
                    }
                }
            )
            logger.info("Created signals index")

        # Companies index
        if not self.client.indices.exists(index=self.indices["companies"]):
            self.client.indices.create(
                index=self.indices["companies"],
                body={
                    "mappings": {
                        "properties": {
                            "company_id": {"type": "integer"},
                            "name": {"type": "text"},
                            "domain": {"type": "keyword"},
                            "country": {"type": "keyword"},
                            "industry": {"type": "keyword"},
                            "sector": {"type": "keyword"},
                            "size": {"type": "keyword"},
                            "description": {"type": "text"},
                            "tech_stack": {"type": "keyword"}
                        }
                    }
                }
            )
            logger.info("Created companies index")

    async def index_document(self, index: str, doc_id: int, document: Dict[str, Any]):
        """Index a single document"""
        try:
            self.client.index(
                index=index,
                id=doc_id,
                body=document,
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index document: {e}", index=index, doc_id=doc_id)
            return False

    async def search(self, index: str, query: Dict[str, Any], size: int = 50, from_: int = 0):
        """Execute search query"""
        try:
            response = self.client.search(
                index=index,
                body={"query": query, "size": size, "from": from_}
            )
            return response["hits"]["hits"]
        except Exception as e:
            logger.error(f"Search failed: {e}", index=index)
            return []

    async def search_signals(self, filters: Dict[str, Any], size: int = 50, from_: int = 0):
        """Search signals with filters"""
        must_clauses = []

        if filters.get("query"):
            must_clauses.append({
                "multi_match": {
                    "query": filters["query"],
                    "fields": ["company_name^3", "explanation", "evidence.snippet"]
                }
            })

        if filters.get("product_id"):
            must_clauses.append({"term": {"product_id": filters["product_id"]}})

        if filters.get("kind"):
            must_clauses.append({"term": {"kind": filters["kind"]}})

        if filters.get("min_score"):
            must_clauses.append({"range": {"score": {"gte": filters["min_score"]}}})

        if filters.get("is_active") is not None:
            must_clauses.append({"term": {"is_active": filters["is_active"]}})

        if filters.get("company_ids"):
            must_clauses.append({"terms": {"company_id": filters["company_ids"]}})

        if filters.get("start_date") or filters.get("end_date"):
            date_range = {}
            if filters.get("start_date"):
                date_range["gte"] = filters["start_date"]
            if filters.get("end_date"):
                date_range["lte"] = filters["end_date"]
            must_clauses.append({"range": {"timestamp_start": date_range}})

        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}

        return await self.search(
            self.indices["signals"],
            query,
            size=size,
            from_=from_
        )

    async def bulk_index(self, index: str, documents: List[Dict[str, Any]]):
        """Bulk index documents"""
        actions = [
            {
                "_index": index,
                "_id": doc.get("id"),
                "_source": doc
            }
            for doc in documents
        ]

        try:
            success, failed = helpers.bulk(self.client, actions, raise_on_error=False)
            logger.info(f"Bulk indexed: {success} success, {len(failed)} failed", index=index)
            return success
        except Exception as e:
            logger.error(f"Bulk index failed: {e}", index=index)
            return 0


# Global instance
opensearch_client = OpenSearchService()
