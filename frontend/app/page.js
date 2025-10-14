'use client';
import { useState, useEffect, useRef } from 'react';



export default function Home() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! Welcome to Food Order Chatbot 🍔. What would you like to order?' },
  ]);
  const [input, setInput] = useState('');
  const [menu, setMenu] = useState({});
  const [cart, setCart] = useState([]);
  const session_id = useRef(null);

  useEffect(() => {
    let sid = localStorage.getItem('session_id');
    if (!sid) {
      sid = `${Date.now()}-${Math.random().toString(36).substring(2)}`;
      localStorage.setItem('session_id', sid);
    }
    session_id.current = sid;

    fetchCart();
  }, []);

  const fetchCart = async () => {
    if (!session_id.current) return;
    try {
      const res = await fetch('http://localhost:8001/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'cart', session_id: session_id.current }),
      });
      const data = await res.json();
      const cartItems = data.reply.split('\n').slice(0, -1).map(line => {
        const match = line.match(/\d+\. (\d+) x (\w+) (.*) -> \$(\d+\.\d+)/);
        if (!match) return null;
        return {
          qty: parseInt(match[1]),
          size: match[2],
          item: match[3],
          price: parseFloat(match[4]),
        };
      }).filter(Boolean);
      setCart(cartItems);
    } catch (error) {
      console.error("Could not fetch cart:", error);
    }
  };

  const sendMessage = async (message) => {
    const text = message || input;
    if (!text.trim()) return;

    const newMessages = [...messages, { role: 'user', text }];
    setMessages(newMessages);

    try {
      const res = await fetch('http://localhost:8001/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: session_id.current }),
      });
      const data = await res.json();

      setMessages([...newMessages, { role: 'bot', text: data.reply }]);
      fetchCart();
    } catch (error) {
      setMessages([...newMessages, { role: 'bot', text: '⚠️ Error: could not reach server' }]);
    }

    if (!message) {
      setInput('');
    }
  };

  const addToCart = (item, size) => {
    const message = `add 1 ${size} ${item}`;
    sendMessage(message);
  };

  const removeFromCart = (index) => {
    const message = `remove ${index}`;
    sendMessage(message);
  };

  return (
    <main className="flex flex-row items-start p-8 gap-8 bg-slate-50 min-h-screen font-sans">
      {/* Chat Section */}
      <div className="w-2/3 flex flex-col space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-6 text-center text-gray-800 hover:text-pink-500">Food Order Chatbot</h1>
          <div className="w-full bg-white border rounded-xl shadow-lg p-4 h-96 overflow-y-auto">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`my-2 p-3 rounded-xl shadow-md max-w-md text-base ${ 
                  msg.role === 'user' ? 'bg-indigo-500 text-white ml-auto' : 'bg-gray-200 text-gray-800'
                }`}
              >
                {msg.text}
              </div>
            ))}
          </div>
          <div className="flex w-full mt-4">
            <input
              className="flex-1 border border-gray-300 rounded-l-xl p-3 text-base focus:ring-2 focus:ring-indigo-400 focus:border-transparent shadow-sm"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()} 
              placeholder="Type to order or chat..."
            />
            <button className="bg-indigo-600 text-white px-6 py-3 rounded-r-xl hover:bg-indigo-700 font-semibold text-base transition-colors duration-200"
              onClick={() => sendMessage()}>
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Cart Section */}
      <div className="w-1/3 flex flex-col space-y-8">
        <div>
          <h2 className="text-3xl font-bold mb-6 text-gray-800 hover:text-pink-500">Your Cart</h2>
          <div className="bg-white p-5 rounded-xl shadow-lg border border-gray-200 min-h-[12rem]">
            {cart.length === 0 ? (
              <p className="text-gray-500 text-center pt-10 text-lg font-medium">Your cart is empty. Start adding some delicious food! 😋</p>
            ) : (
              <div className="space-y-4">
                {cart.map((item, i) => (
                  <div key={i} className="flex justify-between items-center bg-gray-50 p-3 rounded-lg shadow-sm border border-gray-200">
                    <div>
                      <p className="font-bold text-lg text-gray-800">{item.qty} x {item.item} <span className="text-sm font-normal text-gray-600 capitalize">({item.size})</span></p>
                      <p className="text-md text-gray-700 font-semibold">${item.price.toFixed(2)}</p>
                    </div>
                    <button 
                      className="bg-rose-500 text-white font-bold py-1 px-3 rounded-full text-xs hover:bg-rose-600 transition-transform transform hover:scale-105 duration-200"
                      onClick={() => removeFromCart(i + 1)} >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

