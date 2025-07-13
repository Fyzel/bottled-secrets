#!/usr/bin/env python3
"""HTTPS-enabled server for Bottled Secrets with TLS support.

This script starts the Flask development server with HTTPS/TLS encryption
for Google SAML authentication compatibility.
"""

import os
import ssl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check SSL certificate files
cert_file = "./certs/cert.pem"
key_file = "./certs/key.pem"

if not os.path.exists(cert_file) or not os.path.exists(key_file):
    print(f"❌ SSL certificate files not found!")
    print(f"   Expected: {cert_file}")
    print(f"   Expected: {key_file}")
    exit(1)

# Try to import the full application first
try:
    from app import create_app

    app = create_app()
    print("✅ Full application loaded successfully")
except Exception as e:
    print(f"⚠️  SAML import issue detected: {e}")
    print("🔄 Creating minimal Flask app for HTTPS testing...")

    # Create a minimal Flask app with just the folder system
    from flask import Flask, session, redirect, url_for, send_from_directory
    from app.models import db
    from app.folders import bp as folders_bp
    from config.config import DevelopmentConfig

    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # Initialize database
    db.init_app(app)

    # Register only the folders blueprint
    app.register_blueprint(folders_bp, url_prefix="/folders")

    # Static file route for serving images
    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory("app/static", filename)

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

    print("✅ Minimal Flask app created for HTTPS testing")


def create_ssl_context():
    """Create SSL context for HTTPS."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(cert_file, key_file)
    return context


if __name__ == "__main__":
    print("🔒 Starting Bottled Secrets HTTPS server...")
    print(f"📂 Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"🔐 Debug mode: {app.config.get('DEBUG')}")
    print(f"🔑 SSL Certificate: {cert_file}")
    print(f"🔑 SSL Key: {key_file}")
    print("🌐 HTTPS URLs:")
    print("   Main: https://192.168.129.33:5000")
    print("   Folders: https://192.168.129.33:5000/folders/")
    print("   ACS: https://192.168.129.33:5000/auth/acs")
    print("   Metadata: https://192.168.129.33:5000/auth/metadata")
    print(
        "\n⚠️  Note: You'll see SSL warnings in browser due to self-signed certificate"
    )
    print("   Click 'Advanced' → 'Proceed to 192.168.129.33 (unsafe)' to continue")
    print("\nPress Ctrl+C to stop the server")

    # Create SSL context
    ssl_context = create_ssl_context()

    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=ssl_context)
