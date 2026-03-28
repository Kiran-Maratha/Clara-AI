import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from models import db, User
from routes import main_bp, auth_bp
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

# Initializes the Flask application, configures global services, and registers core blueprints.
def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///claraai.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/ai_error.log', maxBytes=1024000, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.ERROR)
    
    ai_logger = logging.getLogger('ai_logger')
    ai_logger.addHandler(file_handler)
    ai_logger.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    
    with app.app_context():
        db.create_all()
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
