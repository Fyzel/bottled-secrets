"""Database models for Bottled Secrets Flask application.

This module defines SQLAlchemy models for folders, secrets, and access permissions
with hierarchical folder structure and role-based access control.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.models
.. platform:: Unix, Windows
.. synopsis:: Database models for folders and secrets management

Example:
    Create a folder with secrets::

        folder = Folder(name="API Keys", path="/production/api-keys", created_by="admin@example.com")
        secret = Secret(name="stripe_key", value="sk_live_...", folder=folder)
        db.session.add_all([folder, secret])
        db.session.commit()
"""

import os
import base64
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet

__all__ = ["db", "Folder", "Secret", "FolderPermission", "AccessType"]

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association table for folder permissions (many-to-many)
folder_permissions = Table(
    "folder_permissions",
    db.Model.metadata,
    Column("folder_id", Integer, ForeignKey("folders.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class AccessType(Enum):
    """Access types for folder permissions."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Folder(db.Model):
    """Folder model for organizing secrets in hierarchical structure.

    Folders can contain secrets and other folders, forming a tree structure.
    Each folder has access permissions that control user access.

    :ivar id: Primary key
    :type id: int
    :ivar name: Folder display name
    :type name: str
    :ivar path: Full hierarchical path (e.g., "/production/api-keys")
    :type path: str
    :ivar icon: Icon identifier for UI display
    :type icon: str
    :ivar description: Optional folder description
    :type description: str
    :ivar created_by: Email of user who created the folder
    :type created_by: str
    :ivar created_at: Timestamp when folder was created
    :type created_at: datetime
    :ivar updated_at: Timestamp when folder was last modified
    :type updated_at: datetime
    :ivar parent_id: ID of parent folder (None for root folders)
    :type parent_id: int
    :ivar is_active: Whether folder is active or archived
    :type is_active: bool
    """

    __tablename__ = "folders"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    path = Column(String(1000), nullable=False, unique=True)
    icon = Column(String(50), nullable=False, default="folder")
    description = Column(Text)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    parent_id = Column(Integer, ForeignKey("folders.id"))
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    parent = relationship("Folder", remote_side=[id], backref="children")
    secrets = relationship(
        "Secret", back_populates="folder", cascade="all, delete-orphan"
    )
    permissions = relationship(
        "FolderPermission", back_populates="folder", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        name: str,
        path: str,
        created_by: str,
        icon: str = "folder",
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
    ):
        """Initialize Folder instance.

        :param name: Folder display name
        :type name: str
        :param path: Full hierarchical path
        :type path: str
        :param created_by: Email of user creating the folder
        :type created_by: str
        :param icon: Icon identifier for UI display
        :type icon: str
        :param description: Optional folder description
        :type description: Optional[str]
        :param parent_id: ID of parent folder
        :type parent_id: Optional[int]
        :raises ValueError: If required parameters are missing or invalid
        """
        if not name or not path or not created_by:
            raise ValueError("Name, path, and created_by are required")

        if not path.startswith("/"):
            raise ValueError("Path must start with '/'")

        self.name = name
        self.path = path
        self.created_by = created_by
        self.icon = icon
        self.description = description
        self.parent_id = parent_id

    def get_full_path(self) -> str:
        """Get the full hierarchical path of the folder.

        :returns: Full path string
        :rtype: str
        """
        return self.path

    def get_children(self) -> List["Folder"]:
        """Get all child folders.

        :returns: List of child folders
        :rtype: List[Folder]
        """
        return [child for child in self.children if child.is_active]

    def get_secrets(self) -> List["Secret"]:
        """Get all secrets in this folder.

        :returns: List of secrets
        :rtype: List[Secret]
        """
        return [secret for secret in self.secrets if secret.is_active]

    def has_access(self, user_email: str, access_type: AccessType) -> bool:
        """Check if user has specific access to this folder.

        :param user_email: User's email address
        :type user_email: str
        :param access_type: Type of access to check
        :type access_type: AccessType
        :returns: True if user has access
        :rtype: bool
        """
        # Creator always has admin access
        if self.created_by == user_email:
            return True

        # Check explicit permissions
        for permission in self.permissions:
            if permission.user_email == user_email:
                if access_type == AccessType.READ:
                    return permission.can_read
                elif access_type == AccessType.WRITE:
                    return permission.can_write
                elif access_type == AccessType.ADMIN:
                    return permission.can_admin

        return False

    def grant_access(
        self, user_email: str, access_type: AccessType, granted_by: str
    ) -> None:
        """Grant access to user for this folder.

        :param user_email: User's email address
        :type user_email: str
        :param access_type: Type of access to grant
        :type access_type: AccessType
        :param granted_by: Email of user granting access
        :type granted_by: str
        """
        permission = next(
            (p for p in self.permissions if p.user_email == user_email), None
        )

        if not permission:
            permission = FolderPermission(
                folder_id=self.id, user_email=user_email, granted_by=granted_by
            )
            self.permissions.append(permission)

        if access_type == AccessType.READ:
            permission.can_read = True
        elif access_type == AccessType.WRITE:
            permission.can_read = True
            permission.can_write = True
        elif access_type == AccessType.ADMIN:
            permission.can_read = True
            permission.can_write = True
            permission.can_admin = True

    def __repr__(self) -> str:
        """String representation of Folder object.

        :returns: String representation
        :rtype: str
        """
        return f"<Folder {self.path} created_by={self.created_by}>"


class Secret(db.Model):
    """Secret model for storing encrypted secret values within folders.

    Secrets are encrypted at rest and associated with folders for organization
    and access control.

    :ivar id: Primary key
    :type id: int
    :ivar name: Secret name/key
    :type name: str
    :ivar encrypted_value: Encrypted secret value
    :type encrypted_value: str
    :ivar description: Optional secret description
    :type description: str
    :ivar folder_id: ID of containing folder
    :type folder_id: int
    :ivar created_by: Email of user who created the secret
    :type created_by: str
    :ivar created_at: Timestamp when secret was created
    :type created_at: datetime
    :ivar updated_at: Timestamp when secret was last modified
    :type updated_at: datetime
    :ivar is_active: Whether secret is active or archived
    :type is_active: bool
    """

    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    encrypted_value = Column(Text, nullable=False)
    description = Column(Text)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    folder = relationship("Folder", back_populates="secrets")

    def __init__(
        self,
        name: str,
        value: str,
        folder_id: int,
        created_by: str,
        description: Optional[str] = None,
    ):
        """Initialize Secret instance.

        :param name: Secret name/key
        :type name: str
        :param value: Plain text secret value (will be encrypted)
        :type value: str
        :param folder_id: ID of containing folder
        :type folder_id: int
        :param created_by: Email of user creating the secret
        :type created_by: str
        :param description: Optional secret description
        :type description: Optional[str]
        :raises ValueError: If required parameters are missing
        """
        if not name or not value or not folder_id or not created_by:
            raise ValueError("Name, value, folder_id, and created_by are required")

        self.name = name
        self.encrypted_value = self._encrypt_value(value)
        self.folder_id = folder_id
        self.created_by = created_by
        self.description = description

    def _encrypt_value(self, value: str) -> str:
        """Encrypt a secret value.

        :param value: Plain text value to encrypt
        :type value: str
        :returns: Encrypted value as base64 string
        :rtype: str
        """
        key = self._get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted_bytes).decode()

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a secret value.

        :param encrypted_value: Encrypted value as base64 string
        :type encrypted_value: str
        :returns: Decrypted plain text value
        :rtype: str
        """
        key = self._get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_value.encode())
        return fernet.decrypt(encrypted_bytes).decode()

    def _get_encryption_key(self) -> bytes:
        """Get encryption key from environment or generate one.

        :returns: Encryption key
        :rtype: bytes
        """
        key_string = os.environ.get("SECRETS_ENCRYPTION_KEY")
        if not key_string:
            # Generate a key if not provided (development only)
            key_string = base64.urlsafe_b64encode(os.urandom(32)).decode()

        return key_string.encode()

    def get_value(self) -> str:
        """Get decrypted secret value.

        :returns: Decrypted secret value
        :rtype: str
        """
        return self._decrypt_value(self.encrypted_value)

    def set_value(self, value: str) -> None:
        """Set secret value (will be encrypted).

        :param value: New plain text value
        :type value: str
        """
        self.encrypted_value = self._encrypt_value(value)
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation of Secret object.

        :returns: String representation
        :rtype: str
        """
        return f"<Secret {self.name} in folder_id={self.folder_id}>"


class FolderPermission(db.Model):
    """Permission model for folder access control.

    Defines what level of access specific users have to folders.

    :ivar id: Primary key
    :type id: int
    :ivar folder_id: ID of the folder
    :type folder_id: int
    :ivar user_email: Email of user with permission
    :type user_email: str
    :ivar can_read: Whether user can read folder contents
    :type can_read: bool
    :ivar can_write: Whether user can modify folder contents
    :type can_write: bool
    :ivar can_admin: Whether user can manage folder permissions
    :type can_admin: bool
    :ivar granted_by: Email of user who granted the permission
    :type granted_by: str
    :ivar granted_at: Timestamp when permission was granted
    :type granted_at: datetime
    """

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False)
    user_email = Column(String(255), nullable=False)
    can_read = Column(Boolean, nullable=False, default=True)
    can_write = Column(Boolean, nullable=False, default=False)
    can_admin = Column(Boolean, nullable=False, default=False)
    granted_by = Column(String(255), nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    folder = relationship("Folder", back_populates="permissions")

    def __init__(
        self,
        folder_id: int,
        user_email: str,
        granted_by: str,
        can_read: bool = True,
        can_write: bool = False,
        can_admin: bool = False,
    ):
        """Initialize FolderPermission instance.

        :param folder_id: ID of the folder
        :type folder_id: int
        :param user_email: Email of user with permission
        :type user_email: str
        :param granted_by: Email of user granting permission
        :type granted_by: str
        :param can_read: Whether user can read folder contents
        :type can_read: bool
        :param can_write: Whether user can modify folder contents
        :type can_write: bool
        :param can_admin: Whether user can manage folder permissions
        :type can_admin: bool
        """
        self.folder_id = folder_id
        self.user_email = user_email
        self.granted_by = granted_by
        self.can_read = can_read
        self.can_write = can_write
        self.can_admin = can_admin

    def get_access_level(self) -> str:
        """Get human-readable access level.

        :returns: Access level description
        :rtype: str
        """
        if self.can_admin:
            return "Admin"
        elif self.can_write:
            return "Read/Write"
        elif self.can_read:
            return "Read Only"
        else:
            return "No Access"

    def __repr__(self) -> str:
        """String representation of FolderPermission object.

        :returns: String representation
        :rtype: str
        """
        return f"<FolderPermission user={self.user_email} folder_id={self.folder_id} level={self.get_access_level()}>"
