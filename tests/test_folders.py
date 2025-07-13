"""Test cases for folder management functionality.

This module contains unit tests for the folder and secret management system,
including CRUD operations, access control, and hierarchical folder structure.

.. moduleauthor:: Bottled Secrets Team
.. module:: tests.test_folders
.. platform:: Unix, Windows
.. synopsis:: Folder management tests
"""

import pytest
import json
from datetime import datetime
from flask import session
from app import create_app, db
from app.models import Folder, Secret, FolderPermission, AccessType
from app.auth.models import User
from app.auth.roles import UserRole
from config.config import TestingConfig


@pytest.fixture
def app():
    """Create test Flask application."""
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return User(
        email="admin@example.com",
        name="Admin User",
        provider="google",
        roles={UserRole.USER_ADMINISTRATOR},
    )


@pytest.fixture
def regular_user():
    """Create regular user for testing."""
    return User(
        email="user@example.com",
        name="Regular User",
        provider="google",
        roles={UserRole.REGULAR_USER},
    )


@pytest.fixture
def guest_user():
    """Create guest user for testing."""
    return User(
        email="guest@example.com",
        name="Guest User",
        provider="google",
        roles={UserRole.GUEST},
    )


class TestFolderModel:
    """Test cases for Folder model."""

    def test_folder_creation(self, app):
        """Test folder creation."""
        with app.app_context():
            folder = Folder(
                name="Test Folder",
                path="/test",
                created_by="admin@example.com",
                description="Test folder description",
            )
            db.session.add(folder)
            db.session.commit()

            assert folder.id is not None
            assert folder.name == "Test Folder"
            assert folder.path == "/test"
            assert folder.created_by == "admin@example.com"
            assert folder.description == "Test folder description"
            assert folder.icon == "folder"
            assert folder.is_active is True

    def test_folder_validation(self, app):
        """Test folder validation."""
        with app.app_context():
            # Test missing required fields
            with pytest.raises(ValueError):
                Folder(name="", path="/test", created_by="admin@example.com")

            with pytest.raises(ValueError):
                Folder(name="Test", path="", created_by="admin@example.com")

            with pytest.raises(ValueError):
                Folder(name="Test", path="/test", created_by="")

            # Test invalid path
            with pytest.raises(ValueError):
                Folder(name="Test", path="test", created_by="admin@example.com")

    def test_folder_hierarchy(self, app):
        """Test folder parent-child relationships."""
        with app.app_context():
            parent = Folder(
                name="Parent", path="/parent", created_by="admin@example.com"
            )
            db.session.add(parent)
            db.session.commit()

            child = Folder(
                name="Child",
                path="/parent/child",
                created_by="admin@example.com",
                parent_id=parent.id,
            )
            db.session.add(child)
            db.session.commit()

            assert child.parent_id == parent.id
            assert child.parent == parent
            assert child in parent.children

    def test_folder_access_control(self, app):
        """Test folder access control methods."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by="admin@example.com"
            )
            db.session.add(folder)
            db.session.commit()

            # Creator should have admin access
            assert folder.has_access("admin@example.com", AccessType.READ)
            assert folder.has_access("admin@example.com", AccessType.WRITE)
            assert folder.has_access("admin@example.com", AccessType.ADMIN)

            # Other users should not have access
            assert not folder.has_access("user@example.com", AccessType.READ)

            # Grant read access to user
            folder.grant_access(
                "user@example.com", AccessType.READ, "admin@example.com"
            )
            db.session.commit()

            assert folder.has_access("user@example.com", AccessType.READ)
            assert not folder.has_access("user@example.com", AccessType.WRITE)
            assert not folder.has_access("user@example.com", AccessType.ADMIN)


class TestSecretModel:
    """Test cases for Secret model."""

    def test_secret_creation(self, app):
        """Test secret creation and encryption."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by="admin@example.com"
            )
            db.session.add(folder)
            db.session.commit()

            secret = Secret(
                name="test_secret",
                value="secret_value",
                folder_id=folder.id,
                created_by="admin@example.com",
                description="Test secret",
            )
            db.session.add(secret)
            db.session.commit()

            assert secret.id is not None
            assert secret.name == "test_secret"
            assert secret.folder_id == folder.id
            assert secret.created_by == "admin@example.com"
            assert secret.description == "Test secret"
            assert secret.is_active is True

            # Value should be encrypted
            assert secret.encrypted_value != "secret_value"

            # But decryption should work
            assert secret.get_value() == "secret_value"

    def test_secret_validation(self, app):
        """Test secret validation."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by="admin@example.com"
            )
            db.session.add(folder)
            db.session.commit()

            # Test missing required fields
            with pytest.raises(ValueError):
                Secret(
                    name="",
                    value="secret",
                    folder_id=folder.id,
                    created_by="admin@example.com",
                )

            with pytest.raises(ValueError):
                Secret(
                    name="test",
                    value="",
                    folder_id=folder.id,
                    created_by="admin@example.com",
                )

            with pytest.raises(ValueError):
                Secret(
                    name="test",
                    value="secret",
                    folder_id=None,
                    created_by="admin@example.com",
                )

            with pytest.raises(ValueError):
                Secret(name="test", value="secret", folder_id=folder.id, created_by="")

    def test_secret_value_update(self, app):
        """Test updating secret values."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by="admin@example.com"
            )
            db.session.add(folder)
            db.session.commit()

            secret = Secret(
                name="test_secret",
                value="original_value",
                folder_id=folder.id,
                created_by="admin@example.com",
            )
            db.session.add(secret)
            db.session.commit()

            original_updated_at = secret.updated_at

            # Update value
            secret.set_value("new_value")

            assert secret.get_value() == "new_value"
            assert secret.updated_at > original_updated_at


class TestFolderPermission:
    """Test cases for FolderPermission model."""

    def test_permission_creation(self, app):
        """Test permission creation."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by="admin@example.com"
            )
            db.session.add(folder)
            db.session.commit()

            permission = FolderPermission(
                folder_id=folder.id,
                user_email="user@example.com",
                granted_by="admin@example.com",
                can_read=True,
                can_write=True,
                can_admin=False,
            )
            db.session.add(permission)
            db.session.commit()

            assert permission.id is not None
            assert permission.folder_id == folder.id
            assert permission.user_email == "user@example.com"
            assert permission.granted_by == "admin@example.com"
            assert permission.can_read is True
            assert permission.can_write is True
            assert permission.can_admin is False
            assert permission.get_access_level() == "Read/Write"

    def test_access_level_descriptions(self, app):
        """Test access level descriptions."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by="admin@example.com"
            )
            db.session.add(folder)
            db.session.commit()

            # Read only
            read_only = FolderPermission(
                folder_id=folder.id,
                user_email="user1@example.com",
                granted_by="admin@example.com",
                can_read=True,
                can_write=False,
                can_admin=False,
            )
            assert read_only.get_access_level() == "Read Only"

            # Read/Write
            read_write = FolderPermission(
                folder_id=folder.id,
                user_email="user2@example.com",
                granted_by="admin@example.com",
                can_read=True,
                can_write=True,
                can_admin=False,
            )
            assert read_write.get_access_level() == "Read/Write"

            # Admin
            admin = FolderPermission(
                folder_id=folder.id,
                user_email="user3@example.com",
                granted_by="admin@example.com",
                can_read=True,
                can_write=True,
                can_admin=True,
            )
            assert admin.get_access_level() == "Admin"

            # No access
            no_access = FolderPermission(
                folder_id=folder.id,
                user_email="user4@example.com",
                granted_by="admin@example.com",
                can_read=False,
                can_write=False,
                can_admin=False,
            )
            assert no_access.get_access_level() == "No Access"


class TestFolderRoutes:
    """Test cases for folder routes."""

    def authenticate_user(self, client, user):
        """Helper to authenticate a user in test session."""
        with client.session_transaction() as sess:
            user.save_to_session()

    def test_folder_index_unauthenticated(self, client):
        """Test folder index redirects when unauthenticated."""
        response = client.get("/folders/")
        assert response.status_code == 302  # Redirect to login

    def test_folder_index_authenticated(self, client, app, regular_user):
        """Test folder index for authenticated user."""
        with app.app_context():
            self.authenticate_user(client, regular_user)
            response = client.get("/folders/")
            assert response.status_code == 200
            assert b"Secret Folders" in response.data

    def test_api_list_folders_unauthorized(self, client):
        """Test API list folders without authentication."""
        response = client.get("/folders/api/folders")
        assert response.status_code == 401

    def test_api_list_folders_guest_forbidden(self, client, app, guest_user):
        """Test API list folders with guest user (no permissions)."""
        with app.app_context():
            self.authenticate_user(client, guest_user)
            response = client.get("/folders/api/folders")
            assert response.status_code == 403

    def test_api_list_folders_authorized(self, client, app, regular_user):
        """Test API list folders with authorized user."""
        with app.app_context():
            # Create a test folder
            folder = Folder(
                name="Test Folder", path="/test", created_by=regular_user.email
            )
            db.session.add(folder)
            db.session.commit()

            self.authenticate_user(client, regular_user)
            response = client.get("/folders/api/folders")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "folders" in data
            assert len(data["folders"]) == 1
            assert data["folders"][0]["name"] == "Test Folder"

    def test_api_create_folder_success(self, client, app, regular_user):
        """Test successful folder creation via API."""
        with app.app_context():
            self.authenticate_user(client, regular_user)

            folder_data = {
                "name": "New Folder",
                "path": "/new-folder",
                "icon": "folder-key",
                "description": "A new test folder",
            }

            response = client.post(
                "/folders/api/folders",
                data=json.dumps(folder_data),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["name"] == "New Folder"
            assert data["path"] == "/new-folder"
            assert data["created_by"] == regular_user.email

            # Verify folder was created in database
            folder = Folder.query.filter_by(path="/new-folder").first()
            assert folder is not None
            assert folder.name == "New Folder"

    def test_api_create_folder_validation_errors(self, client, app, regular_user):
        """Test folder creation validation errors."""
        with app.app_context():
            self.authenticate_user(client, regular_user)

            # Missing name
            response = client.post(
                "/folders/api/folders",
                data=json.dumps({"path": "/test"}),
                content_type="application/json",
            )
            assert response.status_code == 400

            # Missing path
            response = client.post(
                "/folders/api/folders",
                data=json.dumps({"name": "Test"}),
                content_type="application/json",
            )
            assert response.status_code == 400

            # Invalid path (doesn't start with /)
            response = client.post(
                "/folders/api/folders",
                data=json.dumps({"name": "Test", "path": "invalid"}),
                content_type="application/json",
            )
            assert response.status_code == 400

    def test_api_create_folder_duplicate_path(self, client, app, regular_user):
        """Test folder creation with duplicate path."""
        with app.app_context():
            # Create existing folder
            existing_folder = Folder(
                name="Existing", path="/test", created_by=regular_user.email
            )
            db.session.add(existing_folder)
            db.session.commit()

            self.authenticate_user(client, regular_user)

            folder_data = {
                "name": "New Folder",
                "path": "/test",  # Same path as existing folder
            }

            response = client.post(
                "/folders/api/folders",
                data=json.dumps(folder_data),
                content_type="application/json",
            )

            assert response.status_code == 409  # Conflict
            data = json.loads(response.data)
            assert "already exists" in data["error"]

    def test_api_get_folder_details(self, client, app, regular_user):
        """Test getting folder details via API."""
        with app.app_context():
            # Create folder with secrets
            folder = Folder(
                name="Test Folder", path="/test", created_by=regular_user.email
            )
            db.session.add(folder)
            db.session.commit()

            secret = Secret(
                name="test_secret",
                value="secret_value",
                folder_id=folder.id,
                created_by=regular_user.email,
            )
            db.session.add(secret)
            db.session.commit()

            self.authenticate_user(client, regular_user)

            response = client.get(f"/folders/api/folders/{folder.id}")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["name"] == "Test Folder"
            assert data["path"] == "/test"
            assert len(data["secrets"]) == 1
            assert data["secrets"][0]["name"] == "test_secret"

    def test_api_create_secret_success(self, client, app, regular_user):
        """Test successful secret creation via API."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by=regular_user.email
            )
            db.session.add(folder)
            db.session.commit()

            self.authenticate_user(client, regular_user)

            secret_data = {
                "name": "api_key",
                "value": "secret123",
                "description": "API key for service",
            }

            response = client.post(
                f"/folders/api/folders/{folder.id}/secrets",
                data=json.dumps(secret_data),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["name"] == "api_key"
            assert data["folder_id"] == folder.id

            # Verify secret was created and encrypted
            secret = Secret.query.filter_by(name="api_key").first()
            assert secret is not None
            assert secret.get_value() == "secret123"
            assert secret.encrypted_value != "secret123"

    def test_api_grant_permission_success(self, client, app, admin_user):
        """Test successful permission granting via API."""
        with app.app_context():
            folder = Folder(
                name="Test Folder", path="/test", created_by=admin_user.email
            )
            db.session.add(folder)
            db.session.commit()

            self.authenticate_user(client, admin_user)

            permission_data = {"user_email": "user@example.com", "access_type": "write"}

            response = client.post(
                f"/folders/api/folders/{folder.id}/permissions",
                data=json.dumps(permission_data),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "access granted" in data["message"]

            # Verify permission was created
            permission = FolderPermission.query.filter_by(
                folder_id=folder.id, user_email="user@example.com"
            ).first()
            assert permission is not None
            assert permission.can_read is True
            assert permission.can_write is True
            assert permission.can_admin is False


if __name__ == "__main__":
    pytest.main([__file__])
