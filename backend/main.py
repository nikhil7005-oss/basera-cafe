import os
from pathlib import Path

import razorpay
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Baseraa API", version="1.0.0")


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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "basera-cafe-api"}


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
