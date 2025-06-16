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

import os
from app import create_app
from config.config import CONFIG_MAP

# Get configuration from environment or default to development
config_name = os.environ.get('FLASK_ENV', 'development')
config_class = CONFIG_MAP.get(config_name, CONFIG_MAP['default'])

app = create_app(config_class)  # pylint: disable=invalid-name

if __name__ == '__main__':
    # Use debug setting from configuration, not hardcoded
    debug_mode = app.config.get('DEBUG', False)
    app.run(debug=debug_mode)