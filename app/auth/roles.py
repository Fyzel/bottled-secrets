"""User roles and permissions system for Bottled Secrets Flask application.

This module defines user roles, permissions, and access control mechanisms
for the administration and security features of the application.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.auth.roles
.. platform:: Unix, Windows
.. synopsis:: Role-based access control system

Example:
    Check user permissions::

        if user.has_role(UserRole.USER_ADMINISTRATOR):
            # User can access admin functions
            pass

    Assign role to user::

        user.assign_role(UserRole.REGULAR_USER)
"""

from enum import Enum
from typing import Set, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

__all__ = ["UserRole", "Permission", "RoleManager", "UserPermissions"]


class UserRole(Enum):
    """Enumeration of user roles in the system.

    :cvar USER_ADMINISTRATOR: Can manage users and roles
    :type USER_ADMINISTRATOR: str
    :cvar REGULAR_USER: Standard user with basic access
    :type REGULAR_USER: str
    :cvar GUEST: Limited access user
    :type GUEST: str
    """

    USER_ADMINISTRATOR = "user_administrator"
    REGULAR_USER = "regular_user"
    GUEST = "guest"

    @classmethod
    def get_all_roles(cls) -> List["UserRole"]:
        """Get list of all available roles.

        :returns: List of all user roles
        :rtype: List[UserRole]
        """
        return list(cls)

    @classmethod
    def get_role_display_name(cls, role: "UserRole") -> str:
        """Get human-readable display name for role.

        :param role: User role to get display name for
        :type role: UserRole
        :returns: Human-readable role name
        :rtype: str
        """
        display_names = {
            cls.USER_ADMINISTRATOR: "User Administrator",
            cls.REGULAR_USER: "Regular User",
            cls.GUEST: "Guest User",
        }
        return display_names.get(role, role.value.replace("_", " ").title())


class Permission(Enum):
    """Enumeration of system permissions.

    :cvar MANAGE_USERS: Create, update, delete users
    :type MANAGE_USERS: str
    :cvar MANAGE_ROLES: Assign and revoke user roles
    :type MANAGE_ROLES: str
    :cvar VIEW_ADMIN_PANEL: Access administration interface
    :type VIEW_ADMIN_PANEL: str
    :cvar VIEW_USER_LIST: View list of system users
    :type VIEW_USER_LIST: str
    :cvar ACCESS_SECRETS: Access secret management features
    :type ACCESS_SECRETS: str
    :cvar MANAGE_SECRETS: Create, update, delete secrets and folders
    :type MANAGE_SECRETS: str
    """

    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_ADMIN_PANEL = "view_admin_panel"
    VIEW_USER_LIST = "view_user_list"
    ACCESS_SECRETS = "access_secrets"
    MANAGE_SECRETS = "manage_secrets"


@dataclass
class UserPermissions:
    """Container for user permissions and role information.

    :ivar roles: Set of roles assigned to the user
    :type roles: Set[UserRole]
    :ivar permissions: Set of permissions granted to the user
    :type permissions: Set[Permission]
    :ivar assigned_by: Email of admin who assigned the roles
    :type assigned_by: Optional[str]
    :ivar assigned_at: Timestamp when roles were assigned
    :type assigned_at: datetime
    """

    roles: Set[UserRole] = field(default_factory=set)
    permissions: Set[Permission] = field(default_factory=set)
    assigned_by: Optional[str] = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role.

        :param role: Role to check for
        :type role: UserRole
        :returns: True if user has the role
        :rtype: bool
        """
        return role in self.roles

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission.

        :param permission: Permission to check for
        :type permission: Permission
        :returns: True if user has the permission
        :rtype: bool
        """
        return permission in self.permissions

    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles.

        :param roles: List of roles to check for
        :type roles: List[UserRole]
        :returns: True if user has any of the roles
        :rtype: bool
        """
        return bool(self.roles.intersection(set(roles)))

    def add_role(self, role: UserRole, assigned_by: str) -> None:
        """Add role to user.

        :param role: Role to add
        :type role: UserRole
        :param assigned_by: Email of admin assigning the role
        :type assigned_by: str
        """
        self.roles.add(role)
        self.assigned_by = assigned_by
        self.assigned_at = datetime.utcnow()
        self._update_permissions()

    def remove_role(self, role: UserRole) -> None:
        """Remove role from user.

        :param role: Role to remove
        :type role: UserRole
        """
        self.roles.discard(role)
        self._update_permissions()

    def _update_permissions(self) -> None:
        """Update permissions based on current roles."""
        self.permissions.clear()
        for role in self.roles:
            self.permissions.update(RoleManager.get_role_permissions(role))


class RoleManager:
    """Manager class for role and permission operations.

    This class provides static methods for managing role-based access control,
    including permission mappings and role validation.
    """

    # Role to permissions mapping
    _ROLE_PERMISSIONS = {
        UserRole.USER_ADMINISTRATOR: {
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ADMIN_PANEL,
            Permission.VIEW_USER_LIST,
            Permission.ACCESS_SECRETS,
            Permission.MANAGE_SECRETS,
        },
        UserRole.REGULAR_USER: {Permission.ACCESS_SECRETS, Permission.MANAGE_SECRETS},
        UserRole.GUEST: set(),  # No permissions for guests
    }

    @classmethod
    def get_role_permissions(cls, role: UserRole) -> Set[Permission]:
        """Get permissions for a specific role.

        :param role: Role to get permissions for
        :type role: UserRole
        :returns: Set of permissions for the role
        :rtype: Set[Permission]
        """
        return cls._ROLE_PERMISSIONS.get(role, set()).copy()

    @classmethod
    def get_all_permissions(cls) -> Set[Permission]:
        """Get all available permissions in the system.

        :returns: Set of all permissions
        :rtype: Set[Permission]
        """
        all_permissions = set()
        for permissions in cls._ROLE_PERMISSIONS.values():
            all_permissions.update(permissions)
        return all_permissions

    @classmethod
    def can_assign_role(
        cls, assigner_roles: Set[UserRole], target_role: UserRole
    ) -> bool:
        """Check if user with given roles can assign a target role.

        :param assigner_roles: Roles of the user attempting to assign
        :type assigner_roles: Set[UserRole]
        :param target_role: Role being assigned
        :type target_role: UserRole
        :returns: True if assignment is allowed
        :rtype: bool
        """
        # Only User Administrators can assign roles
        return UserRole.USER_ADMINISTRATOR in assigner_roles

    @classmethod
    def validate_role_assignment(
        cls,
        assigner_email: str,
        assigner_roles: Set[UserRole],
        target_email: str,
        target_role: UserRole,
    ) -> tuple[bool, str]:
        """Validate a role assignment operation.

        :param assigner_email: Email of user attempting assignment
        :type assigner_email: str
        :param assigner_roles: Roles of the assigner
        :type assigner_roles: Set[UserRole]
        :param target_email: Email of user receiving role
        :type target_email: str
        :param target_role: Role being assigned
        :type target_role: UserRole
        :returns: Tuple of (is_valid, error_message)
        :rtype: tuple[bool, str]
        """
        # Check if assigner has permission
        if not cls.can_assign_role(assigner_roles, target_role):
            return False, "Insufficient permissions to assign roles"

        # Prevent self-assignment of User Administrator role
        if (
            assigner_email == target_email
            and target_role == UserRole.USER_ADMINISTRATOR
        ):
            return False, "Cannot assign User Administrator role to yourself"

        # Validate target role exists
        if target_role not in UserRole.get_all_roles():
            return False, f"Invalid role: {target_role.value}"

        return True, ""

    @classmethod
    def get_default_role(cls) -> UserRole:
        """Get the default role for new users.

        :returns: Default user role
        :rtype: UserRole
        """
        return UserRole.REGULAR_USER
