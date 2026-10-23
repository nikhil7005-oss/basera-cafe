from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


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
