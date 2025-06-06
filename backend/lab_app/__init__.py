# This file makes lab_app a Python package.
# It can also be used for application factory pattern, e.g., initializing Flask app and extensions.

# For now, it's kept simple.
# Potential future content:
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_socketio import SocketIO
# from .database import Base, engine

# db = SQLAlchemy()
# socketio = SocketIO()

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object('config.Config') # Example configuration

#     db.init_app(app)
#     socketio.init_app(app, cors_allowed_origins="*")

#     # Create database tables if they don't exist
#     # with app.app_context():
#     #     Base.metadata.create_all(bind=engine)


#     # Import and register blueprints
#     from .routes.clinical_intelligence import intelligence_bp
#     from .routes.pro_routes import pro_bp
#     # ... other blueprints ...

#     # app.register_blueprint(intelligence_bp)
#     # app.register_blueprint(pro_bp)
#     # ...

#     # Register SocketIO event handlers
#     # from .routes.alert_ws_routes import register_socketio_events
#     # register_socketio_events(socketio)

#     return app

# print("lab_app package loaded")
