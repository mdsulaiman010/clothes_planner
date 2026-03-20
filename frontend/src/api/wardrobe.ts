import client from './client';

export interface WardrobeItem {
  id: string;
  url: string;
  s3_key?: string;
  mainCategory?: string;
  subCategory?: string;
}

export async function uploadFiles(files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const { data } = await client.post('/wardrobe/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data as { items: Array<{ id: string; mainCategory: string; subCategory: string }> };
}

export async function getItems(category: string, skip = 0, limit = 20) {
  const { data } = await client.get('/wardrobe/items', {
    params: { category, skip, limit },
  });
  return data as { items: WardrobeItem[]; total: number };
}

export async function getCategories() {
  const { data } = await client.get('/wardrobe/categories');
  return data as Record<string, string[]>;
}

export async function deleteItem(itemId: string) {
  const { data } = await client.delete(`/wardrobe/items/${itemId}`);
  return data;
}
