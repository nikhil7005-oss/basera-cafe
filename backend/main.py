import json
import os
from pathlib import Path

import razorpay
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

MENU_DATA_FILE = BASE_DIR / "backend" / "menu_data.json"
DEFAULT_MENU = [
    {"id": 1, "name": "Matcha Latte", "price": 4.50, "emoji": "🍵", "image": "", "category": "Beverages"},
    {"id": 2, "name": "Cold Brew", "price": 3.00, "emoji": "🧊", "image": "", "category": "Beverages"},
    {"id": 3, "name": "Avocado Toast", "price": 8.00, "emoji": "🥑", "image": "", "category": "Starters"},
    {"id": 4, "name": "Acai Bowl", "price": 9.50, "emoji": "🥣", "image": "", "category": "Desserts"}
]
DEFAULT_CATEGORIES = ["Starters", "Main Course", "Beverages", "Desserts", "Others"]

app = FastAPI(title="Baseraa API", version="1.0.0")


def ensure_menu_store() -> dict:
    MENU_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MENU_DATA_FILE.exists():
        payload = {"menu": DEFAULT_MENU, "categories": DEFAULT_CATEGORIES}
        MENU_DATA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    try:
        payload = json.loads(MENU_DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        payload = {"menu": DEFAULT_MENU, "categories": DEFAULT_CATEGORIES}
        MENU_DATA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    payload.setdefault("menu", DEFAULT_MENU)
    payload.setdefault("categories", DEFAULT_CATEGORIES)
    return payload


def get_allowed_origins() -> list[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080"
    )
    return [
        value.strip()
        for value in raw.split(",")
        if value.strip() and "*" not in value.strip()
    ]


def get_allowed_origin_regex() -> str | None:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    for value in raw.split(","):
        clean = value.strip()
        if "*" in clean:
            pattern = clean.replace(".", "\\.").replace("*", ".*")
            return rf"^{pattern}$"
    return None


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=get_allowed_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


class OrderRequest(BaseModel):
    amount: float


class MenuPayload(BaseModel):
    menu: list[dict]
    categories: list[str]


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "basera-cafe-api"}


@app.get("/menu")
def get_menu():
    return ensure_menu_store()


@app.post("/menu")
def save_menu(payload: MenuPayload):
    menu_state = {
        "menu": payload.menu,
        "categories": payload.categories,
    }
    MENU_DATA_FILE.write_text(json.dumps(menu_state, indent=2), encoding="utf-8")
    return menu_state


@app.post("/create-order")
def create_order(order: OrderRequest):
    if client is None:
        raise HTTPException(status_code=500, detail="Razorpay keys are not configured.")

    payment_data = {
        "amount": int(order.amount * 100),
        "currency": "INR",
        "receipt": f"receipt_{os.urandom(4).hex()}"
    }

    try:
        razorpay_order = client.order.create(data=payment_data)
        return {"order_id": razorpay_order["id"]}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to create Razorpay order: {str(exc)}") from exc
