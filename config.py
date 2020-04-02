import os
base_dir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'this-is-a-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('PG_DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TRAP_HTTP_EXCEPTIONS = True


class ProductionConfig(Config):
    """
    """
    DEBUG = False


class StagingConfig(Config):
    """
    """
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """
    """
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
