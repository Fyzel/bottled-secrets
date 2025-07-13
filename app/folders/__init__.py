"""Folders blueprint for Bottled Secrets Flask application.

This module provides the folders blueprint for managing secret folders
and their access permissions.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.folders
.. platform:: Unix, Windows
.. synopsis:: Folders management blueprint
"""

from flask import Blueprint

bp = Blueprint("folders", __name__)

from app.folders import routes
