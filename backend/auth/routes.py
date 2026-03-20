from flask import request, jsonify, g
from auth import auth_bp
from auth.utils import hash_password, create_token
from auth.decorators import jwt_required
from services.db_functions import connect_supabase, supabase_check_existing_users


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    client = connect_supabase()
    hashed_pw = hash_password(password)
    response = client.table('users').select('*').eq('username', username).eq('password', hashed_pw).execute()

    if len(response.data) == 0:
        return jsonify({'error': 'Invalid username or password'}), 401

    token = create_token(username)
    return jsonify({'token': token, 'username': username})


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    mobile_number = data.get('mobile_number', '').strip()

    if not username or not password or not mobile_number:
        return jsonify({'error': 'Username, password, and mobile number are required'}), 400

    client = connect_supabase()
    existing_users = supabase_check_existing_users(client)

    if username in existing_users:
        return jsonify({'error': 'Username already taken'}), 409

    hashed_pw = hash_password(password)
    user_dict = {
        'username': username,
        'password': hashed_pw,
        'mobile_number': mobile_number,
    }
    response = client.table('users').insert(user_dict).execute()

    if response.data:
        return jsonify({'message': 'Account created successfully'}), 201
    return jsonify({'error': 'Failed to create account'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required
def refresh():
    token = create_token(g.current_user)
    return jsonify({'token': token})
