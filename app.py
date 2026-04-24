import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from models import db, User
from routes import main_bp, auth_bp
from admin_routes import admin_bp
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Initializes the Flask application, configures global services, and registers core blueprints.
def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')
    
    # Ensure instance folder exists for the database
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'claraai.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    logs_dir = os.path.join(basedir, 'logs')
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    
    file_handler = RotatingFileHandler(os.path.join(logs_dir, 'ai_error.log'), maxBytes=1024000, backupCount=5)
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
    app.register_blueprint(admin_bp)
    
    with app.app_context():
        db.create_all()
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
