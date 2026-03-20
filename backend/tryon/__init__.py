from flask import Blueprint

tryon_bp = Blueprint('tryon', __name__)

from tryon import routes  # noqa: E402, F401
