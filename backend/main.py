# backend/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
from chatbot import parse_with_gemini, format_menu, add_to_cart, view_cart_text, remove_from_cart, update_cart, clear_cart, MENU
from database import get_session, save_session

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str  # Expect session_id from frontend

@app.get("/menu")
async def get_menu() -> Dict:
    return MENU

@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> Dict:
    session_id = req.session_id
    session = get_session(session_id)
    if not session:
        session = {"cart": [], "name": None, "delivery": None}

    parsed = parse_with_gemini(req.message)
    action = parsed.get("action") if isinstance(parsed, dict) else None

    # MENU
    if action == "menu":
        return {"reply": format_menu()}

    # SHOW CART
    if action in ("show", "cart"):
        return {"reply": view_cart_text(session)}

    # CLEAR CART
    if action == "clear":
        msg = clear_cart(session)
        save_session(session_id, session)
        return {"reply": msg + "\n\n" + view_cart_text(session)}

    # ADD
    if action == "add":
        item = parsed.get("item")
        size = parsed.get("size")
        qty = parsed.get("qty", 1)
        ok, msg = add_to_cart(session, item, size, qty)
        if not ok:
            return {"reply": f"Error: {msg}"}
        save_session(session_id, session)
        return {"reply": msg + "\n\n" + view_cart_text(session)}

    # REMOVE
    if action == "remove":
        idx = parsed.get("index")
        ok, msg = remove_from_cart(session, idx)
        if not ok:
            return {"reply": f"Error: {msg}"}
        save_session(session_id, session)
        return {"reply": msg + "\n\n" + view_cart_text(session)}

    # UPDATE
    if action == "update":
        ok, msg = update_cart(
            session,
            index=parsed.get("index"),
            item_name=parsed.get("item_name"),
            new_size=parsed.get("size"),
            new_qty=parsed.get("qty"),
        )
        if not ok:
            return {"reply": f"Error: {msg}"}
        save_session(session_id, session)
        return {"reply": msg + "\n\n" + view_cart_text(session)}

    # NAME
    if action == "name":
        name = parsed.get("name")
        session["name"] = name
        save_session(session_id, session)
        return {"reply": f"Got it — I’ll use the name: {name}."}

    # ADDRESS
    if action == "address":
        address = parsed.get("address")
        session["delivery"] = address
        save_session(session_id, session)
        return {"reply": f"Got it — delivery/pickup set to: {address}."}

    # CHECKOUT
    if action == "checkout":
        if not session.get("cart"):
            return {"reply": "Your cart is empty. Add items before checkout."}
        if not session.get("name"):
            return {"reply": "Please provide your name before checkout (e.g., 'My name is Alice')."}
        if not session.get("delivery"):
            return {"reply": "Please provide pickup/delivery address before checkout (e.g., 'Address: 123 Street')."}
        summary = view_cart_text(session)
        name = session["name"]
        addr = session["delivery"]
        # Confirm and clear cart
        session["cart"].clear()
        save_session(session_id, session)
        return {"reply": f"Order confirmed for {name} - {addr}\n\n{summary}"}

    if parsed.get("action") == "unknown":
        # check if the message is just a size
        tx = req.message.lower().strip()
        if tx in ["small", "medium", "large"]:
            if session["cart"]:
                last_item_index = len(session["cart"])
                ok, msg = update_cart(session, index=last_item_index, new_size=tx)
                if ok:
                    save_session(session_id, session)
                    return {"reply": msg + "\n\n" + view_cart_text(session)}

    # UNKNOWN
    return {"reply": "Sorry, I didn't understand. Try 'menu', 'cart', 'add 2 medium cheeseburgers', 'remove 1', 'update 1 size large', or 'checkout'."}
