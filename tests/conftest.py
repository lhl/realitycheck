"""
Pytest fixtures for Reality Check tests.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from db import get_db, init_tables, drop_tables


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_embedding: mark test as requiring embedding model"
    )


def pytest_collection_modifyitems(config, items):
    """Skip embedding tests if REALITYCHECK_EMBED_SKIP is set."""
    if os.environ.get("REALITYCHECK_EMBED_SKIP") or os.environ.get("SKIP_EMBEDDING_TESTS"):
        skip_embedding = pytest.mark.skip(reason="REALITYCHECK_EMBED_SKIP is set")
        for item in items:
            if "requires_embedding" in item.keywords:
                item.add_marker(skip_embedding)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path."""
    return tmp_path / "test.lance"


@pytest.fixture
def initialized_db(temp_db_path: Path):
    """Provide an initialized empty database."""
    db = get_db(temp_db_path)
    init_tables(db)
    yield db
    drop_tables(db)


@pytest.fixture
def sample_claim() -> dict:
    """Provide a sample claim for testing."""
    return {
        "id": "TECH-2026-001",
        "text": "AI training costs double annually",
        "type": "[F]",
        "domain": "TECH",
        "evidence_level": "E2",
        "credence": 0.75,
        "operationalization": "Track published training cost estimates",
        "assumptions": ["Current paradigm continues"],
        "falsifiers": ["Costs flat for 2+ years"],
        "source_ids": ["test-source-001"],
        "first_extracted": "2026-01-19",
        "extracted_by": "test",
        "supports": [],
        "contradicts": [],
        "depends_on": [],
        "modified_by": [],
        "part_of_chain": "",
        "version": 1,
        "last_updated": "2026-01-19",
        "notes": "Test claim",
    }


@pytest.fixture
def sample_source() -> dict:
    """Provide a sample source for testing."""
    return {
        "id": "test-source-001",
        "type": "REPORT",
        "title": "Test Report on AI",
        "author": ["Test Author"],
        "year": 2026,
        "url": "https://example.com/test",
        "doi": None,
        "accessed": "2026-01-19",
        "reliability": 0.8,
        "bias_notes": "Test bias notes",
        "claims_extracted": ["TECH-2026-001"],
        "analysis_file": None,
        "topics": ["ai", "test"],
        "domains": ["TECH"],
        "status": "analyzed",
    }


@pytest.fixture
def sample_chain() -> dict:
    """Provide a sample chain for testing."""
    return {
        "id": "CHAIN-2026-001",
        "name": "Test Chain",
        "thesis": "Test thesis statement",
        "credence": 0.5,
        "claims": ["TECH-2026-001"],
        "analysis_file": None,
        "weakest_link": "TECH-2026-001",
        "scoring_method": "MIN",
    }


@pytest.fixture
def sample_prediction() -> dict:
    """Provide a sample prediction for testing."""
    return {
        "claim_id": "TECH-2026-002",
        "source_id": "test-source-001",
        "date_made": "2026-01-19",
        "target_date": "2027-12-31",
        "falsification_criteria": "Training costs decrease",
        "verification_criteria": "Training costs increase 2x",
        "status": "[P→]",
        "last_evaluated": "2026-01-19",
        "evidence_updates": None,
    }


@pytest.fixture
def sample_yaml_registry(tmp_path: Path) -> Path:
    """Create a sample YAML registry for testing migration."""
    registry_dir = tmp_path / "claims"
    registry_dir.mkdir()

    registry = {
        "counters": {
            "TECH": 2,
            "LABOR": 1,
            "DIST": 1,
            "VALUE": 1,
        },
        "claims": {
            "TECH-2026-001": {
                "text": "AI costs double annually",
                "type": "[F]",
                "domain": "TECH",
                "evidence_level": "E2",
                "confidence": 0.75,
                "source_ids": ["test-source"],
                "first_extracted": "2026-01-19",
                "extracted_by": "test",
                "supports": [],
                "contradicts": [],
                "depends_on": [],
                "modified_by": [],
                "part_of_chain": "",
                "version": 1,
                "last_updated": "2026-01-19",
            },
            "TECH-2026-002": {
                "text": "AI will reach AGI by 2030",
                "type": "[P]",
                "domain": "TECH",
                "evidence_level": "E5",
                "confidence": 0.3,
                "source_ids": ["test-source"],
                "first_extracted": "2026-01-19",
                "extracted_by": "test",
                "supports": [],
                "contradicts": [],
                "depends_on": ["TECH-2026-001"],
                "modified_by": [],
                "part_of_chain": "",
                "version": 1,
                "last_updated": "2026-01-19",
            },
            "DIST-2026-001": {
                "text": "Wealth will concentrate",
                "type": "[T]",
                "domain": "DIST",
                "evidence_level": "E4",
                "confidence": 0.5,
                "source_ids": ["test-source"],
                "first_extracted": "2026-01-19",
                "extracted_by": "test",
                "supports": [],
                "contradicts": [],
                "depends_on": [],
                "modified_by": [],
                "part_of_chain": "",
                "version": 1,
                "last_updated": "2026-01-19",
            },
            "VALUE-2026-001": {
                "text": "Post-labor requires redistribution",
                "type": "[T]",
                "domain": "VALUE",
                "evidence_level": "E3",
                "confidence": 0.7,
                "source_ids": ["test-source"],
                "first_extracted": "2026-01-19",
                "extracted_by": "test",
                "supports": [],
                "contradicts": [],
                "depends_on": [],
                "modified_by": [],
                "part_of_chain": "",
                "version": 1,
                "last_updated": "2026-01-19",
            },
        },
        "chains": {
            "CHAIN-2026-001": {
                "name": "Test Chain",
                "thesis": "Test thesis",
                "confidence": 0.3,
                "claims": ["TECH-2026-001", "TECH-2026-002"],
                "analysis_file": "",
                "weakest_link": "TECH-2026-002",
            },
        },
    }

    with open(registry_dir / "registry.yaml", "w") as f:
        yaml.dump(registry, f)

    return tmp_path


@pytest.fixture
def sample_yaml_sources(sample_yaml_registry: Path) -> Path:
    """Create sample sources.yaml for testing."""
    sources_dir = sample_yaml_registry / "reference"
    sources_dir.mkdir()

    sources = {
        "sources": {
            "test-source": {
                "type": "REPORT",
                "title": "Test Report",
                "author": ["Test Author"],
                "year": 2026,
                "url": "https://example.com",
                "accessed": "2026-01-19",
                "reliability": 0.7,
                "bias_notes": "Test",
                "claims_extracted": ["TECH-2026-001", "TECH-2026-002", "DIST-2026-001", "VALUE-2026-001"],
                "analysis_file": "",
                "topics": ["test"],
                "domains": ["TECH", "DIST", "VALUE"],
            },
        },
    }

    with open(sources_dir / "sources.yaml", "w") as f:
        yaml.dump(sources, f)

    return sample_yaml_registry


@pytest.fixture
def sample_predictions_md(sample_yaml_sources: Path) -> Path:
    """Create sample predictions.md for testing."""
    tracking_dir = sample_yaml_sources / "tracking"
    tracking_dir.mkdir()

    predictions_content = """# Predictions

## Active Predictions

### AGI by 2030
- **Claim ID**: TECH-2026-002
- **Source**: test-source
- **Date Made**: 2026-01-19
- **Target Date**: 2030-12-31
- **Falsification Criteria**: No AGI by 2030
- **Verification Criteria**: AGI achieved
- **Status**: [P→]
- **Last Evaluated**: 2026-01-19
"""

    with open(tracking_dir / "predictions.md", "w") as f:
        f.write(predictions_content)

    return sample_yaml_sources


@pytest.fixture
def sample_analysis_log() -> dict:
    """Provide a sample analysis log for testing."""
    return {
        "id": "ANALYSIS-2026-001",
        "source_id": "test-source-001",
        "analysis_file": "analysis/sources/test-source-001.md",
        "pass": 1,
        "status": "completed",
        "tool": "claude-code",
        "command": "check",
        "model": "claude-sonnet-4",
        "framework_version": "0.1.0",
        "methodology_version": None,
        "started_at": "2026-01-23T10:00:00Z",
        "completed_at": "2026-01-23T10:08:00Z",
        "duration_seconds": 480,
        "tokens_in": 2500,
        "tokens_out": 1200,
        "total_tokens": 3700,
        "cost_usd": 0.08,
        # New delta accounting fields
        "tokens_baseline": 10000,
        "tokens_final": 13700,
        "tokens_check": 3700,
        "usage_provider": "claude",
        "usage_mode": "per_message_sum",
        "usage_session_id": "abc12345-1234-5678-9abc-def012345678",
        # Synthesis linking fields (empty lists, not None, for pyarrow compatibility)
        "inputs_source_ids": [],
        "inputs_analysis_ids": [],
        "stages_json": None,
        "claims_extracted": ["TECH-2026-001"],
        "claims_updated": [],
        "notes": "Initial analysis",
        "git_commit": "abc123",
        "created_at": "2026-01-23T10:09:00Z",
    }


@pytest.fixture
def sample_evidence_link() -> dict:
    """Provide a sample evidence link for testing."""
    return {
        "id": "EVLINK-2026-001",
        "claim_id": "TECH-2026-001",
        "source_id": "test-source-001",
        "direction": "supports",
        "status": "active",
        "supersedes_id": None,
        "strength": 0.8,
        "location": "Table 3, p.15",
        "quote": "The study found that AI training costs double annually",
        "reasoning": "Direct measurement of training costs supports the claim",
        "analysis_log_id": None,
        "created_at": "2026-01-30T10:00:00Z",
        "created_by": "claude-code",
    }


@pytest.fixture
def sample_reasoning_trail() -> dict:
    """Provide a sample reasoning trail for testing."""
    return {
        "id": "REASON-2026-001",
        "claim_id": "TECH-2026-001",
        "status": "active",
        "supersedes_id": None,
        "credence_at_time": 0.75,
        "evidence_level_at_time": "E2",
        "evidence_summary": "E2 based on 2 supporting sources, 1 weak counter",
        "supporting_evidence": ["EVLINK-2026-001"],
        "contradicting_evidence": [],
        "assumptions_made": ["Current paradigm continues"],
        "counterarguments_json": json.dumps([
            {
                "text": "Study X found opposite result",
                "response": "Study X used different methodology; not directly comparable",
                "disposition": "discounted"
            }
        ]),
        "reasoning_text": "Assigned 0.75 credence because:\n1. Two independent studies support the core mechanism\n2. One contradicting study exists but uses incompatible methodology\n3. No direct replication yet (prevents E1)",
        "analysis_pass": 1,
        "analysis_log_id": None,
        "created_at": "2026-01-30T10:00:00Z",
        "created_by": "claude-code",
    }
