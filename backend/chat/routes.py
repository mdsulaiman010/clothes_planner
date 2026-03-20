import time
from flask import request, jsonify, g
from chat import chat_bp
from auth.decorators import jwt_required
from chat.gemini_service import GeminiChatService
from chat.context import build_system_prompt
from services.db_functions import connect_mongodb

gemini_service = GeminiChatService()


def _get_chat_collection():
    _, db = connect_mongodb()
    return db['chat_sessions']


@chat_bp.route('/message', methods=['POST'])
@jwt_required
def send_message():
    data = request.get_json()
    message = data.get('message', '').strip()
    page_context = data.get('page_context', {})

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    collection = _get_chat_collection()

    # Get or create chat session
    session = collection.find_one({'username': g.current_user})
    history = session.get('messages', []) if session else []

    # Build context-aware system prompt
    system_prompt = build_system_prompt(page_context)

    # Get reply from Gemini
    try:
        reply = gemini_service.get_reply(message, system_prompt, history)
    except Exception as e:
        return jsonify({'error': f'Chat service error: {str(e)}'}), 500

    # Save messages
    now = time.time()
    user_msg = {'role': 'user', 'content': message, 'timestamp': now}
    assistant_msg = {'role': 'assistant', 'content': reply, 'timestamp': now}

    collection.update_one(
        {'username': g.current_user},
        {'$push': {'messages': {'$each': [user_msg, assistant_msg]}}},
        upsert=True,
    )

    return jsonify({'reply': reply})


@chat_bp.route('/history', methods=['GET'])
@jwt_required
def get_history():
    collection = _get_chat_collection()
    session = collection.find_one({'username': g.current_user})
    messages = session.get('messages', []) if session else []
    return jsonify({'messages': messages})


@chat_bp.route('/history', methods=['DELETE'])
@jwt_required
def clear_history():
    collection = _get_chat_collection()
    collection.update_one(
        {'username': g.current_user},
        {'$set': {'messages': []}},
    )
    return jsonify({'message': 'Chat history cleared'})
