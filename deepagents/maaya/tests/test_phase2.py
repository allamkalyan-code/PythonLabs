"""Phase 2 tests — agent wiring, YAML config, WebSocket streaming.

Run with:  uv run pytest tests/test_phase2.py -v
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the maaya/ root is on sys.path so imports work from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    """Ensure ANTHROPIC_API_KEY is always set so no test fails on missing key."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-for-unit-tests")


# ── 1. subagents.yaml ────────────────────────────────────────────────────────

class TestSubagentsYaml:
    """Validate the subagents.yaml file is valid and well-structured."""

    def _load(self):
        import yaml
        path = Path(__file__).parent.parent / "agents" / "subagents.yaml"
        with open(path) as f:
            return yaml.safe_load(f)

    def test_yaml_parses_without_error(self):
        data = self._load()
        assert isinstance(data, dict)

    def test_subagents_key_exists(self):
        data = self._load()
        assert "subagents" in data, "YAML must have a top-level 'subagents' key"

    def test_all_required_subagents_present(self):
        data = self._load()
        names = {s["name"] for s in data["subagents"]}
        required = {"spec-evaluator", "planner", "architect", "frontend",
                    "backend", "database", "devops", "tester"}
        assert required == names, f"Missing subagents: {required - names}"

    def test_each_subagent_has_required_fields(self):
        data = self._load()
        for subagent in data["subagents"]:
            name = subagent.get("name", "<unnamed>")
            assert "name" in subagent, f"{name}: missing 'name'"
            assert "description" in subagent, f"{name}: missing 'description'"
            assert "system_prompt" in subagent, f"{name}: missing 'system_prompt'"
            assert "tier" in subagent, f"{name}: missing 'tier'"

    def test_all_tiers_are_valid(self):
        import yaml
        from agents.model_config import get_model
        data = self._load()
        for subagent in data["subagents"]:
            tier = subagent["tier"]
            # get_model raises ValueError for unknown tiers
            model = get_model(tier)
            assert model.startswith("anthropic:"), \
                f"{subagent['name']}: tier '{tier}' resolved to unexpected model '{model}'"

    def test_spec_evaluator_system_prompt_contains_spec_complete(self):
        data = self._load()
        se = next(s for s in data["subagents"] if s["name"] == "spec-evaluator")
        assert "SPEC_COMPLETE" in se["system_prompt"]
        assert "NEEDS_CLARIFICATION" in se["system_prompt"]


# ── 2. model_config ──────────────────────────────────────────────────────────

class TestModelConfig:
    def test_get_model_fast(self):
        from agents.model_config import get_model
        assert "haiku" in get_model("fast")

    def test_get_model_balanced(self):
        from agents.model_config import get_model
        assert "sonnet" in get_model("balanced")

    def test_get_model_powerful(self):
        from agents.model_config import get_model
        assert "opus" in get_model("powerful")

    def test_get_model_unknown_raises(self):
        from agents.model_config import get_model
        with pytest.raises(ValueError, match="Unknown model tier"):
            get_model("nonexistent")

    def test_get_max_tokens_returns_int(self):
        from agents.model_config import get_max_tokens
        for tier in ("fast", "balanced", "powerful"):
            tokens = get_max_tokens(tier)
            assert isinstance(tokens, int) and tokens > 0


# ── 3. tracker_tools ─────────────────────────────────────────────────────────

class TestTrackerTools:
    def test_all_tracker_tools_exported(self):
        from agents.tracker_tools import ALL_TRACKER_TOOLS
        assert len(ALL_TRACKER_TOOLS) == 11

    def test_all_tools_are_langchain_tools(self):
        from langchain_core.tools import BaseTool
        from agents.tracker_tools import ALL_TRACKER_TOOLS
        for tool in ALL_TRACKER_TOOLS:
            assert isinstance(tool, BaseTool), f"{tool} is not a BaseTool"

    def test_tools_have_descriptions(self):
        from agents.tracker_tools import ALL_TRACKER_TOOLS
        for tool in ALL_TRACKER_TOOLS:
            assert tool.description, f"Tool '{tool.name}' has no description"

    def test_get_project_id_raises_when_not_set(self):
        from agents import tracker_tools
        tracker_tools._current_project_id = None
        with pytest.raises(RuntimeError, match="No project set"):
            tracker_tools._get_project_id()

    def test_set_current_project(self):
        from agents.tracker_tools import set_current_project, _get_project_id
        set_current_project(42)
        assert _get_project_id() == 42

    def test_create_epic_returns_error_when_db_fails(self):
        """create_epic should return an error string, not raise, on DB failure."""
        from agents.tracker_tools import create_epic, set_current_project
        set_current_project(9999)  # non-existent project
        # DB will likely fail with FK violation; tool must catch and return error string
        result = create_epic.invoke({
            "title": "Test Epic",
            "description": "Test",
            "priority": "medium",
            "success_criteria": "",
        })
        # Should be a string (either success or error message)
        assert isinstance(result, str)


# ── 4. handoff parser ────────────────────────────────────────────────────────

class TestHandoffParser:
    def _parse(self, text):
        from server.routers.agent import _parse_handoff
        return _parse_handoff(text)

    def test_returns_none_when_no_block(self):
        assert self._parse("Some random text") is None

    def test_parses_status(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Spec is complete.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Proceed to planning.
---END HANDOFF---
""")
        assert result is not None
        assert result["status"] == "DONE"

    def test_parses_files_created(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Created files.
FILES_CREATED: src/app.py, src/models.py
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Done.
---END HANDOFF---
""")
        assert result["files_created"] == ["src/app.py", "src/models.py"]

    def test_parses_tests_written_yes(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Tests written.
FILES_CREATED: tests/test_app.py
FILES_MODIFIED: NONE
TESTS_WRITTEN: YES - tests/test_app.py
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Run tests.
---END HANDOFF---
""")
        assert result["tests_written"] is True

    def test_parses_tests_written_no(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: No tests.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Done.
---END HANDOFF---
""")
        assert result["tests_written"] is False

    def test_parses_flags(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Done with flags.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: Missing env var, DB not migrated
NEXT_SUGGESTED: Check flags.
---END HANDOFF---
""")
        assert len(result["flags"]) == 2

    def test_flags_none_returns_empty_list(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Clean.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Done.
---END HANDOFF---
""")
        assert result["flags"] == []

    def test_blocked_status_parsed(self):
        result = self._parse("""
---HANDOFF---
STATUS: BLOCKED
SUMMARY: Cannot find the database migration file.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: User must create migration manually.
---END HANDOFF---
""")
        assert result["status"] == "BLOCKED"

    def test_case_insensitive_delimiter(self):
        result = self._parse("""
---handoff---
STATUS: done
SUMMARY: Works.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: no
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Done.
---end handoff---
""")
        assert result is not None
        assert result["status"] == "DONE"


# ── 5. cost estimator ────────────────────────────────────────────────────────

class TestCostEstimator:
    def _cost(self, model, inp, out):
        from server.routers.agent import _estimate_cost
        return _estimate_cost(model, inp, out)

    def test_haiku_cheaper_than_sonnet(self):
        haiku = self._cost("anthropic:claude-haiku-4-5-20251001", 10000, 2000)
        sonnet = self._cost("anthropic:claude-sonnet-4-6", 10000, 2000)
        assert haiku < sonnet

    def test_sonnet_cheaper_than_opus(self):
        sonnet = self._cost("anthropic:claude-sonnet-4-6", 10000, 2000)
        opus = self._cost("anthropic:claude-opus-4-6", 10000, 2000)
        assert sonnet < opus

    def test_zero_tokens_returns_zero(self):
        assert self._cost("anthropic:claude-sonnet-4-6", 0, 0) == 0.0

    def test_none_model_uses_sonnet_rates(self):
        cost_none = self._cost(None, 10000, 2000)
        cost_sonnet = self._cost("anthropic:claude-sonnet-4-6", 10000, 2000)
        assert cost_none == cost_sonnet


# ── 6. environment / startup ─────────────────────────────────────────────────

class TestEnvironment:
    def test_dotenv_file_exists(self):
        env_path = Path(__file__).parent.parent / ".env"
        assert env_path.exists(), ".env file must exist in maaya/"

    def test_env_example_exists(self):
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example must exist for documentation"

    def test_api_key_loads_from_env(self, tmp_path, monkeypatch):
        """Verify load_dotenv picks up ANTHROPIC_API_KEY from a .env file."""
        from dotenv import load_dotenv
        env_file = tmp_path / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=sk-ant-test-xyz\n")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        load_dotenv(env_file)
        assert os.getenv("ANTHROPIC_API_KEY") == "sk-ant-test-xyz"

    def test_agents_md_exists(self):
        agents_md = Path(__file__).parent.parent / "AGENTS.md"
        assert agents_md.exists(), "AGENTS.md must exist in maaya/"

    def test_agents_md_contains_required_sections(self):
        agents_md = Path(__file__).parent.parent / "AGENTS.md"
        content = agents_md.read_text()
        for section in ("spec-evaluator", "SPEC_COMPLETE", "HANDOFF", "Definition of Done"):
            assert section in content, f"AGENTS.md missing section: {section}"


# ── 7. FastAPI app ────────────────────────────────────────────────────────────

class TestFastAPIApp:
    @pytest.fixture
    def client(self, tmp_path):
        """TestClient backed by an isolated in-memory SQLite DB so tests never
        pollute maaya.db."""
        import os
        from fastapi.testclient import TestClient

        # Point DATABASE_URL at a temp file for the duration of this test
        db_path = tmp_path / "test.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        # Re-import engine/models with the new URL
        import importlib
        import server.database as db_mod
        import server.models as models_mod

        db_mod.DATABASE_URL = f"sqlite:///{db_path}"
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        db_mod.engine = create_engine(db_mod.DATABASE_URL, connect_args={"check_same_thread": False})
        db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_mod.engine)
        db_mod.Base.metadata.create_all(bind=db_mod.engine)

        from server.main import app
        with TestClient(app) as c:
            yield c

        os.environ.pop("DATABASE_URL", None)

    def test_projects_list_returns_200(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_project_returns_201(self, client, tmp_path):
        resp = client.post("/api/projects", json={
            "name": "test-project",
            "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-project"
        assert "id" in data

    def test_get_nonexistent_project_returns_404(self, client):
        resp = client.get("/api/projects/99999")
        assert resp.status_code == 404

    def test_delete_project_returns_204(self, client, tmp_path):
        # Create first
        create = client.post("/api/projects", json={
            "name": "delete-me",
            "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        project_id = create.json()["id"]
        # Then delete
        resp = client.delete(f"/api/projects/{project_id}")
        assert resp.status_code == 204
        # Verify gone
        resp2 = client.get(f"/api/projects/{project_id}")
        assert resp2.status_code == 404

    def test_tracker_returns_empty_for_new_project(self, client, tmp_path):
        create = client.post("/api/projects", json={
            "name": "tracker-test",
            "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        project_id = create.json()["id"]
        resp = client.get(f"/api/projects/{project_id}/tracker")
        assert resp.status_code == 200
        assert resp.json()["epics"] == []

    def test_reset_session_returns_200(self, client, tmp_path):
        create = client.post("/api/projects", json={
            "name": "reset-test",
            "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        project_id = create.json()["id"]
        resp = client.post(f"/api/projects/{project_id}/reset-session")
        assert resp.status_code == 204
