from fastapi import HTTPException, Header
from auth.utils import decode_token


async def get_current_user(authorization: str = Header(...)) -> str:
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid authorization header')

    token = authorization.split(' ', 1)[1]
    try:
        payload = decode_token(token)
        return payload['sub']
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
