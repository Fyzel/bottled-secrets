"""Application factory module for Bottled Secrets Flask application.

This module implements the application factory pattern, providing a function
to create and configure Flask application instances with blueprints and
configuration settings.

.. moduleauthor:: Bottled Secrets Team
.. module:: app
.. platform:: Unix, Windows
.. synopsis:: Flask application factory

Example:
    Create a Flask application instance::

        from app import create_app
        app = create_app()
        app.run()
"""

from typing import Type
from flask import Flask
from config.config import Config

__all__ = ['create_app']


def create_app(config_class: Type[Config] = Config) -> Flask:
    """Create and configure a Flask application instance.

    This function implements the application factory pattern, creating a new
    Flask application instance with the specified configuration and registering
    all necessary blueprints.

    :param config_class: Configuration class to use for the application
    :type config_class: type
    :returns: Configured Flask application instance
    :rtype: flask.Flask
    :raises ImportError: If required modules cannot be imported
    :raises ValueError: If required configuration is missing

    Example:
        Create app with default config::

            app = create_app()

        Create app with custom config::

            app = create_app(ProductionConfig)
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Validate configuration
    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in configuration")
    
    # Register blueprints
    from app.main import bp as main_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.admin import bp as admin_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app