from flask import request, jsonify, g
from tryon import tryon_bp
from auth.decorators import jwt_required
from tryon.factory import get_tryon_provider
from services.db_functions import mongodb_get_item_by_id
from services.s3_service import s3_get_presigned_urls_for_user


@tryon_bp.route('/generate', methods=['POST'])
@jwt_required
def generate():
    data = request.get_json()
    selfie_image_b64 = data.get('selfie_image_b64', '')
    clothing_item_id = data.get('clothing_item_id', '')
    provider_name = data.get('provider', 'fashn')

    if not selfie_image_b64 or not clothing_item_id:
        return jsonify({'error': 'selfie_image_b64 and clothing_item_id are required'}), 400

    # Get clothing image URL
    doc = mongodb_get_item_by_id(clothing_item_id)
    if not doc:
        return jsonify({'error': 'Clothing item not found'}), 404

    if doc.get('uploadedBy') != g.current_user:
        return jsonify({'error': 'Unauthorized'}), 403

    urls = s3_get_presigned_urls_for_user(g.current_user, [clothing_item_id])
    if not urls:
        return jsonify({'error': 'Could not get clothing image URL'}), 500

    clothing_url = urls[0]['url']

    try:
        provider = get_tryon_provider(provider_name)
        result = provider.submit_job(selfie_image_b64, clothing_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tryon_bp.route('/result/<job_id>', methods=['GET'])
@jwt_required
def get_result(job_id):
    provider_name = request.args.get('provider', 'fashn')

    try:
        provider = get_tryon_provider(provider_name)
        result = provider.get_result(job_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
