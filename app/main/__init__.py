"""Main blueprint module for Bottled Secrets Flask application.

This module defines the main blueprint for the application, which handles
the primary routes and functionality of the Bottled Secrets application.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.main
.. platform:: Unix, Windows
.. synopsis:: Main application blueprint

Example:
    Import the blueprint::\n\n        from app.main import bp\n        app.register_blueprint(bp)
"""

from flask import Blueprint

__all__ = ['bp']

bp = Blueprint('main', __name__)  # pylint: disable=invalid-name

from app.main import routes  # pylint: disable=wrong-import-position