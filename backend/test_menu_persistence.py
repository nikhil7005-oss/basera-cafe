import importlib
import os

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_menu_persistence_round_trip():
    payload = {
        "menu": [
            {"id": 1, "name": "Shared Test Dish", "price": 25.5, "emoji": "🧪", "image": "", "category": "Starters"}
        ],
        "categories": ["Starters", "Main Course", "Beverages", "Desserts", "Others"]
    }

    post_response = client.post("/menu", json=payload)
    assert post_response.status_code == 200, post_response.text

    get_response = client.get("/menu")
    assert get_response.status_code == 200, get_response.text
    data = get_response.json()
    assert data["menu"][0]["name"] == "Shared Test Dish"
    assert "Starters" in data["categories"]


def test_menu_store_uses_explicit_storage_path(monkeypatch, tmp_path):
    menu_path = tmp_path / "menu.json"
    monkeypatch.setenv("MENU_DATA_PATH", str(menu_path))
    importlib.reload(main)

    payload = {
        "menu": [
            {"id": 99, "name": "Persisted Dish", "price": 14.75, "emoji": "🍽️", "image": "", "category": "Main Course"}
        ],
        "categories": ["Main Course", "Beverages", "Others"]
    }

    saved = main.save_menu(payload)
    assert saved["menu"][0]["name"] == "Persisted Dish"
    assert menu_path.exists()

    loaded = main.ensure_menu_store()
    assert loaded["menu"][0]["name"] == "Persisted Dish"
    monkeypatch.delenv("MENU_DATA_PATH", raising=False)
    importlib.reload(main)


def test_allowed_origins_include_netlify_domain(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://baseraa-cafe.netlify.app,http://localhost:8080")
    importlib.reload(main)
    assert "https://baseraa-cafe.netlify.app" in main.get_allowed_origins()
    assert main.get_allowed_origin_regex() is not None
