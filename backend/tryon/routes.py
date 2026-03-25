from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from auth.dependencies import get_current_user
from tryon.factory import get_tryon_provider
from services.db_functions import mongodb_get_item_by_id
from services.s3_service import s3_get_presigned_urls_for_user

router = APIRouter()


class GenerateRequest(BaseModel):
    selfie_image_b64: str
    clothing_item_id: str
    provider: str = 'fashn'


@router.post('/generate')
def generate(body: GenerateRequest, current_user: str = Depends(get_current_user)):
    if not body.selfie_image_b64 or not body.clothing_item_id:
        raise HTTPException(status_code=400, detail='selfie_image_b64 and clothing_item_id are required')

    doc = mongodb_get_item_by_id(body.clothing_item_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Clothing item not found')

    if doc.get('uploadedBy') != current_user:
        raise HTTPException(status_code=403, detail='Unauthorized')

    urls = s3_get_presigned_urls_for_user(current_user, [body.clothing_item_id])
    if not urls:
        raise HTTPException(status_code=500, detail='Could not get clothing image URL')

    clothing_url = urls[0]['url']

    try:
        provider = get_tryon_provider(body.provider)
        result = provider.submit_job(body.selfie_image_b64, clothing_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/result/{job_id}')
def get_result(job_id: str, provider: str = Query('fashn'), current_user: str = Depends(get_current_user)):
    try:
        tryon_provider = get_tryon_provider(provider)
        result = tryon_provider.get_result(job_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
