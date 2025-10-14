

# backend/tests/test_chatbot.py
import unittest
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot import add_to_cart, remove_from_cart, update_cart, clear_cart, parse_with_gemini

class TestChatbot(unittest.TestCase):

    def test_add_to_cart(self):
        session = {"cart": []}
        ok, msg = add_to_cart(session, "Cheeseburger", "medium", 1)
        self.assertTrue(ok)
        self.assertEqual(len(session["cart"]), 1)
        self.assertEqual(session["cart"][0]["item"], "Cheeseburger")

    def test_remove_from_cart(self):
        session = {"cart": [{"item": "Cheeseburger", "size": "medium", "qty": 1, "price": 6.49}]}
        ok, msg = remove_from_cart(session, 1)
        self.assertTrue(ok)
        self.assertEqual(len(session["cart"]), 0)

    def test_update_cart(self):
        session = {"cart": [{"item": "Cheeseburger", "size": "medium", "qty": 1, "price": 6.49}]}
        ok, msg = update_cart(session, 1, new_qty=2)
        self.assertTrue(ok)
        self.assertEqual(session["cart"][0]["qty"], 2)

        ok, msg = update_cart(session, 1, new_size="large")
        self.assertTrue(ok)
        self.assertEqual(session["cart"][0]["size"], "large")

    def test_clear_cart(self):
        session = {"cart": [{"item": "Cheeseburger", "size": "medium", "qty": 1, "price": 6.49}]}
        clear_cart(session)
        self.assertEqual(len(session["cart"]), 0)

    def test_parse_add_intent(self):
        # Test various "add" phrases
        phrases = [
            "add a large cheeseburger",
            "get me 2 medium pizzas",
            "i want to order a veggie wrap",
            "i'd like a small caesar salad",
            "order 3 large chicken tacos"
        ]
        expected = [
            {"action": "add", "item": "Cheeseburger", "size": "large", "qty": 1},
            {"action": "add", "item": "Pizza", "size": "medium", "qty": 2},
            {"action": "add", "item": "Veggie Wrap", "size": "medium", "qty": 1},
            {"action": "add", "item": "Caesar Salad", "size": "small", "qty": 1},
            {"action": "add", "item": "Chicken Tacos", "size": "large", "qty": 3},
        ]

        for i, phrase in enumerate(phrases):
            with self.subTest(phrase=phrase):
                parsed = parse_with_gemini(phrase)
                # We are only checking item, size and qty, not the full parsed output
                self.assertEqual(parsed.get("action"), expected[i].get("action"))
                self.assertIn(expected[i].get("item"), parsed.get("item"))
                self.assertEqual(parsed.get("size"), expected[i].get("size"))
                self.assertEqual(parsed.get("qty"), expected[i].get("qty"))

if __name__ == '__main__':
    unittest.main()
