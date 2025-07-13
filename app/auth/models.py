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

__all__ = ["User"]


class User:
    """User model for authenticated users.

    This class represents an authenticated user with information obtained
    from SAML identity providers.

    :ivar email: User's email address
    :type email: str
    :ivar name: User's full name
    :type name: str
    :ivar first_name: User's first name
    :type first_name: str
    :ivar last_name: User's last name
    :type last_name: str
    :ivar department: User's department/organizational unit
    :type department: str
    :ivar job_title: User's job title
    :type job_title: str
    :ivar phone: User's phone number
    :type phone: str
    :ivar employee_id: User's employee ID
    :type employee_id: str
    :ivar groups: User's group memberships
    :type groups: List[str]
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
        roles: Optional[set] = None,
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

        # Extract Google IdP attributes if available
        self._extract_google_attributes()

        # Initialize user permissions with default role for new users
        self.user_permissions: UserPermissions = UserPermissions()
        if roles:
            self.user_permissions.roles = set(roles)
        else:
            # Assign default role for new users
            self.user_permissions.roles.add(RoleManager.get_default_role())
        self.user_permissions._update_permissions()

    def _extract_google_attributes(self) -> None:
        """Extract Google-specific attributes from SAML attributes."""
        if self.provider == "google":
            # Extract first name
            self.first_name = (
                self.attributes.get("first_name", [""])[0]
                or self.attributes.get("firstName", [""])[0]
                or self.attributes.get("givenName", [""])[0]
                or self.attributes.get(
                    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
                    [""],
                )[0]
                or ""
            )

            # Extract last name
            self.last_name = (
                self.attributes.get("last_name", [""])[0]
                or self.attributes.get("lastName", [""])[0]
                or self.attributes.get("surname", [""])[0]
                or self.attributes.get(
                    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
                    [""],
                )[0]
                or ""
            )

            # Extract department/organizational unit
            self.department = (
                self.attributes.get("department", [""])[0]
                or self.attributes.get("organizationalUnit", [""])[0]
                or self.attributes.get("ou", [""])[0]
                or ""
            )

            # Extract job title
            self.job_title = (
                self.attributes.get("job_title", [""])[0]
                or self.attributes.get("jobTitle", [""])[0]
                or self.attributes.get("title", [""])[0]
                or ""
            )

            # Extract phone number
            self.phone = (
                self.attributes.get("phone", [""])[0]
                or self.attributes.get("phoneNumber", [""])[0]
                or self.attributes.get("telephoneNumber", [""])[0]
                or ""
            )

            # Extract employee ID
            self.employee_id = (
                self.attributes.get("employee_id", [""])[0]
                or self.attributes.get("employeeId", [""])[0]
                or self.attributes.get("employeeNumber", [""])[0]
                or ""
            )

            # Extract groups - handle both single values and arrays
            groups_attr = (
                self.attributes.get("groups", [])
                or self.attributes.get("memberOf", [])
                or self.attributes.get("group_membership", [])
                or []
            )

            # Ensure groups is always a list
            if isinstance(groups_attr, str):
                self.groups = [groups_attr]
            elif isinstance(groups_attr, list):
                self.groups = groups_attr
            else:
                self.groups = []
        else:
            # Set default values for non-Google providers
            self.first_name = ""
            self.last_name = ""
            self.department = ""
            self.job_title = ""
            self.phone = ""
            self.employee_id = ""
            self.groups = []

    @classmethod
    def from_saml_attributes(
        cls, saml_attributes: Dict[str, Any], provider: str
    ) -> "User":
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
            saml_attributes.get(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                [""],
            )[0]
            or saml_attributes.get("email", [""])[0]
            or saml_attributes.get("mail", [""])[0]
            or saml_attributes.get("emailAddress", [""])[0]
        )

        # Extract name from various possible attribute names
        name = (
            saml_attributes.get(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name", [""]
            )[0]
            or saml_attributes.get("displayName", [""])[0]
            or saml_attributes.get("name", [""])[0]
            or saml_attributes.get("cn", [""])[0]
            or email  # Fallback to email if name not available
        )

        if not email:
            raise ValueError("Email address not found in SAML attributes")

        return cls(
            email=email, name=name, provider=provider, attributes=saml_attributes
        )

    def save_to_session(self) -> None:
        """Save user information to Flask session.

        Stores user data in the session for authentication persistence
        across requests.

        :raises RuntimeError: If session is not available
        """
        session["user"] = {
            "email": self.email,
            "name": self.name,
            "provider": self.provider,
            "attributes": self.attributes,
            "authenticated_at": self.authenticated_at.isoformat(),
            "roles": [role.value for role in self.user_permissions.roles],
            "permissions": [perm.value for perm in self.user_permissions.permissions],
            # Google IdP attributes
            "first_name": getattr(self, "first_name", ""),
            "last_name": getattr(self, "last_name", ""),
            "department": getattr(self, "department", ""),
            "job_title": getattr(self, "job_title", ""),
            "phone": getattr(self, "phone", ""),
            "employee_id": getattr(self, "employee_id", ""),
            "groups": getattr(self, "groups", []),
        }
        session["authenticated"] = True

    @classmethod
    def from_session(cls) -> Optional["User"]:
        """Load user from Flask session.

        :returns: User instance if authenticated, None otherwise
        :rtype: Optional[User]

        Example:
            Check if user is authenticated::

                user = User.from_session()
                if user:
                    print(f"Welcome {user.name}")
        """
        if not session.get("authenticated") or "user" not in session:
            return None

        user_data = session["user"]

        # Restore roles from session
        roles = set()
        if "roles" in user_data:
            for role_value in user_data["roles"]:
                try:
                    roles.add(UserRole(role_value))
                except ValueError:
                    pass  # Skip invalid roles

        user = cls(
            email=user_data["email"],
            name=user_data["name"],
            provider=user_data["provider"],
            attributes=user_data.get("attributes", {}),
            roles=roles,
        )

        # Restore Google IdP attributes
        user.first_name = user_data.get("first_name", "")
        user.last_name = user_data.get("last_name", "")
        user.department = user_data.get("department", "")
        user.job_title = user_data.get("job_title", "")
        user.phone = user_data.get("phone", "")
        user.employee_id = user_data.get("employee_id", "")
        user.groups = user_data.get("groups", [])

        # Restore original authentication timestamp
        if "authenticated_at" in user_data:
            user.authenticated_at = datetime.fromisoformat(
                user_data["authenticated_at"]
            )

        return user

    @staticmethod
    def logout() -> None:
        """Clear user session and logout.

        Removes only authentication-related data from the session,
        preserving other session data that may be useful.
        """
        session.pop("user", None)
        session.pop("authenticated", None)

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
        roles_str = ", ".join([role.value for role in self.user_permissions.roles])
        return f"<User {self.email} via {self.provider} roles=[{roles_str}]>"
