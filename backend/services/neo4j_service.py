import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Neo4jService:
    def __init__(self) -> None:
        self.driver: Any = None
        self._connect()

    def _connect(self) -> None:
        try:
            from neo4j import GraphDatabase  # type: ignore[import]

            uri = os.environ.get("NEO4J_URI", "")
            username = os.environ.get("NEO4J_USERNAME", "neo4j")
            password = os.environ.get("NEO4J_PASSWORD", "")

            if not uri or not password:
                logger.info("Neo4j credentials not configured; graph features disabled.")
                return

            driver = GraphDatabase.driver(uri, auth=(username, password))
            driver.verify_connectivity()

            # Create indexes
            with driver.session() as session:
                session.run("CREATE INDEX clause_session IF NOT EXISTS FOR (c:Clause) ON (c.session_id)")
                session.run("CREATE INDEX law_citation IF NOT EXISTS FOR (l:Law) ON (l.citation)")

            self.driver = driver
            logger.info("Neo4j connected successfully.")
        except Exception as exc:
            logger.warning("Neo4j connection failed (graph features disabled): %s", exc)
            self.driver = None

    def is_connected(self) -> bool:
        if self.driver is None:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def store_analysis(self, session_id: str, clauses: list[dict[str, Any]]) -> bool:
        """Store analysis results in Neo4j. Returns False on failure (non-blocking)."""
        if self.driver is None:
            return False
        try:
            with self.driver.session() as session:
                for clause in clauses:
                    session.run(
                        """
                        MERGE (l:Law {citation: $citation})
                        ON CREATE SET l.name = $citation
                        CREATE (c:Clause {
                            session_id: $session_id,
                            clause_text: $clause_text,
                            violation_type: $violation_type,
                            severity: $severity,
                            explanation: $explanation
                        })
                        MERGE (r:Remedy {text: $remedy})
                        CREATE (c)-[:VIOLATES]->(l)
                        CREATE (c)-[:HAS_REMEDY]->(r)
                        """,
                        session_id=session_id,
                        citation=clause.get("legal_citation", "Unknown"),
                        clause_text=clause.get("clause_text", "")[:500],
                        violation_type=clause.get("violation_type", ""),
                        severity=clause.get("severity", "low"),
                        explanation=clause.get("explanation", ""),
                        remedy=clause.get("remedy", ""),
                    )
            return True
        except Exception as exc:
            logger.warning("Neo4j store_analysis failed: %s", exc)
            return False

    def get_graph(self, session_id: str) -> dict[str, list[dict[str, Any]]]:
        """Return nodes and edges for a session. Returns empty on failure."""
        if self.driver is None:
            return {"nodes": [], "edges": []}
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (c:Clause {session_id: $session_id})-[:VIOLATES]->(l:Law)
                    OPTIONAL MATCH (c)-[:HAS_REMEDY]->(r:Remedy)
                    RETURN c, l, r
                    """,
                    session_id=session_id,
                )
                nodes: list[dict[str, Any]] = []
                edges: list[dict[str, Any]] = []
                seen_nodes: set[str] = set()

                for record in result:
                    clause_node = record["c"]
                    law_node = record["l"]
                    remedy_node = record["r"]

                    c_id = f"clause-{clause_node.element_id}"
                    l_id = f"law-{law_node.element_id}"

                    if c_id not in seen_nodes:
                        nodes.append({"id": c_id, "label": clause_node["violation_type"], "type": "clause"})
                        seen_nodes.add(c_id)

                    if l_id not in seen_nodes:
                        nodes.append({"id": l_id, "label": law_node["citation"], "type": "law"})
                        seen_nodes.add(l_id)

                    edges.append({"source": c_id, "target": l_id, "relationship": "VIOLATES"})

                    if remedy_node is not None:
                        r_id = f"remedy-{remedy_node.element_id}"
                        if r_id not in seen_nodes:
                            nodes.append({"id": r_id, "label": remedy_node["text"][:80], "type": "remedy"})
                            seen_nodes.add(r_id)
                        edges.append({"source": c_id, "target": r_id, "relationship": "HAS_REMEDY"})

                return {"nodes": nodes, "edges": edges}
        except Exception as exc:
            logger.warning("Neo4j get_graph failed: %s", exc)
            return {"nodes": [], "edges": []}

    def close(self) -> None:
        if self.driver is not None:
            try:
                self.driver.close()
            except Exception:
                pass
            self.driver = None


neo4j_service = Neo4jService()
