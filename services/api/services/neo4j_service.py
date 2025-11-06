"""
Neo4j service for knowledge graph operations
"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import structlog
from config import settings

logger = structlog.get_logger()


class Neo4jService:
    """Neo4j service wrapper for knowledge graph"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

    def verify_connectivity(self):
        """Verify Neo4j connection"""
        self.driver.verify_connectivity()

    def execute_query(self, query: str, parameters: Dict[str, Any] = None):
        """Execute Cypher query"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    async def create_company_node(self, company_data: Dict[str, Any]):
        """Create or update company node"""
        query = """
        MERGE (c:Company {company_id: $company_id})
        SET c.name = $name,
            c.domain = $domain,
            c.industry = $industry,
            c.country = $country,
            c.size = $size,
            c.updated_at = datetime()
        RETURN c
        """
        return self.execute_query(query, company_data)

    async def create_technology_relationship(self, company_id: int, tech_name: str):
        """Create relationship between company and technology"""
        query = """
        MATCH (c:Company {company_id: $company_id})
        MERGE (t:Technology {name: $tech_name})
        MERGE (c)-[r:USES]->(t)
        SET r.detected_at = datetime()
        RETURN c, r, t
        """
        return self.execute_query(query, {
            "company_id": company_id,
            "tech_name": tech_name
        })

    async def create_event_node(self, event_data: Dict[str, Any]):
        """Create event node and link to company"""
        query = """
        MATCH (c:Company {company_id: $company_id})
        CREATE (e:Event {
            event_id: $event_id,
            type: $event_type,
            url: $url,
            timestamp: datetime($timestamp)
        })
        CREATE (c)-[:HAS_EVENT]->(e)
        RETURN e
        """
        return self.execute_query(query, event_data)

    async def create_signal_relationship(self, signal_data: Dict[str, Any]):
        """Create signal node and relationships"""
        query = """
        MATCH (c:Company {company_id: $company_id})
        CREATE (s:Signal {
            signal_id: $signal_id,
            kind: $kind,
            score: $score,
            timestamp: datetime($timestamp)
        })
        CREATE (c)-[:HAS_SIGNAL]->(s)
        RETURN s
        """
        return self.execute_query(query, signal_data)

    async def find_related_companies(self, company_id: int, relationship_type: str = None) -> List[Dict]:
        """Find companies related through specific relationships"""
        if relationship_type:
            query = """
            MATCH (c:Company {company_id: $company_id})-[r]->(related:Company)
            WHERE type(r) = $rel_type
            RETURN related, type(r) as relationship
            """
            params = {"company_id": company_id, "rel_type": relationship_type}
        else:
            query = """
            MATCH (c:Company {company_id: $company_id})-[r]-(related:Company)
            RETURN related, type(r) as relationship
            """
            params = {"company_id": company_id}

        return self.execute_query(query, params)

    async def find_companies_using_tech(self, tech_name: str) -> List[Dict]:
        """Find all companies using a specific technology"""
        query = """
        MATCH (c:Company)-[:USES]->(t:Technology {name: $tech_name})
        RETURN c
        """
        return self.execute_query(query, {"tech_name": tech_name})

    async def get_company_graph(self, company_id: int, depth: int = 2) -> Dict[str, Any]:
        """Get subgraph around a company"""
        query = """
        MATCH path = (c:Company {company_id: $company_id})-[*1..$depth]-(related)
        RETURN path
        """
        results = self.execute_query(query, {"company_id": company_id, "depth": depth})

        # Process results into nodes and relationships
        nodes = {}
        relationships = []

        for record in results:
            path = record.get("path")
            # Process path data
            # This is simplified - actual implementation would extract nodes and rels

        return {
            "nodes": list(nodes.values()),
            "relationships": relationships
        }

    async def find_similar_companies(self, company_id: int, limit: int = 10) -> List[Dict]:
        """Find similar companies based on shared characteristics"""
        query = """
        MATCH (c:Company {company_id: $company_id})
        MATCH (c)-[:USES]->(t:Technology)<-[:USES]-(similar:Company)
        WHERE similar.company_id <> $company_id
        WITH similar, count(t) as common_tech
        ORDER BY common_tech DESC
        LIMIT $limit
        RETURN similar, common_tech
        """
        return self.execute_query(query, {"company_id": company_id, "limit": limit})

    async def create_partnership_relationship(self, company_id_1: int, company_id_2: int):
        """Create partnership relationship between companies"""
        query = """
        MATCH (c1:Company {company_id: $company_id_1})
        MATCH (c2:Company {company_id: $company_id_2})
        MERGE (c1)-[r:PARTNERS_WITH]-(c2)
        SET r.created_at = datetime()
        RETURN r
        """
        return self.execute_query(query, {
            "company_id_1": company_id_1,
            "company_id_2": company_id_2
        })


# Global instance
neo4j_driver = Neo4jService()
