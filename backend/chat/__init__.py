from flask import Blueprint

chat_bp = Blueprint('chat', __name__)

from chat import routes  # noqa: E402, F401
