#!/usr/bin/env python3
"""Database table creation script for Bottled Secrets (bypasses SAML imports).

This script creates all database tables required for the application,
including folders, secrets, and permissions tables.

Usage:
    python create_tables_simple.py
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SimpleConfig:
    """Simple configuration for table creation."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Import models directly to avoid SAML route imports
from app.models import db


def create_tables():
    """Create all database tables."""
    app = Flask(__name__)
    app.config.from_object(SimpleConfig)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")

            # Print table information
            tables = db.metadata.tables.keys()
            print(f"📋 Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")

        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            sys.exit(1)


if __name__ == "__main__":
    print("🗄️  Creating database tables for Bottled Secrets...")
    create_tables()
