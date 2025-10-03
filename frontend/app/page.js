"use client";
import { useState } from "react";

export default function Home() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! Welcome to Food Order Bot 🍔. What would you like to order?" },
  ]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    // add user message
    const newMessages = [...messages, { role: "user", text: input }];
    setMessages(newMessages);

    // send to backend (FastAPI)
    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();

      // add bot reply
      setMessages([...newMessages, { role: "bot", text: data.reply }]);
    } catch (error) {
      setMessages([...newMessages, { role: "bot", text: "⚠️ Error: could not reach server" }]);
    }

    setInput("");
  };

  return (
    <main className="flex flex-col items-center p-6">
      <h1 className="text-2xl font-bold mb-4">Food Order Chatbot</h1>

      <div className="w-full max-w-md border rounded p-4 h-96 overflow-y-auto bg-white">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`my-2 p-2 rounded ${
              msg.role === "user" ? "bg-blue-100 text-right" : "bg-gray-100 text-left"
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div className="flex w-full max-w-md mt-4">
        <input
          className="flex-1 border rounded-l p-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message..."
        />
        <button className="bg-blue-500 text-white px-4 rounded-r" onClick={sendMessage}>
          Send
        </button>
      </div>
    </main>
  );
}
