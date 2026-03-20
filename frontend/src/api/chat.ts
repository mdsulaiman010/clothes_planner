import client from './client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export async function sendMessage(message: string, page_context: Record<string, unknown>) {
  const { data } = await client.post('/chat/message', { message, page_context });
  return data as { reply: string };
}

export async function getChatHistory() {
  const { data } = await client.get('/chat/history');
  return data as { messages: ChatMessage[] };
}

export async function clearChatHistory() {
  await client.delete('/chat/history');
}
