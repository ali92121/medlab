from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=None):
    app = Flask(__name__)

    # Configuration
    # In a real app, use a Config class or environment variables
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///./lab_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret') # Change this!

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Blueprints
    from lab_app.routes.patient_routes import patient_bp
    app.register_blueprint(patient_bp, url_prefix='/api/patients')

    from lab_app.routes.assessment_routes import assessment_bp
    app.register_blueprint(assessment_bp, url_prefix='/api')

    # A simple route to test
    @app.route('/hello')
    def hello():
        return "Hello, World!"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
