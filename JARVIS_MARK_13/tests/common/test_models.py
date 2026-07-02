"""
tests/common/test_models.py

Unit tests for model scanning, configuration management, and FastAPI route outputs.
"""

from fastapi.testclient import TestClient
from aether.web_main import app
from aether.models.scanner import scan_gguf_models, get_gguf_dir
from aether.models.manager import load_models_config

client = TestClient(app)

def test_gguf_scanner_and_dir():
    """Verifies that GGUF scanning executes without error and returns list structure."""
    gguf_dir = get_gguf_dir()
    assert gguf_dir.exists()
    
    models = scan_gguf_models()
    assert isinstance(models, list)
    for m in models:
        assert "name" in m
        assert "path" in m
        assert m["name"].endswith(".gguf")

def test_load_models_config():
    """Verifies loading config yields router and planner strings."""
    cfg = load_models_config()
    assert "router_model" in cfg
    assert "planner_model" in cfg
    assert isinstance(cfg["router_model"], str)
    assert isinstance(cfg["planner_model"], str)

def test_get_models_api():
    """Tests GET /api/models REST endpoint structure."""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "router_model" in data
    assert "planner_model" in data
    assert "available_models" in data
    assert isinstance(data["available_models"], list)

def test_refresh_models_api():
    """Tests POST /api/models/refresh REST endpoint structure."""
    response = client.post("/api/models/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "router_model" in data
    assert "available_models" in data
