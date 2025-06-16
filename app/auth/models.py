"""User authentication models for Bottled Secrets Flask application.

This module defines user models and authentication-related data structures
for managing user sessions and identity information from SAML providers.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.auth.models
.. platform:: Unix, Windows
.. synopsis:: Authentication models and user management

Example:
    Create a user from SAML attributes::

        user = User.from_saml_attributes(saml_attributes)
        user.save_to_session()
"""

from typing import Dict, Any, Optional
from datetime import datetime
from flask import session
from app.auth.roles import UserRole, UserPermissions, RoleManager

__all__ = ['User']


class User:
    """User model for authenticated users.

    This class represents an authenticated user with information obtained
    from SAML identity providers.

    :ivar email: User's email address
    :type email: str
    :ivar name: User's full name
    :type name: str
    :ivar provider: Identity provider used for authentication
    :type provider: str
    :ivar attributes: Additional SAML attributes
    :type attributes: Dict[str, Any]
    :ivar authenticated_at: Timestamp of authentication
    :type authenticated_at: datetime
    :ivar user_permissions: User roles and permissions
    :type user_permissions: UserPermissions
    """

    def __init__(
        self,
        email: str,
        name: str,
        provider: str,
        attributes: Optional[Dict[str, Any]] = None,
        roles: Optional[set] = None
    ) -> None:
        """Initialize User instance.

        :param email: User's email address
        :type email: str
        :param name: User's full name
        :type name: str
        :param provider: Identity provider ('google' or 'azure')
        :type provider: str
        :param attributes: Additional SAML attributes
        :type attributes: Optional[Dict[str, Any]]
        :param roles: Set of user roles
        :type roles: Optional[set]
        :raises ValueError: If required parameters are missing
        """
        if not email or not name:
            raise ValueError("Email and name are required")

        self.email: str = email
        self.name: str = name
        self.provider: str = provider
        self.attributes: Dict[str, Any] = attributes or {}
        self.authenticated_at: datetime = datetime.utcnow()
        
        # Initialize user permissions with default role for new users
        self.user_permissions: UserPermissions = UserPermissions()
        if roles:
            self.user_permissions.roles = set(roles)
        else:
            # Assign default role for new users
            self.user_permissions.roles.add(RoleManager.get_default_role())
        self.user_permissions._update_permissions()

    @classmethod
    def from_saml_attributes(
        cls,
        saml_attributes: Dict[str, Any],
        provider: str
    ) -> 'User':
        """Create User instance from SAML attributes.

        :param saml_attributes: Dictionary of SAML attributes
        :type saml_attributes: Dict[str, Any]
        :param provider: Identity provider name
        :type provider: str
        :returns: User instance created from SAML data
        :rtype: User
        :raises ValueError: If required SAML attributes are missing

        Example:
            Create user from Google SAML::

                user = User.from_saml_attributes(attrs, 'google')

            Create user from Azure SAML::

                user = User.from_saml_attributes(attrs, 'azure')
        """
        # Extract email from various possible attribute names
        email = (
            saml_attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress', [''])[0] or
            saml_attributes.get('email', [''])[0] or
            saml_attributes.get('mail', [''])[0] or
            saml_attributes.get('emailAddress', [''])[0]
        )

        # Extract name from various possible attribute names
        name = (
            saml_attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name', [''])[0] or
            saml_attributes.get('displayName', [''])[0] or
            saml_attributes.get('name', [''])[0] or
            saml_attributes.get('cn', [''])[0] or
            email  # Fallback to email if name not available
        )

        if not email:
            raise ValueError("Email address not found in SAML attributes")

        return cls(
            email=email,
            name=name,
            provider=provider,
            attributes=saml_attributes
        )

    def save_to_session(self) -> None:
        """Save user information to Flask session.

        Stores user data in the session for authentication persistence
        across requests.

        :raises RuntimeError: If session is not available
        """
        session['user'] = {
            'email': self.email,
            'name': self.name,
            'provider': self.provider,
            'attributes': self.attributes,
            'authenticated_at': self.authenticated_at.isoformat(),
            'roles': [role.value for role in self.user_permissions.roles],
            'permissions': [perm.value for perm in self.user_permissions.permissions]
        }
        session['authenticated'] = True

    @classmethod
    def from_session(cls) -> Optional['User']:
        """Load user from Flask session.

        :returns: User instance if authenticated, None otherwise
        :rtype: Optional[User]

        Example:
            Check if user is authenticated::

                user = User.from_session()
                if user:
                    print(f"Welcome {user.name}")
        """
        if not session.get('authenticated') or 'user' not in session:
            return None

        user_data = session['user']
        
        # Restore roles from session
        roles = set()
        if 'roles' in user_data:
            for role_value in user_data['roles']:
                try:
                    roles.add(UserRole(role_value))
                except ValueError:
                    pass  # Skip invalid roles
        
        user = cls(
            email=user_data['email'],
            name=user_data['name'],
            provider=user_data['provider'],
            attributes=user_data.get('attributes', {}),
            roles=roles
        )
        
        # Restore original authentication timestamp
        if 'authenticated_at' in user_data:
            user.authenticated_at = datetime.fromisoformat(user_data['authenticated_at'])

        return user

    @staticmethod
    def logout() -> None:
        """Clear user session and logout.

        Removes all authentication-related data from the session.
        """
        session.pop('user', None)
        session.pop('authenticated', None)
        session.clear()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        :returns: True if user is authenticated
        :rtype: bool
        """
        return True

    def get_id(self) -> str:
        """Get unique user identifier.

        :returns: User's email address as unique identifier
        :rtype: str
        """
        return self.email

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role.

        :param role: Role to check for
        :type role: UserRole
        :returns: True if user has the role
        :rtype: bool
        """
        return self.user_permissions.has_role(role)

    def has_permission(self, permission) -> bool:
        """Check if user has specific permission.

        :param permission: Permission to check for
        :returns: True if user has the permission
        :rtype: bool
        """
        return self.user_permissions.has_permission(permission)

    def assign_role(self, role: UserRole, assigned_by: str) -> None:
        """Assign role to user.

        :param role: Role to assign
        :type role: UserRole
        :param assigned_by: Email of admin assigning the role
        :type assigned_by: str
        """
        self.user_permissions.add_role(role, assigned_by)

    def remove_role(self, role: UserRole) -> None:
        """Remove role from user.

        :param role: Role to remove
        :type role: UserRole
        """
        self.user_permissions.remove_role(role)

    def get_roles(self) -> set:
        """Get all roles assigned to user.

        :returns: Set of user roles
        :rtype: set
        """
        return self.user_permissions.roles.copy()

    def is_admin(self) -> bool:
        """Check if user has administrative privileges.

        :returns: True if user is an administrator
        :rtype: bool
        """
        return self.has_role(UserRole.USER_ADMINISTRATOR)

    def __repr__(self) -> str:
        """String representation of User object.

        :returns: String representation
        :rtype: str
        """
        roles_str = ', '.join([role.value for role in self.user_permissions.roles])
        return f"<User {self.email} via {self.provider} roles=[{roles_str}]>"