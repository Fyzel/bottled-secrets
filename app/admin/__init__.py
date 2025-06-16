"""Administration module for Bottled Secrets Flask application.

This module provides administrative functionality for managing users,
roles, and system configuration. Access is restricted to users with
the User Administrator role.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.admin
.. platform:: Unix, Windows
.. synopsis:: Administration blueprint

Example:
    Register the administration blueprint::

        from app.admin import bp as admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
"""

from flask import Blueprint

__all__ = ['bp']

bp = Blueprint('admin', __name__)  # pylint: disable=invalid-name

from app.admin import routes  # pylint: disable=wrong-import-position