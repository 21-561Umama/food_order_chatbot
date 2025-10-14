# backend/chatbot.py
import json
import subprocess
import re
import difflib

# ---------------- Menu (local, authoritative prices) ----------------
MENU = {
    "Cheeseburger": {"small": 4.49, "medium": 6.49, "large": 8.49},
    "Margherita Pizza": {"small": 5.99, "medium": 7.99, "large": 9.99},
    "Veggie Wrap": {"small": 3.99, "medium": 5.99, "large": 7.49},
    "Caesar Salad": {"small": 4.99, "medium": 6.99, "large": 8.99},
    "Chicken Tacos": {"small": 4.49, "medium": 6.49, "large": 8.49},
    "Pasta Alfredo": {"small": 6.49, "medium": 8.49, "large": 10.49},
    "Grilled Salmon": {"small": 7.99, "medium": 10.99, "large": 13.99},
    "BBQ Ribs": {"small": 8.99, "medium": 12.99, "large": 15.99},
    "Fried Rice": {"small": 4.99, "medium": 6.99, "large": 8.99},
    "Chocolate Cake": {"small": 2.99, "medium": 4.99, "large": 6.99},
}

# ---------------- Utilities ----------------
def format_menu():
    lines = []
    for dish, sizes in MENU.items():
        lines.append(f"{dish}: " + ", ".join([f"{sz} ${pr:.2f}" for sz, pr in sizes.items()]))
    return "\n\n".join(lines)

def view_cart_text(session):
    if not session["cart"]:
        return "Your cart is empty."
    lines = []
    total = 0.0
    for i, c in enumerate(session["cart"], start=1):
        lt = c["qty"] * c["price"]
        total += lt
        lines.append(f"{i}. {c['qty']} x {c['size']} {c['item']} -> ${lt:.2f}")
    lines.append(f"TOTAL: ${total:.2f}")
    return "\n".join(lines)

def add_to_cart(session, item, size, qty):
    # normalize inputs
    if not item:
        return False, "No item provided."
    item = item.title()
    size = (size or "").lower()
    if item not in MENU:
        return False, f"'{item}' is not on the menu."
    if size not in MENU[item]:
        return False, f"Invalid size '{size}'. Choose small, medium, or large."
    try:
        qty = int(qty)
        if qty <= 0:
            return False, "Quantity must be 1 or greater."
    except Exception:
        return False, "Invalid quantity."
    price = MENU[item][size]
    session["cart"].append({"item": item, "size": size, "qty": qty, "price": price})
    return True, f"Added {qty} x {size} {item}."

def remove_from_cart(session, index):
    # index is 1-based in messages
    try:
        idx = int(index) - 1
        if idx < 0 or idx >= len(session["cart"]):
            return False, "Invalid item number to remove."
        removed = session["cart"].pop(idx)
        return True, f"Removed {removed['qty']} x {removed['size']} {removed['item']}."
    except Exception:
        return False, "Failed to remove item. Provide the item number from the cart."

def update_cart(session, index=None, item_name=None, new_size=None, new_qty=None):
    try:
        idx = -1
        if index is not None:
            idx = int(index) - 1
        elif item_name is not None:
            cart_item_names = [item["item"].lower() for item in session["cart"]]
            matches = difflib.get_close_matches(item_name.lower(), cart_item_names, n=1, cutoff=0.6)
            if matches:
                for i, item in enumerate(session["cart"]):
                    if item["item"].lower() == matches[0]:
                        idx = i
                        break
        
        if idx < 0 or idx >= len(session["cart"]):
            return False, "Invalid item to update."

        entry = session["cart"][idx]
        if new_size:
            if new_size not in MENU[entry["item"]]:
                return False, f"Invalid size '{new_size}'."
            entry["size"] = new_size
            entry["price"] = MENU[entry["item"]][new_size]
        if new_qty is not None:
            q = int(new_qty)
            if q <= 0:
                return False, "Quantity must be 1 or greater."
            entry["qty"] = q
        return True, f"Updated item {idx + 1}."
    except Exception:
        return False, "Failed to update. Check item, size, and quantity."

def clear_cart(session):
    session["cart"].clear()
    return "Cart cleared."

# ---------------- Gemini CLI parser with fallback ----------------
def parse_with_gemini(text):
    """
    Try to parse using gemini CLI to strict JSON:
    {"action":"add/remove/show/menu/checkout/name/address/update/clear", "item": "...", "size":"small", "qty":1, "index":1, "name":"...", "address":"..."}
    If gemini CLI is missing or fails, use a heuristic fallback parser.
    """
    # Strict prompt for Gemini (if available)
    prompt = (
        "Parse the user message into JSON with these keys (only return valid JSON):\n"
        "action: one of [add, remove, show, menu, checkout, name, address, update, clear]\n"
        "item: item name (string) if applicable\n"
        "size: small|medium|large if applicable\n"
        "qty: integer if applicable\n"
        "index: integer (1-based) for cart item references if applicable\n"
        "name: user's name if user provided\n"
        "address: delivery/pickup address if user provided\n\n"
        f"Message: \"{text}\"\n\nReturn only JSON."
    )
    cmd = ["gemini", "-p", prompt, "--output-format", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        # Try to extract candidate content (Gemini CLI formats vary)
        if isinstance(data, dict) and "candidates" in data and data["candidates"]:
            content = data["candidates"][0].get("content", "")
            return json.loads(content)
        # otherwise assume data is already the JSON we need
        return data
    except Exception:
        # fallback heuristic parser (very simple)
        tx = text.lower().strip()

        # direct commands
        if "menu" in tx:
            return {"action": "menu"}
        if "cart" in tx or "show cart" in tx or "view cart" in tx:
            return {"action": "show"}
        if "clear cart" in tx or (tx == "clear" and "cart" in tx):
            return {"action": "clear"}
        if "checkout" in tx:
            return {"action": "checkout"}
        # name or address
        mname = re.search(r"(my name is|i am|this is)\s+([A-Za-z ,.'-]+)", text, re.IGNORECASE)
        if mname:
            name = mname.group(2).strip()
            return {"action": "name", "name": name}
        maddr = re.search(r"(address[:\-]?\s*|deliver to|my address is)\s*(.+)", text, re.IGNORECASE)
        if maddr:
            addr = maddr.group(2).strip()
            return {"action": "address", "address": addr}

        # remove item by number: "remove 2" or "remove item 2"
        mrem = re.search(r"remove(?: item)?\s+(\d+)", tx)
        if mrem:
            return {"action": "remove", "index": int(mrem.group(1))}

        # update item: "update 2 size large" or "change item 1 to large"
        mup = re.search(r"(?:update|change)\s+(\d+)(?:\s+to\s+)?\s*(small|medium|large)?(?:\s+qty\s+(\d+))?", tx)
        if mup:
            idx = int(mup.group(1))
            size = mup.group(2)
            qty = mup.group(3)
            res = {"action": "update", "index": idx}
            if size:
                res["size"] = size
            if qty:
                res["qty"] = int(qty)
            return res

        mup_by_name = re.search(r"(?:update|change)\s+(.+?)\s+to\s+(small|medium|large)", tx)
        if mup_by_name:
            item_name = mup_by_name.group(1).strip()
            size = mup_by_name.group(2).strip()
            return {"action": "update", "item_name": item_name, "size": size}

        # add pattern: "I want 2 medium cheeseburgers" or "add 1 small cheeseburger"
        madd = re.search(r"(?:\badd\b|get me|i want|i'd like|i want to order|order)\s*(?:a|an|the)?\s*(\d+|a|an)?\s*(small|medium|large)?\s*([a-zA-Z\s]+)", tx)
        if madd:
            qty_str = madd.group(1)
            if qty_str in ["a", "an"]:
                qty = 1
            elif qty_str:
                qty = int(qty_str)
            else:
                qty = 1
            size = madd.group(2) or "medium"
            item = madd.group(3).strip().title()
            if item not in MENU and item.endswith('s'):
                singular_item = item.rstrip('s')
                if singular_item in MENU:
                    item = singular_item
            return {"action": "add", "item": item, "size": size, "qty": qty}

        # check if the message is a menu item
        for item_name in MENU:
            if tx == item_name.lower():
                return {"action": "add", "item": item_name, "size": "medium", "qty": 1}

        # fallback unknown
        return {"action": "unknown", "raw": text}
