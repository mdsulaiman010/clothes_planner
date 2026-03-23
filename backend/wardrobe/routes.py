import os
import json
from flask import request, jsonify, g
from wardrobe import wardrobe_bp
from auth.decorators import jwt_required
from services.db_functions import (
    connect_mongodb,
    mongodb_filter_by_user_and_category,
    mongodb_count_by_user_and_category,
    mongodb_save_image_and_metadata,
    mongodb_get_item_by_id,
    mongodb_delete_item,
)
from services.s3_service import s3_upload_image, s3_get_presigned_urls_for_user, s3_delete_image, connect_s3


@wardrobe_bp.route('/upload', methods=['POST'])
@jwt_required
def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files provided'}), 400

    _, clothes_db = connect_mongodb()
    collection = clothes_db['items']
    items = []

    for f in files:
        raw = f.read()
        item_id, item_path = mongodb_save_image_and_metadata(collection, g.current_user, raw)

        if item_id:
            try:
                s3_upload_image(item_path, g.current_user)
                temp_dir = os.path.join(os.path.dirname(__file__), '..', 'tempImages')
                temp_file = os.path.join(temp_dir, item_path)
                if os.path.exists(temp_file):
                    os.remove(temp_file)

                doc = mongodb_get_item_by_id(item_id)
                bucket_name = os.environ['S3_BUCKET_NAME']
                s3_client = connect_s3(return_type='client')
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': f"{g.current_user}/{item_path}"},
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

    return jsonify({'items': items}), 201


@wardrobe_bp.route('/items', methods=['GET'])
@jwt_required
def get_items():
    category = request.args.get('category', 'top')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 20))

    item_ids = mongodb_filter_by_user_and_category(g.current_user, category, skip, limit)
    total = mongodb_count_by_user_and_category(g.current_user, category)

    items = s3_get_presigned_urls_for_user(g.current_user, item_ids)

    # Enrich with metadata
    for item in items:
        doc = mongodb_get_item_by_id(item['id'])
        if doc:
            item['mainCategory'] = doc.get('mainCategory', '')
            item['subCategory'] = doc.get('subCategory', '')

    return jsonify({'items': items, 'total': total})


@wardrobe_bp.route('/categories', methods=['GET'])
def get_categories():
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    with open(os.path.join(prompts_dir, 'clothing_hierarchy.json'), 'r') as f:
        categories = json.load(f)
    return jsonify(categories)


@wardrobe_bp.route('/items/<item_id>', methods=['DELETE'])
@jwt_required
def delete_item(item_id):
    doc = mongodb_get_item_by_id(item_id)
    if not doc:
        return jsonify({'error': 'Item not found'}), 404

    if doc.get('uploadedBy') != g.current_user:
        return jsonify({'error': 'Unauthorized'}), 403

    # Delete from S3
    ext = doc.get('format', 'png').lower()
    s3_key = f"{g.current_user}/{item_id}_{g.current_user}.{ext}"
    try:
        s3_delete_image(s3_key)
    except Exception:
        pass  # S3 deletion is best-effort

    # Delete from MongoDB
    mongodb_delete_item(item_id)
    return jsonify({'message': 'Item deleted'}), 200
