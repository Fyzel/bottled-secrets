"""Configuration module for Bottled Secrets Flask application.

This module defines configuration classes for different environments
(development, production, testing) and loads environment variables
from .env files using python-dotenv.

.. moduleauthor:: Bottled Secrets Team
.. module:: config.config
.. platform:: Unix, Windows
.. synopsis:: Application configuration management

Example:
    Use configuration classes::

        from config.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
"""

import os
from typing import Dict, Type
from dotenv import load_dotenv

__all__ = ['Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig', 'CONFIG_MAP']

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))


class Config:
    """Base configuration class with common settings.

    This class contains configuration settings that are common across
    all environments. Environment-specific configurations inherit from
    this base class.

    :cvar SECRET_KEY: Application secret key for sessions and CSRF protection
    :type SECRET_KEY: str
    :cvar DATABASE_URL: Database connection URL
    :type DATABASE_URL: str
    :cvar DEBUG: Debug mode setting (controlled by FLASK_DEBUG env var)
    :type DEBUG: bool

    Example:
        Inherit from base config::

            class CustomConfig(Config):
                DEBUG = True
    """
    
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_URL: str = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://user:password@localhost:3306/bottled_secrets'
    
    # Debug mode should be controlled by environment variables, not hardcoded
    DEBUG: bool = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')


class DevelopmentConfig(Config):
    """Development environment configuration.

    This configuration is used during development and includes
    debug mode enabled and development-specific settings.

    :cvar DEBUG: Enable debug mode for development (can be overridden by FLASK_DEBUG)
    :type DEBUG: bool
    """
    
    # Default to debug mode in development, but allow environment override
    DEBUG: bool = os.environ.get('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')


class ProductionConfig(Config):
    """Production environment configuration.

    This configuration is used in production and includes
    security-focused settings with debug mode disabled.

    :cvar DEBUG: Debug mode disabled for production security
    :type DEBUG: bool
    """
    
    # Production should never have debug mode enabled for security
    DEBUG: bool = False


class TestingConfig(Config):
    """Testing environment configuration.

    This configuration is used during testing and includes
    in-memory database and testing-specific settings.

    :cvar TESTING: Enable testing mode
    :type TESTING: bool
    :cvar DATABASE_URL: In-memory SQLite database for testing
    :type DATABASE_URL: str
    """
    
    TESTING: bool = True
    DATABASE_URL: str = 'sqlite:///:memory:'


CONFIG_MAP: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}