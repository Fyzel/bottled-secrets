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
from datetime import datetime
from flask import Flask
from config.config import Config
from app.models import db

__all__ = ["create_app"]


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
    if not app.config.get("SECRET_KEY"):
        raise ValueError("SECRET_KEY must be set in configuration")

    # Initialize database
    db.init_app(app)

    # Register template filters
    @app.template_filter("strftime")
    def strftime_filter(value: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a datetime string using strftime.

        :param value: The datetime string to format
        :type value: str
        :param format_string: The format string to use
        :type format_string: str
        :returns: Formatted datetime string
        :rtype: str
        """
        if not value:
            return ""
        try:
            # Parse ISO format datetime string
            if "T" in value:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(value)
            return dt.strftime(format_string)
        except (ValueError, AttributeError):
            # If parsing fails, return original value
            return value

    @app.template_filter("datetime_friendly")
    def datetime_friendly_filter(value: str) -> str:
        """Format a datetime string in a user-friendly format.

        :param value: The datetime string to format
        :type value: str
        :returns: User-friendly datetime string
        :rtype: str
        """
        if not value:
            return "Never"
        try:
            # Parse ISO format datetime string
            if "T" in value:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(value)

            # Format as "Dec 15, 2024 at 2:30 PM"
            return dt.strftime("%b %d, %Y at %I:%M %p")
        except (ValueError, AttributeError):
            # If parsing fails, return original value truncated
            return value[:19] if len(value) > 19 else value

    # Register blueprints
    from app.main import bp as main_bp  # pylint: disable=import-outside-toplevel

    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp  # pylint: disable=import-outside-toplevel

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.admin import bp as admin_bp  # pylint: disable=import-outside-toplevel

    app.register_blueprint(admin_bp, url_prefix="/admin")

    from app.folders import bp as folders_bp  # pylint: disable=import-outside-toplevel

    app.register_blueprint(folders_bp, url_prefix="/folders")

    return app
