#!/usr/bin/env python3
"""Development server startup script for Bottled Secrets.

This script starts the Flask development server with proper configuration
for testing the folder management system.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if we can import the full application
try:
    from app import create_app

    app = create_app()
    print("✅ Full application loaded successfully")
except Exception as e:
    print(f"⚠️  SAML import issue detected: {e}")
    print("🔄 Creating minimal Flask app for folder testing...")

    # Create a minimal Flask app with just the folder system
    from flask import Flask, session, redirect, url_for
    from app.models import db
    from app.folders import bp as folders_bp
    from config.config import DevelopmentConfig

    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # Initialize database
    db.init_app(app)

    # Register only the folders blueprint
    app.register_blueprint(folders_bp, url_prefix="/folders")

    # Add a simple home route that redirects to folders
    @app.route("/")
    def index():
        # Create a mock user session for testing
        session["authenticated"] = True
        session["user"] = {
            "email": "admin@example.com",
            "name": "Admin User",
            "provider": "test",
            "roles": ["user_administrator", "regular_user"],
            "permissions": ["manage_secrets", "access_secrets"],
        }
        return redirect("/folders/")

    print("✅ Minimal Flask app created for folder testing")

if __name__ == "__main__":
    print("🚀 Starting Bottled Secrets development server...")
    print(f"📂 Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"🔐 Debug mode: {app.config.get('DEBUG')}")
    print("🌐 Access the application at: http://localhost:5000")
    print("📁 Folder management at: http://localhost:5000/folders/")
    print("\nPress Ctrl+C to stop the server")

    app.run(host="0.0.0.0", port=5000, debug=True)
