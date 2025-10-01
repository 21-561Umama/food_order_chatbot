// frontend/pages/index.js
import { useState, useRef, useEffect } from "react";

export default function Home() {
  // --- State: messages in the chat, input text, and loading flag
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hi! I’m the Food Order Bot. Try 'menu', 'cart', or 'I want 2 medium cheeseburgers'."
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // --- Ref to keep the chat scrolled to the bottom
  const listRef = useRef(null);

  // Auto-scroll when messages change
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  // Send message to backend and show responses
  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    // Add the user's message immediately (use functional update to avoid stale state)
    setMessages(prev => [...prev, { sender: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data = await res.json();
      const replyText = data.reply ?? "No reply from server.";

      // Append bot reply
      setMessages(prev => [...prev, { sender: "bot", text: replyText }]);
    } catch (err) {
      // Show an error message from the bot so the user sees something
      setMessages(prev => [...prev, { sender: "bot", text: "⚠️ Could not reach backend — make sure it is running." }]);
      console.error("Send message error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Send on Enter key
  const onKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div style={{ maxWidth: 900, margin: "20px auto", fontFamily: "system-ui, sans-serif", padding: 12 }}>
      <h1>Food Order Chatbot</h1>

      {/* Chat messages box */}
      <div
        ref={listRef}
        style={{
          border: "1px solid #e6e6e6",
          padding: 12,
          height: 420,
          overflowY: "auto",
          background: "#fafafa",
          borderRadius: 8
        }}
      >
        {messages.map((m, i) => (
          <div key={i} style={{ display: "flex", justifyContent: m.sender === "user" ? "flex-end" : "flex-start", margin: "8px 0" }}>
            <div style={{
              maxWidth: "75%",
              padding: "8px 12px",
              borderRadius: 10,
              background: m.sender === "user" ? "#dcf8c6" : "#ffffff",
              boxShadow: "0 1px 2px rgba(0,0,0,0.06)"
            }}>
              <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>{m.sender}</div>
              <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Input area */}
      <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type your message..."
          style={{ flex: 1, padding: "10px 12px", borderRadius: 6, border: "1px solid #ccc" }}
        />
        <button onClick={sendMessage} disabled={loading} style={{ padding: "10px 16px", borderRadius: 6 }}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>

      <p style={{ color: "#666", marginTop: 8 }}>
        Tip: Try <kbd>menu</kbd>, <kbd>cart</kbd>, or natural text like <em>"I want 2 medium cheeseburgers"</em>.
      </p>
    </div>
  );
}
