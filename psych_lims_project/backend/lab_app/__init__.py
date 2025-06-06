import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
        app.config['ENCRYPTION_KEY'] = os.environ.get('ENCRYPTION_KEY') # Ensure this is loaded
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": os.environ.get('CORS_ORIGINS', '').split(',')}})
    limiter.init_app(app)

    from .routes.lab_routes import lab_bp

    # Register Blueprints here (if any)
    # from .api import main_api_blueprint
    # app.register_blueprint(main_api_blueprint, url_prefix='/api')
    app.register_blueprint(lab_bp)

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok"}), 200

    # Initialize Alembic within app context for migrations
    with app.app_context():
        if db.engine.url.drivername == 'sqlite':
            migrate.init_app(app, db, render_as_batch=True)
        else:
            migrate.init_app(app, db)

    from . import models # Ensure models are registered with SQLAlchemy instance

    return app
