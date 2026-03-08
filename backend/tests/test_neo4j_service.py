"""Service-level unit tests for neo4j_service.Neo4jService."""
import os
from unittest.mock import MagicMock, patch

import neo4j
import services.neo4j_service as _svc_mod
from services.neo4j_service import Neo4jService

# Capture the real _connect before the session-scoped 'client' fixture from conftest.py
# patches it at the class level. Module import happens during collection (before fixtures run).
_REAL_CONNECT = _svc_mod.Neo4jService._connect


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_service_with_driver() -> tuple["Neo4jService", MagicMock]:
    """Create a Neo4jService bypassing __init__, injecting a mock driver."""
    svc = Neo4jService.__new__(Neo4jService)
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
    svc.driver = mock_driver
    return svc, mock_session


def _sample_clauses() -> list[dict]:
    return [
        {
            "legal_citation": "CA Civil Code §1941",
            "clause_text": "Tenant waives habitability.",
            "violation_type": "Habitability waiver",
            "severity": "high",
            "explanation": "Cannot waive habitability.",
            "remedy": "Clause is void.",
        }
    ]


# ── _connect ──────────────────────────────────────────────────────────────────


def test_neo4j_connect_success_verifies_connectivity_and_creates_indexes():
    """_connect() calls verify_connectivity() and creates both indexes on success."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    svc = Neo4jService.__new__(Neo4jService)
    svc.driver = None

    # Restore the real _connect (session fixture may have patched it) and call it
    # directly with all inner dependencies mocked.
    with (
        patch.dict(
            os.environ,
            {
                "NEO4J_URI": "neo4j+s://test.databases.neo4j.io",
                "NEO4J_PASSWORD": "secret",
                "NEO4J_USERNAME": "neo4j",
            },
        ),
        patch.object(neo4j.GraphDatabase, "driver", return_value=mock_driver),
    ):
        _REAL_CONNECT(svc)

    mock_driver.verify_connectivity.assert_called_once()
    assert mock_session.run.call_count == 2  # two CREATE INDEX statements
    assert svc.driver is mock_driver


def test_neo4j_connect_failure_sets_driver_to_none_without_raising():
    """_connect() sets self.driver = None and does not raise on failure."""
    svc = Neo4jService.__new__(Neo4jService)
    svc.driver = None

    with (
        patch.dict(
            os.environ,
            {"NEO4J_URI": "neo4j+s://test.databases.neo4j.io", "NEO4J_PASSWORD": "secret"},
        ),
        patch.object(neo4j.GraphDatabase, "driver", side_effect=Exception("Connection refused")),
    ):
        _REAL_CONNECT(svc)  # Should not raise

    assert svc.driver is None


# ── store_analysis ────────────────────────────────────────────────────────────


def test_neo4j_store_analysis_with_driver_calls_merge_for_each_clause():
    """store_analysis() calls session.run (MERGE) once per clause and returns True."""
    svc, mock_session = _make_service_with_driver()

    result = svc.store_analysis("session-abc", _sample_clauses())

    assert result is True
    mock_session.run.assert_called_once()
    # Verify the MERGE keyword appears in the query
    call_args = mock_session.run.call_args
    query = call_args.args[0] if call_args.args else call_args[0][0]
    assert "MERGE" in query


def test_neo4j_store_analysis_without_driver_returns_false_without_crashing():
    """store_analysis() with driver=None silently returns False."""
    svc = Neo4jService.__new__(Neo4jService)
    svc.driver = None

    result = svc.store_analysis("session-xyz", _sample_clauses())

    assert result is False


def test_neo4j_store_analysis_db_error_returns_false():
    """store_analysis() returns False when session.run raises an exception."""
    svc, mock_session = _make_service_with_driver()
    mock_session.run.side_effect = Exception("DB write error")

    result = svc.store_analysis("session-err", _sample_clauses())

    assert result is False


# ── get_graph ─────────────────────────────────────────────────────────────────


def test_neo4j_get_graph_without_driver_returns_empty():
    """get_graph() with driver=None returns empty nodes and edges."""
    svc = Neo4jService.__new__(Neo4jService)
    svc.driver = None

    result = svc.get_graph("session-xyz")

    assert result == {"nodes": [], "edges": []}


def test_neo4j_get_graph_with_driver_returns_graph_data():
    """get_graph() with a working driver returns populated nodes and edges."""
    svc, mock_session = _make_service_with_driver()

    # Build a mock record with clause, law, and remedy nodes
    clause_node = MagicMock()
    clause_node.element_id = "1"
    clause_node.__getitem__ = MagicMock(
        side_effect=lambda k: "Habitability waiver" if k == "violation_type" else ""
    )

    law_node = MagicMock()
    law_node.element_id = "2"
    law_node.__getitem__ = MagicMock(
        side_effect=lambda k: "CA Civil Code §1941" if k == "citation" else ""
    )

    remedy_node = MagicMock()
    remedy_node.element_id = "3"
    remedy_node.__getitem__ = MagicMock(
        side_effect=lambda k: "Clause is void." if k == "text" else ""
    )

    record = {"c": clause_node, "l": law_node, "r": remedy_node}
    mock_session.run.return_value = [record]

    result = svc.get_graph("session-abc")

    assert "nodes" in result
    assert "edges" in result
    assert len(result["nodes"]) > 0
    assert len(result["edges"]) > 0

