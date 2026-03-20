from flask import Blueprint

wardrobe_bp = Blueprint('wardrobe', __name__)

from wardrobe import routes  # noqa: E402, F401
