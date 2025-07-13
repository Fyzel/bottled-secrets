#!/usr/bin/env python3
"""Database table creation script for Bottled Secrets.

This script creates all database tables required for the application,
including folders, secrets, and permissions tables.

Usage:
    python create_tables.py
"""

import os
import sys
from app import create_app
from app.models import db


def create_tables():
    """Create all database tables."""
    app = create_app()

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
