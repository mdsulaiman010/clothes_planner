import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth.dependencies import get_current_user
from chat.gemini_service import GeminiChatService
from chat.context import build_system_prompt
from services.db_functions import connect_mongodb

router = APIRouter()
gemini_service = GeminiChatService()


class SendMessageRequest(BaseModel):
    message: str
    page_context: dict = {}


def _get_chat_collection():
    _, db = connect_mongodb()
    return db['chat_sessions']


@router.post('/message')
def send_message(body: SendMessageRequest, current_user: str = Depends(get_current_user)):
    message = body.message.strip()
    page_context = body.page_context

    if not message:
        raise HTTPException(status_code=400, detail='Message is required')

    collection = _get_chat_collection()

    session = collection.find_one({'username': current_user})
    history = session.get('messages', []) if session else []

    system_prompt = build_system_prompt(page_context)

    try:
        reply = gemini_service.get_reply(message, system_prompt, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Chat service error: {str(e)}')

    now = time.time()
    user_msg = {'role': 'user', 'content': message, 'timestamp': now}
    assistant_msg = {'role': 'assistant', 'content': reply, 'timestamp': now}

    collection.update_one(
        {'username': current_user},
        {'$push': {'messages': {'$each': [user_msg, assistant_msg]}}},
        upsert=True,
    )

    return {'reply': reply}


@router.get('/history')
def get_history(current_user: str = Depends(get_current_user)):
    collection = _get_chat_collection()
    session = collection.find_one({'username': current_user})
    messages = session.get('messages', []) if session else []
    return {'messages': messages}


@router.delete('/history')
def clear_history(current_user: str = Depends(get_current_user)):
    collection = _get_chat_collection()
    collection.update_one(
        {'username': current_user},
        {'$set': {'messages': []}},
    )
    return {'message': 'Chat history cleared'}
