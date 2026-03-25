from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth.utils import hash_password, create_token
from auth.dependencies import get_current_user
from services.db_functions import connect_supabase, supabase_check_existing_users

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    mobile_number: str


@router.post('/login')
def login(body: LoginRequest):
    username = body.username.strip()
    password = body.password

    if not username or not password:
        raise HTTPException(status_code=400, detail='Username and password are required')

    client = connect_supabase()
    hashed_pw = hash_password(password)
    response = client.table('users').select('*').eq('username', username).eq('password', hashed_pw).execute()

    if len(response.data) == 0:
        raise HTTPException(status_code=401, detail='Invalid username or password')

    token = create_token(username)
    return {'token': token, 'username': username}


@router.post('/register')
def register(body: RegisterRequest):
    username = body.username.strip()
    password = body.password
    mobile_number = body.mobile_number.strip()

    if not username or not password or not mobile_number:
        raise HTTPException(status_code=400, detail='Username, password, and mobile number are required')

    client = connect_supabase()
    existing_users = supabase_check_existing_users(client)

    if username in existing_users:
        raise HTTPException(status_code=409, detail='Username already taken')

    hashed_pw = hash_password(password)
    user_dict = {
        'username': username,
        'password': hashed_pw,
        'mobile_number': mobile_number,
    }
    response = client.table('users').insert(user_dict).execute()

    if response.data:
        return {'message': 'Account created successfully'}
    raise HTTPException(status_code=500, detail='Failed to create account')


@router.post('/refresh')
def refresh(current_user: str = Depends(get_current_user)):
    token = create_token(current_user)
    return {'token': token}
