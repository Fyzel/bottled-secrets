#!/usr/bin/env python3
"""Simple demonstration of the folder management system working.

This creates a minimal Flask app that demonstrates the folder functionality
without the SAML authentication dependencies.
"""

import os
from flask import Flask, render_template_string, session, jsonify, request, redirect
from dotenv import load_dotenv
from app.models import db, Folder, Secret, FolderPermission, AccessType

# Load environment variables
load_dotenv()


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


# Simple User class for demo
class MockUser:
    def __init__(self, email, name, roles=None):
        self.email = email
        self.name = name
        self.roles = roles or ["regular_user"]

    def has_role(self, role):
        return role in self.roles

    def has_permission(self, permission):
        return "manage_secrets" in self.roles or permission in ["access_secrets"]


# Routes
@app.route("/")
def index():
    # Set up a mock user session
    session["authenticated"] = True
    session["user"] = {
        "email": "admin@example.com",
        "name": "Demo Admin",
        "provider": "demo",
    }
    return """
    <h1>🗂️ Bottled Secrets - Folder Management Demo</h1>
    <p>Welcome to the folder management system!</p>
    <a href="/folders/">Go to Folders</a>
    <br><br>
    <a href="/demo-setup">Set up demo data</a>
    """


@app.route("/demo-setup")
def setup_demo():
    """Create some demo folders and secrets."""
    try:
        # Create demo folders
        production = Folder(
            name="Production",
            path="/production",
            created_by="admin@example.com",
            icon="folder-prod",
            description="Production environment secrets",
        )
        db.session.add(production)
        db.session.flush()  # Get the ID

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

        database = Folder(
            name="Database",
            path="/production/database",
            created_by="admin@example.com",
            parent_id=production.id,
            icon="folder-database",
            description="Database credentials",
        )
        db.session.add(database)
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
                name="sendgrid_key",
                value="SG.example123456789",
                folder_id=api_keys.id,
                created_by="admin@example.com",
                description="Email service API key",
            ),
            Secret(
                name="database_url",
                value="postgresql://user:pass@prod-db:5432/app",
                folder_id=database.id,
                created_by="admin@example.com",
                description="Main database connection",
            ),
        ]

        for secret in secrets:
            db.session.add(secret)

        db.session.commit()

        return """
        <h2>✅ Demo data created successfully!</h2>
        <p>Created folders and secrets for demonstration.</p>
        <a href="/folders/">View Folders</a>
        """

    except Exception as e:
        db.session.rollback()
        return f'<h2>❌ Error: {str(e)}</h2><a href="/">Back</a>'


@app.route("/folders/")
def folders_index():
    """Simple folders listing."""
    folders = Folder.query.filter_by(is_active=True).all()

    html = """
    <h1>📁 Secret Folders</h1>
    <style>
        .folder-card {
            border: 1px solid #ccc;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            display: inline-block;
            width: 300px;
            vertical-align: top;
        }
        .folder-icon { font-size: 2em; margin-bottom: 10px; }
        .folder-path { color: #666; font-family: monospace; }
        .secret-item { background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 4px; }
    </style>
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
                        <small>Value: {"*" * 20} (encrypted)</small>
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


if __name__ == "__main__":
    print("🚀 Starting Bottled Secrets Demo Server...")
    print("🌐 Access at: http://localhost:5000")
    print("📁 Folders at: http://localhost:5000/folders/")
    print("⚙️  Demo setup at: http://localhost:5000/demo-setup")

    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
