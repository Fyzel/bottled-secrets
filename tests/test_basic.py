"""Basic test cases for Bottled Secrets Flask application.

This module contains fundamental test cases that verify the basic
functionality of the Flask application, including route responses
and application setup.

.. moduleauthor:: Bottled Secrets Team
.. module:: tests.test_basic
.. platform:: Unix, Windows
.. synopsis:: Basic application tests

Example:
    Run this test module::

        python -m unittest tests.test_basic
        python -m pytest tests/test_basic.py
"""

import unittest
from flask import Flask
from flask.ctx import AppContext
from flask.testing import FlaskClient
from app import create_app
from config.config import TestingConfig


class BasicTestCase(unittest.TestCase):
    """Basic test case class for fundamental application testing.

    This test case class contains tests for basic application functionality,
    including route accessibility and response validation.

    :ivar app: Flask application instance for testing
    :type app: flask.Flask
    :ivar app_context: Flask application context
    :type app_context: flask.ctx.AppContext
    :ivar client: Flask test client
    :type client: flask.testing.FlaskClient
    """

    def setUp(self) -> None:
        """Set up test fixtures before each test method.

        Creates a test application instance with testing configuration,
        sets up application context, and initializes a test client.

        :raises ImportError: If application modules cannot be imported
        :raises RuntimeError: If application context setup fails
        """
        self.app: Flask = create_app(TestingConfig)
        self.app_context: AppContext = self.app.app_context()
        self.app_context.push()
        self.client: FlaskClient = self.app.test_client()

    def tearDown(self) -> None:
        """Clean up after each test method.

        Removes the application context to ensure clean state
        between test runs.

        :raises RuntimeError: If context cleanup fails
        """
        self.app_context.pop()

    def test_index(self) -> None:
        """Test the index route accessibility and content.

        Verifies that the root URL returns a successful response
        and contains expected content.

        :raises AssertionError: If response status or content is incorrect
        :raises ConnectionError: If test client cannot connect
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to Bottled Secrets', response.data)


if __name__ == '__main__':
    unittest.main()