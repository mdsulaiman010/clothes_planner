import client from './client';

export async function login(username: string, password: string) {
  const { data } = await client.post('/auth/login', { username, password });
  return data as { token: string; username: string };
}

export async function register(username: string, password: string, mobile_number: string) {
  const { data } = await client.post('/auth/register', { username, password, mobile_number });
  return data as { message: string };
}

export async function refreshToken() {
  const { data } = await client.post('/auth/refresh');
  return data as { token: string };
}
