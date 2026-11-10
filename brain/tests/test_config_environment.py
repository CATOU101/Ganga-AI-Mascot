"""Tests for automatic project-root environment loading."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pytest

from brain.config import BrainConfig


def _run_config_import(
    project_root,
    working_directory,
    *,
    expected_provider,
    expected_key,
    expected_model,
    expected_top_k,
    expected_router_key="dotenv-router-key",
    expected_order=("groq", "openrouter"),
    expected_router_model="nvidia/nemotron-3.5-super-vl:free",
    overrides=None,
):
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(project_root),
        "PYTHONNOUSERSITE": "1",
    }
    env.update(overrides or {})
    check = (
        "from brain.config import BrainConfig, ENV_FILE, ROOT; "
        "assert ENV_FILE == ROOT / '.env'; "
        "cfg = BrainConfig(); "
        f"assert cfg.llm_provider == {expected_provider!r}; "
        f"assert cfg.llm_model == {expected_model!r}; "
        f"assert cfg.top_k == {expected_top_k}; "
        f"assert cfg.llm_provider_order == {expected_order!r}; "
        f"import os; assert os.environ.get('GROQ_API_KEY', '') == {expected_key!r}; "
        f"assert os.environ.get('OPENROUTER_API_KEY', '') == {expected_router_key!r}"
    )

    subprocess.run(
        [sys.executable, "-c", check],
        cwd=working_directory,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _make_project_fixture(tmp_path):
    project_root = tmp_path / "project"
    brain_package = project_root / "brain"
    brain_package.mkdir(parents=True)
    (brain_package / "__init__.py").write_text("")
    source_config = os.path.join(os.path.dirname(__file__), "..", "config.py")
    shutil.copyfile(source_config, brain_package / "config.py")
    (project_root / ".env").write_text(
        "LLM_PROVIDER=extractive\n"
        "GROQ_API_KEY=dotenv-test-key\n"
        "GROQ_MODEL=dotenv-test-model\n"
        "OPENROUTER_API_KEY=dotenv-router-key\n"
        "OPENROUTER_MODEL=nvidia/nemotron-3.5-super-vl:free\n"
        "LLM_PROVIDER_ORDER=groq, openrouter,groq\n"
        "GANGA_BRAIN_TOP_K=7\n"
    )
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    return project_root, outside


def test_import_automatically_loads_project_root_env_outside_working_directory(tmp_path):
    project_root, outside = _make_project_fixture(tmp_path)

    _run_config_import(
        project_root,
        outside,
        expected_provider="extractive",
        expected_key="dotenv-test-key",
        expected_model="dotenv-test-model",
        expected_top_k=7,
    )


def test_import_preserves_explicit_environment_values_over_project_env(tmp_path):
    project_root, outside = _make_project_fixture(tmp_path)
    overrides = {
        "LLM_PROVIDER": "groq",
        "GROQ_API_KEY": "process-test-key",
        "GROQ_MODEL": "process-test-model",
        "GANGA_BRAIN_TOP_K": "9",
    }

    _run_config_import(
        project_root,
        outside,
        expected_provider="groq",
        expected_key="process-test-key",
        expected_model="process-test-model",
        expected_top_k=9,
        overrides=overrides,
    )


def test_openrouter_can_be_primary_and_selects_its_independent_model(tmp_path):
    project_root, outside = _make_project_fixture(tmp_path)
    (project_root / ".env").write_text(
        "LLM_PROVIDER=openrouter\n"
        "LLM_PROVIDER_ORDER=openrouter,groq\n"
        "OPENROUTER_API_KEY=router-test-key\n"
        "OPENROUTER_MODEL=nvidia/nemotron-3.5-super-vl:free\n"
        "GROQ_MODEL=groq-stays-independent\n"
    )
    _run_config_import(
        project_root,
        outside,
        expected_provider="openrouter",
        expected_key="",
        expected_router_key="router-test-key",
        expected_model="nvidia/nemotron-3.5-super-vl:free",
        expected_top_k=5,
        expected_order=("openrouter", "groq"),
    )


def test_empty_order_uses_default_and_duplicates_are_removed(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_PROVIDER_ORDER", " , groq, openrouter, groq,, ")
    assert BrainConfig().llm_provider_order == ("groq", "openrouter")

    monkeypatch.setenv("LLM_PROVIDER_ORDER", " , , ")
    assert BrainConfig().llm_provider_order == ("groq", "openrouter")


def test_unsupported_order_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "groq,unknown")
    with pytest.raises(ValueError, match="Unsupported hosted LLM provider"):
        BrainConfig()
