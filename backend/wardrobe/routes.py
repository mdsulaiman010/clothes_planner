import os
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from auth.dependencies import get_current_user
from services.db_functions import (
    connect_mongodb,
    mongodb_filter_by_user_and_category,
    mongodb_count_by_user_and_category,
    mongodb_save_image_and_metadata,
    mongodb_get_item_by_id,
    mongodb_delete_item,
)
from services.s3_service import s3_upload_image, s3_get_presigned_urls_for_user, s3_delete_image, connect_s3
from config import settings

router = APIRouter()


@router.post('/upload')
async def upload(
    files: list[UploadFile] = File(...),
    current_user: str = Depends(get_current_user),
):
    _, clothes_db = connect_mongodb()
    collection = clothes_db['items']
    items = []

    for f in files:
        raw = await f.read()
        item_id, item_path = mongodb_save_image_and_metadata(collection, current_user, raw)

        if item_id:
            try:
                s3_upload_image(item_path, current_user)
                temp_file = os.path.join(settings.TEMP_DIR, item_path)
                if os.path.exists(temp_file):
                    os.remove(temp_file)

                doc = mongodb_get_item_by_id(item_id)
                bucket_name = os.environ['S3_BUCKET_NAME']
                s3_client = connect_s3(return_type='client')
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': f"{current_user}/{item_path}"},
                    ExpiresIn=3600,
                )
                items.append({
                    'id': item_id,
                    'url': url,
                    'mainCategory': doc.get('mainCategory', '') if doc else '',
                    'subCategory': doc.get('subCategory', '') if doc else '',
                })
            except Exception as e:
                items.append({'id': item_id, 'error': str(e)})
        else:
            items.append({'error': f'Failed to process {f.filename}'})

    return {'items': items}


@router.get('/items')
def get_items(
    category: str = Query('top'),
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: str = Depends(get_current_user),
):
    item_ids = mongodb_filter_by_user_and_category(current_user, category, skip, limit)
    total = mongodb_count_by_user_and_category(current_user, category)

    items = s3_get_presigned_urls_for_user(current_user, item_ids)

    for item in items:
        doc = mongodb_get_item_by_id(item['id'])
        if doc:
            item['mainCategory'] = doc.get('mainCategory', '')
            item['subCategory'] = doc.get('subCategory', '')

    return {'items': items, 'total': total}


@router.get('/categories')
def get_categories():
    with open(os.path.join(settings.PROMPTS_DIR, 'clothing_hierarchy.json'), 'r') as f:
        categories = json.load(f)
    return categories


@router.delete('/items/{item_id}')
def delete_item(item_id: str, current_user: str = Depends(get_current_user)):
    doc = mongodb_get_item_by_id(item_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Item not found')

    if doc.get('uploadedBy') != current_user:
        raise HTTPException(status_code=403, detail='Unauthorized')

    ext = doc.get('format', 'png').lower()
    s3_key = f"{current_user}/{item_id}_{current_user}.{ext}"
    try:
        s3_delete_image(s3_key)
    except Exception:
        pass

    mongodb_delete_item(item_id)
    return {'message': 'Item deleted'}
