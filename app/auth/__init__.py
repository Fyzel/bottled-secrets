"""Authentication module for Bottled Secrets Flask application.

This module provides SAML authentication integration with Google and Microsoft Azure
identity providers, including user session management and access control.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.auth
.. platform:: Unix, Windows
.. synopsis:: SAML authentication blueprint

Example:
    Register the authentication blueprint::

        from app.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
"""

from flask import Blueprint

__all__ = ['bp']

bp = Blueprint('auth', __name__)  # pylint: disable=invalid-name

from app.auth import routes  # pylint: disable=wrong-import-position