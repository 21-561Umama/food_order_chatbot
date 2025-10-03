# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
from chatbot import parse_with_gemini, format_menu, add_to_cart, view_cart_text, session, remove_from_cart, update_cart, clear_cart

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest) -> Dict:
    parsed = parse_with_gemini(req.message)
    action = parsed.get("action") if isinstance(parsed, dict) else None

    # MENU
    if action == "menu":
        return {"reply": format_menu()}

    # SHOW CART
    if action in ("show", "cart"):
        return {"reply": view_cart_text()}

    # CLEAR CART
    if action == "clear":
        msg = clear_cart()
        return {"reply": msg}

    # ADD
    if action == "add":
        item = parsed.get("item")
        size = parsed.get("size")
        qty = parsed.get("qty", 1)
        ok, msg = add_to_cart(item, size, qty)
        if not ok:
            return {"reply": f"Error: {msg}"}
        return {"reply": msg + "\n\n" + view_cart_text()}

    # REMOVE
    if action == "remove":
        idx = parsed.get("index")
        ok, msg = remove_from_cart(idx)
        if not ok:
            return {"reply": f"Error: {msg}"}
        return {"reply": msg + "\n\n" + view_cart_text()}

    # UPDATE
    if action == "update":
        idx = parsed.get("index")
        new_size = parsed.get("size")
        new_qty = parsed.get("qty")
        ok, msg = update_cart(idx, new_size, new_qty)
        if not ok:
            return {"reply": f"Error: {msg}"}
        return {"reply": msg + "\n\n" + view_cart_text()}

    # NAME
    if action == "name":
        name = parsed.get("name")
        session["name"] = name
        return {"reply": f"Got it — I’ll use the name: {name}."}

    # ADDRESS
    if action == "address":
        address = parsed.get("address")
        session["delivery"] = address
        return {"reply": f"Got it — delivery/pickup set to: {address}."}

    # CHECKOUT
    if action == "checkout":
        if not session.get("cart"):
            return {"reply": "Your cart is empty. Add items before checkout."}
        if not session.get("name"):
            return {"reply": "Please provide your name before checkout (e.g., 'My name is Alice')."}
        if not session.get("delivery"):
            return {"reply": "Please provide pickup/delivery address before checkout (e.g., 'Address: 123 Street')."}
        summary = view_cart_text()
        name = session["name"]
        addr = session["delivery"]
        # Confirm and clear cart
        session["cart"].clear()
        return {"reply": f"Order confirmed for {name} - {addr}\n\n{summary}"}

    # UNKNOWN
    return {"reply": "Sorry, I didn't understand. Try 'menu', 'cart', 'add 2 medium cheeseburgers', 'remove 1', 'update 1 size large', or 'checkout'."}
