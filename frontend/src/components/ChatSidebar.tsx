import { useState, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';

export default function ChatSidebar() {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput('');
    await sendMessage(text);
  }

  return (
    <>
      <button className="chat-toggle" onClick={() => setIsOpen(!isOpen)} title="Chat">
        {isOpen ? '\u2715' : '\uD83D\uDCAC'}
      </button>

      {isOpen && (
        <aside className="chat-sidebar">
          <div className="chat-header">
            <h3>Fashion Assistant</h3>
            <button onClick={clearChat} className="btn btn-sm" title="Clear chat">
              Clear
            </button>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <p className="chat-empty">Ask me anything about your wardrobe!</p>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
                <div className="chat-msg-content">{msg.content}</div>
              </div>
            ))}
            {isLoading && <div className="chat-msg chat-msg-assistant"><div className="chat-msg-content">Thinking...</div></div>}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type a message..."
              disabled={isLoading}
            />
            <button onClick={handleSend} disabled={isLoading || !input.trim()}>
              Send
            </button>
          </div>
        </aside>
      )}
    </>
  );
}
