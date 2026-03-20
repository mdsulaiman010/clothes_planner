from flask import Flask
from flask_cors import CORS
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from auth import auth_bp
    from wardrobe import wardrobe_bp
    from tryon import tryon_bp
    from chat import chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(wardrobe_bp, url_prefix='/api/wardrobe')
    app.register_blueprint(tryon_bp, url_prefix='/api/tryon')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
