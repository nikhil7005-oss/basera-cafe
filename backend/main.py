import os
import razorpay
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your live frontend URL after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

class OrderRequest(BaseModel):
    amount: float

@app.post("/create-order")
def create_order(order: OrderRequest):
    payment_data = {
        "amount": int(order.amount * 100),  # Convert to paise
        "currency": "INR",
        "receipt": f"receipt_{os.urandom(4).hex()}"
    }
    razorpay_order = client.order.create(data=payment_data)
    return {"order_id": razorpay_order["id"]}