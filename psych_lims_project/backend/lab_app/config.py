import os
from dotenv import load_dotenv

load_dotenv() # Load .env file from the backend directory

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///psych_lims_local.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt'
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')

    # Ensure ENCRYPTION_KEY is loaded and is of correct type (bytes) if required by AesEngine
    # For SQLAlchemy-utils EncryptedType with AesEngine, the key is typically expected as a string
    # which it then processes. If a specific byte format is needed, conversion should happen here.
    # The default AesEngine uses a SHA256 hash of the string key if it's not 32 bytes.
    # For explicit 32-byte key usage without hashing by AesEngine, ensure your .env key is exactly 32 bytes.
    if ENCRYPTION_KEY and len(ENCRYPTION_KEY.encode('utf-8')) != 32:
        # This is a placeholder for a real key validation/generation strategy
        # For this setup, we'll assume the key in .env is correctly formatted or AesEngine handles it.
        # In a production system, you'd want to ensure this key is robust.
        pass

# You can add other configurations like DevelopmentConfig, ProductionConfig, etc.
# class DevelopmentConfig(Config):
#     DEBUG = True

# class ProductionConfig(Config):
#     DEBUG = False

# For this setup, the default Config class will be used by create_app if no specific config_class is passed.
# Modify lab_app/__init__.py to use this config.
# The current __init__.py already loads from os.environ directly, which is fine for this setup.
# We will modify __init__.py to also load the ENCRYPTION_KEY from app.config for models.py
# and ensure that the ENCRYPTION_KEY is available in app.config.
