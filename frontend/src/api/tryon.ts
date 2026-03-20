import client from './client';

export async function generateTryOn(selfie_image_b64: string, clothing_item_id: string, provider = 'fashn') {
  const { data } = await client.post('/tryon/generate', {
    selfie_image_b64,
    clothing_item_id,
    provider,
  });
  return data as { job_id: string; status: string };
}

export async function getTryOnResult(jobId: string, provider = 'fashn') {
  const { data } = await client.get(`/tryon/result/${jobId}`, {
    params: { provider },
  });
  return data as { status: string; result_image_url: string | null };
}
