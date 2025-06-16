"""Route handlers for the main blueprint of Bottled Secrets Flask application.

This module contains the route definitions and view functions for the main
blueprint, handling the primary user-facing pages of the application.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.main.routes
.. platform:: Unix, Windows
.. synopsis:: Main blueprint route handlers

Example:
    Access the index route::

        GET /
        GET /index
"""

from flask import render_template
from app.main import bp

__all__ = ['index']


@bp.route('/')
@bp.route('/index')
def index() -> str:
    """Render the main index page.

    This view function handles requests to the root URL and /index,
    rendering the main landing page of the Bottled Secrets application.

    :returns: Rendered HTML template for the index page
    :rtype: str
    :raises TemplateNotFound: If the template file cannot be found

    Example:
        Access via browser::

            http://localhost:5000/
            http://localhost:5000/index
    """
    return render_template('index.html', title='Bottled Secrets')