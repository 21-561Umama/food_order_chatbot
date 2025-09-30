import json
import subprocess

#  Menu Data 
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

# ---------------- Cart & User Details ----------------
cart = []
user_details = {"name": None, "delivery": None}

# ---------------- Functions ----------------
def show_menu():
    print("\n=== FOOD MENU ===")
    for dish, sizes in MENU.items():
        print(f"{dish}:")
        for size, price in sizes.items():
            print(f"  - {size.capitalize()}: ${price:.2f}")
        print()

def add_to_cart(item, size, qty):
    if item not in MENU:
        print("❌ That dish is not on the menu.")
        return
    if size not in MENU[item]:
        print("❌ Invalid size. Choose small, medium, or large.")
        return
    cart.append({"item": item, "size": size, "qty": qty, "price": MENU[item][size]})
    print(f"✅ Added {qty} {size} {item}(s) to your cart.")

def view_cart():
    if not cart:
        print("🛒 Your cart is empty.")
        return
    print("\n--- Your Cart ---")
    total = 0
    for i, c in enumerate(cart, start=1):
        line_total = c["qty"] * c["price"]
        total += line_total
        print(f"{i}. {c['qty']} x {c['size'].capitalize()} {c['item']} → ${line_total:.2f}")
    print(f"TOTAL: ${total:.2f}")

def checkout():
    if not cart:
        print("🛑 Your cart is empty. Add items first!")
        return
    if not user_details["name"]:
        user_details["name"] = input("Enter your name: ").strip()
    if not user_details["delivery"]:
        user_details["delivery"] = input("Enter pickup/delivery address: ").strip()
    print("\n--- ORDER SUMMARY ---")
    view_cart()
    print(f"Name: {user_details['name']}")
    print(f"Pickup/Delivery: {user_details['delivery']}")
    confirm = input("Confirm order? (yes/no): ").strip().lower()
    if confirm == "yes":
        print("🎉 Order confirmed! Thank you!")
        cart.clear()
    else:
        print("❌ Order cancelled.")

# ---------------- Gemini CLI Parsing ----------------
def parse_user_input(text):
    """
    Uses Gemini CLI to parse user input into JSON with keys:
    action, item, size, qty
    """
    prompt = f"Parse this food order into JSON with keys action, item, size, qty: '{text}'"
    cmd = ["gemini", "-p", prompt, "--output-format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data
    except Exception as e:
        print("❌ Could not parse input:", e)
        return None

# ---------------- Main Chatbot Loop ----------------
def chatbot():
    print("🍔 Welcome to the Food Order Chatbot!")
    show_menu()
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "menu":
            show_menu()
        elif user_input.lower() == "cart":
            view_cart()
        elif user_input.lower() == "checkout":
            checkout()
        elif user_input.lower() in ["quit", "exit"]:
            print("👋 Goodbye!")
            break
        else:
            parsed = parse_user_input(user_input)
            if parsed and parsed.get("action") == "add":
                add_to_cart(parsed.get("item"), parsed.get("size"), parsed.get("qty"))
            else:
                print("❓ I didn’t understand that. Try 'menu', 'cart', or 'checkout'.")

if __name__ == "__main__":
    chatbot()
