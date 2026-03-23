import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from models import db, User
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///claraai.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize DB
    db.init_app(app)
    
    # Configure Logging for AI errors
    if not os.path.exists('logs'):
        os.mkdir('logs')
    # Rotating log file, max 1MB, keep 5 backups
    file_handler = RotatingFileHandler('logs/ai_error.log', maxBytes=1024000, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.ERROR)
    
    # Also add handler to a specific ai_logger if we want
    ai_logger = logging.getLogger('ai_logger')
    ai_logger.addHandler(file_handler)
    ai_logger.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)
    
    # Register Blueprints
    from routes import main_bp, auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    
    # Create DB tables
    with app.app_context():
        db.create_all()
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
