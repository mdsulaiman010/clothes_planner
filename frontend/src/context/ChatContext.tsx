import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { sendMessage as apiSendMessage, getChatHistory, clearChatHistory, ChatMessage } from '../api/chat';
import { useAuth } from './AuthContext';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  sendMessage: (text: string) => Promise<void>;
  clearChat: () => Promise<void>;
  pageContext: Record<string, unknown>;
  setPageContext: React.Dispatch<React.SetStateAction<Record<string, unknown>>>;
}

const ChatContext = createContext<ChatState>(null!);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pageContext, setPageContext] = useState<Record<string, unknown>>({});
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  // Auto-update page context on route change
  useEffect(() => {
    const page = location.pathname.replace('/', '') || 'home';
    setPageContext((prev) => ({ ...prev, page }));
  }, [location.pathname]);

  // Load history on auth
  useEffect(() => {
    if (isAuthenticated) {
      getChatHistory().then((data) => setMessages(data.messages)).catch(() => {});
    } else {
      setMessages([]);
    }
  }, [isAuthenticated]);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMsg: ChatMessage = { role: 'user', content: text, timestamp: Date.now() / 1000 };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const { reply } = await apiSendMessage(text, pageContext);
        const assistantMsg: ChatMessage = { role: 'assistant', content: reply, timestamp: Date.now() / 1000 };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch {
        const errMsg: ChatMessage = { role: 'assistant', content: 'Sorry, something went wrong.', timestamp: Date.now() / 1000 };
        setMessages((prev) => [...prev, errMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [pageContext],
  );

  const clearChat = useCallback(async () => {
    await clearChatHistory();
    setMessages([]);
  }, []);

  return (
    <ChatContext.Provider value={{ messages, isLoading, sendMessage, clearChat, pageContext, setPageContext }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  return useContext(ChatContext);
}
