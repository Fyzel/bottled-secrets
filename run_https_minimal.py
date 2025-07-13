#!/usr/bin/env python3
"""Minimal HTTPS-enabled server for Bottled Secrets with TLS support.

This script starts a minimal Flask server with HTTPS/TLS encryption
that avoids ALL SAML-related imports, providing just the folder system.
"""

import os
import ssl
from flask import (
    Flask,
    session,
    redirect,
    url_for,
    send_from_directory,
    render_template,
)
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


# Simple configuration without SAML dependencies
class MinimalConfig:
    """Minimal configuration for HTTPS testing."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-for-testing"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///instance/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True


# Create minimal Flask app
app = Flask(__name__)
app.config.from_object(MinimalConfig)

# Import database models directly (avoiding auth imports)
from app.models import db, Folder, Secret

# Initialize database
db.init_app(app)


# Static file route for serving images and CSS
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("app/static", filename)


# Home route with logo
@app.route("/")
def index():
    # Create a mock user session for testing
    session["authenticated"] = True
    session["user"] = {
        "email": "admin@example.com",
        "name": "HTTPS Test User",
        "provider": "test",
        "roles": ["user_administrator", "regular_user"],
        "permissions": ["manage_secrets", "access_secrets"],
    }

    return render_template_string(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bottled Secrets - HTTPS Test</title>
        <link rel="icon" type="image/png" href="/static/images/Bottled-Secrets.png">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }
            .header {
                background: #2c3e50;
                color: white;
                padding: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .logo {
                height: 48px;
                width: 48px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            .hero {
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 80px 20px;
                margin: -20px -20px 40px -20px;
                border-radius: 12px;
            }
            .hero-logo {
                height: 120px;
                width: 120px;
                margin: 0 auto 30px;
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            }
            .hero h1 {
                font-size: 3rem;
                margin-bottom: 20px;
                font-weight: 300;
            }
            .hero p {
                font-size: 1.25rem;
                margin-bottom: 40px;
                opacity: 0.9;
            }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                background: #27ae60;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 1.1rem;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #219a52;
            }
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .status-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .status-success {
                border-left: 4px solid #27ae60;
            }
            .status-info {
                border-left: 4px solid #3498db;
            }
            .urls {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                font-family: monospace;
                font-size: 0.9rem;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <img src="/static/images/Bottled-Secrets.png" alt="Bottled Secrets" class="logo">
            <h1>Bottled Secrets - HTTPS Test Server</h1>
        </div>

        <div class="container">
            <div class="hero">
                <img src="/static/images/Bottled-Secrets.png" alt="Bottled Secrets" class="hero-logo">
                <h1>🔒 HTTPS Enabled!</h1>
                <p>Your Bottled Secrets server is running securely with TLS encryption</p>
                <a href="/folders" class="btn">Access Folders</a>
            </div>

            <div class="status-grid">
                <div class="status-card status-success">
                    <h3>✅ HTTPS Status</h3>
                    <p>SSL/TLS encryption is active and working properly</p>
                    <p><strong>Certificate:</strong> Self-signed (development)</p>
                    <p><strong>Protocol:</strong> TLS 1.2+</p>
                </div>

                <div class="status-card status-info">
                    <h3>🔗 SAML URLs for Google</h3>
                    <p>Configure these URLs in Google Admin Console:</p>
                    <div class="urls">
                        <strong>ACS URL:</strong><br>
                        https://192.168.129.33:5000/auth/acs<br><br>
                        <strong>Entity ID:</strong><br>
                        https://192.168.129.33:5000/auth/metadata
                    </div>
                </div>

                <div class="status-card status-info">
                    <h3>🧪 Test Features</h3>
                    <ul>
                        <li>✅ Folder management system</li>
                        <li>✅ SSL/TLS encryption</li>
                        <li>✅ Static file serving</li>
                        <li>✅ Database connectivity</li>
                        <li>⚠️ SAML auth (bypassed for testing)</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    )


# Simple folders route that shows basic folder listing
@app.route("/folders")
def folders():
    try:
        folders = Folder.query.filter_by(is_active=True).all()

        folder_list = ""
        for folder in folders:
            secrets = Secret.query.filter_by(folder_id=folder.id, is_active=True).all()
            folder_list += f"""
            <div class="folder-card">
                <h3>📁 {folder.name}</h3>
                <p><strong>Path:</strong> {folder.path}</p>
                <p><strong>Created by:</strong> {folder.created_by}</p>
                <p><strong>Secrets:</strong> {len(secrets)}</p>
                <p>{folder.description or 'No description'}</p>
            </div>
            """

        if not folder_list:
            folder_list = (
                '<p>No folders found. <a href="/demo-setup">Create demo data</a></p>'
            )

    except Exception as e:
        folder_list = f"<p>Database error: {str(e)}</p>"

    return render_template_string(
        f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Folders - Bottled Secrets</title>
        <link rel="icon" type="image/png" href="/static/images/Bottled-Secrets.png">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                padding: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            .logo {{
                height: 32px;
                width: 32px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            .folder-card {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #3498db;
            }}
            .back-link {{
                display: inline-block;
                margin-bottom: 20px;
                color: #3498db;
                text-decoration: none;
            }}
            .back-link:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="/static/images/Bottled-Secrets.png" alt="Bottled Secrets" class="logo">
            <h1>Secret Folders</h1>
        </div>

        <div class="container">
            <a href="/" class="back-link">← Back to Home</a>
            <h2>🔐 Your Secret Folders</h2>
            {folder_list}
        </div>
    </body>
    </html>
    """
    )


# Demo setup route
@app.route("/demo-setup")
def setup_demo():
    """Create demo folders if they don't exist."""
    try:
        if Folder.query.count() == 0:
            production = Folder(
                name="Production",
                path="/production",
                created_by="admin@example.com",
                icon="folder-prod",
                description="Production environment secrets",
            )
            db.session.add(production)
            db.session.flush()

            api_keys = Folder(
                name="API Keys",
                path="/production/api-keys",
                created_by="admin@example.com",
                parent_id=production.id,
                icon="folder-key",
                description="External service API keys",
            )
            db.session.add(api_keys)
            db.session.flush()

            # Create demo secrets
            secrets = [
                Secret(
                    name="stripe_api_key",
                    value="sk_live_example123456789",
                    folder_id=api_keys.id,
                    created_by="admin@example.com",
                    description="Stripe payment processing",
                ),
                Secret(
                    name="google_oauth_secret",
                    value="GOCSPX-example123456789",
                    folder_id=api_keys.id,
                    created_by="admin@example.com",
                    description="Google OAuth client secret",
                ),
            ]

            for secret in secrets:
                db.session.add(secret)

            db.session.commit()
            return '<h2>✅ Demo data created!</h2><a href="/folders">View Folders</a>'
        else:
            return (
                '<h2>ℹ️ Demo data already exists</h2><a href="/folders">View Folders</a>'
            )

    except Exception as e:
        db.session.rollback()
        return f'<h2>❌ Error: {str(e)}</h2><a href="/">Back</a>'


def create_ssl_context():
    """Create SSL context for HTTPS."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(cert_file, key_file)
    return context


if __name__ == "__main__":
    print("🔒 Starting Bottled Secrets Minimal HTTPS Server...")
    print(f"📂 Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"🔐 Debug mode: {app.config.get('DEBUG')}")
    print(f"🔑 SSL Certificate: {cert_file}")
    print(f"🔑 SSL Key: {key_file}")
    print("🌐 HTTPS URLs:")
    print("   Main: https://192.168.129.33:5000")
    print("   Folders: https://192.168.129.33:5000/folders")
    print("   Demo Setup: https://192.168.129.33:5000/demo-setup")
    print("\n📋 For Google Admin Console:")
    print("   ACS URL: https://192.168.129.33:5000/auth/acs")
    print("   Entity ID: https://192.168.129.33:5000/auth/metadata")
    print("\n⚠️  Note: Browser will show SSL warnings due to self-signed certificate")
    print("   Click 'Advanced' → 'Proceed to 192.168.129.33 (unsafe)' to continue")
    print("\n🚀 This minimal server avoids ALL SAML imports for testing")
    print("Press Ctrl+C to stop the server")

    # Create SSL context
    ssl_context = create_ssl_context()

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=ssl_context)
