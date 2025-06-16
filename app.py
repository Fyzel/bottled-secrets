"""Main application entry point for Bottled Secrets Flask application.

This module creates and runs the Flask application instance using the
application factory pattern.

.. moduleauthor:: Bottled Secrets Team
.. module:: app
.. platform:: Unix, Windows
.. synopsis:: Flask application entry point

Example:
    Run the application directly::

        $ python app.py

    Or run with Flask CLI::

        $ flask run
"""

from app import create_app

app = create_app()  # pylint: disable=invalid-name

if __name__ == '__main__':
    app.run(debug=True)