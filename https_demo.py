#!/usr/bin/env python3
"""Simple HTTPS demo server for testing TLS with Google SAML.

This creates a minimal Flask app that demonstrates HTTPS functionality
without the SAML authentication dependencies.
"""

import os
import ssl
from flask import (
    Flask,
    render_template_string,
    session,
    jsonify,
    request,
    redirect,
    send_from_directory,
)
from dotenv import load_dotenv
from app.models import db, Folder, Secret, FolderPermission, AccessType

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


class SimpleConfig:
    """Simple configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///instance/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True


app = Flask(__name__)
app.config.from_object(SimpleConfig)
db.init_app(app)


# Static file route for serving images
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("app/static", filename)


# Routes
@app.route("/")
def index():
    # Set up a mock user session
    session["authenticated"] = True
    session["user"] = {
        "email": "admin@example.com",
        "name": "HTTPS Demo Admin",
        "provider": "demo",
    }
    return """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }
        .header { display: flex; align-items: center; gap: 15px; margin-bottom: 30px; }
        .logo { height: 48px; width: 48px; }
        h1 { margin: 0; color: #2c3e50; }
        .status { background: #d4edda; padding: 15px; border-radius: 8px; border: 1px solid #c3e6cb; margin: 20px 0; }
    </style>
    <div class="header">
        <img src="/static/images/Bottled-Secrets.png" alt="Bottled Secrets" class="logo">
        <h1>Bottled Secrets - HTTPS Demo</h1>
    </div>
    <div class="status">
        <strong>✅ HTTPS/TLS is working!</strong><br>
        This server is now ready for Google SAML authentication.
    </div>
    <h2>🔗 SAML URLs for Google:</h2>
    <ul>
        <li><strong>ACS URL:</strong> <code>https://192.168.129.33:5000/auth/acs</code></li>
        <li><strong>Entity ID:</strong> <code>https://192.168.129.33:5000/auth/metadata</code></li>
        <li><strong>Metadata URL:</strong> <code>https://192.168.129.33:5000/auth/metadata</code></li>
    </ul>
    <br>
    <a href="/folders/">Go to Folders (HTTPS)</a>
    <br><br>
    <a href="/demo-setup">Set up demo data</a>
    <br><br>
    <a href="/test-ssl">Test SSL Certificate Info</a>
    """


@app.route("/test-ssl")
def test_ssl():
    """Display SSL certificate information."""
    return """
    <h1>🔒 SSL Certificate Information</h1>
    <p><strong>Certificate File:</strong> ./certs/cert.pem</p>
    <p><strong>Key File:</strong> ./certs/key.pem</p>
    <p><strong>Subject:</strong> CN=192.168.129.33</p>
    <p><strong>Valid for:</strong> 365 days from creation</p>
    <br>
    <p><em>Note: This is a self-signed certificate for development/testing.</em></p>
    <p><em>Browsers will show a security warning - this is expected.</em></p>
    <br>
    <a href="/">← Back to Home</a>
    """


@app.route("/auth/acs", methods=["POST"])
def saml_acs():
    """Mock SAML ACS endpoint for testing."""
    return """
    <h1>🔐 SAML ACS Endpoint (Mock)</h1>
    <p>This is where Google would POST the SAML response.</p>
    <p><strong>Method:</strong> POST</p>
    <p><strong>URL:</strong> https://192.168.129.33:5000/auth/acs</p>
    <br>
    <p>In production, this endpoint would:</p>
    <ul>
        <li>Validate the SAML response</li>
        <li>Extract user attributes</li>
        <li>Create user session</li>
        <li>Redirect to application</li>
    </ul>
    <br>
    <a href="/">← Back to Home</a>
    """


@app.route("/auth/metadata")
def saml_metadata():
    """Mock SAML metadata endpoint."""
    metadata_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="https://192.168.129.33:5000/auth/metadata">
    <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                     Location="https://192.168.129.33:5000/auth/acs"
                                     index="1"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

    return metadata_xml, 200, {"Content-Type": "application/xml"}


@app.route("/demo-setup")
def setup_demo():
    """Create some demo folders and secrets."""
    try:
        # Create demo folders if they don't exist
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

            return """
            <h2>✅ Demo data created successfully!</h2>
            <p>Created HTTPS-enabled folders and secrets for demonstration.</p>
            <a href="/folders/">View Folders (HTTPS)</a>
            """
        else:
            return """
            <h2>ℹ️ Demo data already exists</h2>
            <a href="/folders/">View Folders (HTTPS)</a>
            """

    except Exception as e:
        db.session.rollback()
        return f'<h2>❌ Error: {str(e)}</h2><a href="/">Back</a>'


@app.route("/folders/")
def folders_index():
    """Simple folders listing over HTTPS."""
    folders = Folder.query.filter_by(is_active=True).all()

    html = """
    <h1>🔒 Secret Folders (HTTPS)</h1>
    <p><strong>Secure connection established!</strong></p>
    <style>
        .folder-card {
            border: 1px solid #ccc;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            display: inline-block;
            width: 300px;
            vertical-align: top;
            background: #f9f9f9;
        }
        .folder-icon { font-size: 2em; margin-bottom: 10px; }
        .folder-path { color: #666; font-family: monospace; }
        .secret-item { background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .https-indicator { background: #d4edda; padding: 10px; margin: 10px 0; border-radius: 4px; border: 1px solid #c3e6cb; }
    </style>
    <div class="https-indicator">
        🔒 <strong>HTTPS Enabled:</strong> This connection is encrypted and ready for Google SAML
    </div>
    """

    if not folders:
        html += '<p>No folders found. <a href="/demo-setup">Create demo data</a></p>'
    else:
        for folder in folders:
            secrets = Secret.query.filter_by(folder_id=folder.id, is_active=True).all()

            icon_map = {
                "folder-prod": "🏭",
                "folder-key": "🔐",
                "folder-database": "🗃️",
                "folder": "📁",
            }
            icon = icon_map.get(folder.icon, "📁")

            html += f"""
            <div class="folder-card">
                <div class="folder-icon">{icon}</div>
                <h3>{folder.name}</h3>
                <div class="folder-path">{folder.path}</div>
                <p>{folder.description or 'No description'}</p>
                <p><strong>Created by:</strong> {folder.created_by}</p>
                <p><strong>Secrets:</strong> {len(secrets)}</p>

                <h4>🔑 Secrets:</h4>
            """

            if secrets:
                for secret in secrets:
                    html += f"""
                    <div class="secret-item">
                        <strong>{secret.name}</strong><br>
                        <small>{secret.description or 'No description'}</small><br>
                        <small>Value: {"*" * 20} (encrypted & secure)</small>
                    </div>
                    """
            else:
                html += "<p><em>No secrets in this folder</em></p>"

            html += "</div>"

    html += """
    <br><br>
    <a href="/">← Back to Home</a>
    """

    return html


def create_ssl_context():
    """Create SSL context for HTTPS."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(cert_file, key_file)
    return context


if __name__ == "__main__":
    print("🔒 Starting Bottled Secrets HTTPS Demo Server...")
    print(f"🔑 SSL Certificate: {cert_file}")
    print(f"🔑 SSL Key: {key_file}")
    print("🌐 HTTPS URLs:")
    print("   Main: https://192.168.129.33:5000")
    print("   Folders: https://192.168.129.33:5000/folders/")
    print("   ACS: https://192.168.129.33:5000/auth/acs")
    print("   Metadata: https://192.168.129.33:5000/auth/metadata")
    print("\n📋 For Google Admin Console:")
    print("   ACS URL: https://192.168.129.33:5000/auth/acs")
    print("   Entity ID: https://192.168.129.33:5000/auth/metadata")
    print("\n⚠️  Certificate Warning:")
    print("   Browsers will show SSL warnings due to self-signed certificate")
    print("   Click 'Advanced' → 'Proceed to 192.168.129.33 (unsafe)' to continue")
    print("\nPress Ctrl+C to stop the server")

    with app.app_context():
        db.create_all()

    # Create SSL context and start HTTPS server
    ssl_context = create_ssl_context()
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=ssl_context)
