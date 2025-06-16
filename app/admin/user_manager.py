"""User management functionality for administration module.

This module provides the business logic for managing users, their roles,
and permissions within the Bottled Secrets application.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.admin.user_manager
.. platform:: Unix, Windows
.. synopsis:: User management business logic

Example:
    Manage users programmatically::

        manager = UserManager()
        users = manager.get_all_users()
        success = manager.assign_role_to_user(
            admin_user, target_email, UserRole.REGULAR_USER
        )
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from flask import session, current_app
from app.auth.models import User
from app.auth.roles import UserRole, RoleManager, UserPermissions

__all__ = ['UserManager', 'UserNotFoundException', 'RoleAssignmentError']


class UserNotFoundException(Exception):
    """Exception raised when a user is not found."""
    pass


class RoleAssignmentError(Exception):
    """Exception raised when role assignment fails."""
    pass


class UserManager:
    """Manager class for user administration operations.

    This class provides methods for creating, updating, deleting users
    and managing their roles and permissions.
    """

    def __init__(self) -> None:
        """Initialize UserManager.

        Note: In a production environment, this would interface with
        a database. For this implementation, we use session storage
        as a simple demonstration.
        """
        self._users_cache: Dict[str, Dict] = {}

    def get_all_users(self) -> List[Dict]:
        """Get list of all users in the system.

        :returns: List of user dictionaries with basic information
        :rtype: List[Dict]

        Example:
            Get all users::

                users = manager.get_all_users()
                for user in users:
                    print(f"{user['name']} - {user['email']}")
        """
        # In a real application, this would query the database
        # For demonstration, we'll return a mock list including session user
        users = []
        
        # Add current session user if authenticated
        current_user = User.from_session()
        if current_user:
            users.append({
                'email': current_user.email,
                'name': current_user.name,
                'provider': current_user.provider,
                'roles': [role.value for role in current_user.get_roles()],
                'role_display': [UserRole.get_role_display_name(role) 
                               for role in current_user.get_roles()],
                'authenticated_at': current_user.authenticated_at.isoformat(),
                'is_admin': current_user.is_admin(),
                'last_seen': datetime.utcnow().isoformat()
            })
        
        # Add cached users (simulating database storage)
        for email, user_data in self._users_cache.items():
            if current_user and email != current_user.email:
                users.append(user_data)
        
        # Add some demo users for testing if no users exist
        if not users:
            demo_users = [
                {
                    'email': 'admin@example.com',
                    'name': 'System Administrator',
                    'provider': 'google',
                    'roles': [UserRole.USER_ADMINISTRATOR.value],
                    'role_display': [UserRole.get_role_display_name(UserRole.USER_ADMINISTRATOR)],
                    'authenticated_at': datetime.utcnow().isoformat(),
                    'is_admin': True,
                    'last_seen': datetime.utcnow().isoformat()
                },
                {
                    'email': 'user@example.com',
                    'name': 'Regular User',
                    'provider': 'azure',
                    'roles': [UserRole.REGULAR_USER.value],
                    'role_display': [UserRole.get_role_display_name(UserRole.REGULAR_USER)],
                    'authenticated_at': datetime.utcnow().isoformat(),
                    'is_admin': False,
                    'last_seen': datetime.utcnow().isoformat()
                }
            ]
            users.extend(demo_users)
        
        return sorted(users, key=lambda x: x['name'])

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user information by email address.

        :param email: Email address of the user
        :type email: str
        :returns: User dictionary or None if not found
        :rtype: Optional[Dict]
        :raises UserNotFoundException: If user is not found

        Example:
            Get specific user::

                user = manager.get_user_by_email('user@example.com')
                if user:
                    print(f"Found user: {user['name']}")
        """
        users = self.get_all_users()
        for user in users:
            if user['email'].lower() == email.lower():
                return user
        return None

    def assign_role_to_user(
        self,
        admin_user: User,
        target_email: str,
        role: UserRole
    ) -> Tuple[bool, str]:
        """Assign role to a user.

        :param admin_user: User performing the role assignment
        :type admin_user: User
        :param target_email: Email of user receiving the role
        :type target_email: str
        :param role: Role to assign
        :type role: UserRole
        :returns: Tuple of (success, message)
        :rtype: Tuple[bool, str]
        :raises RoleAssignmentError: If assignment is not allowed

        Example:
            Assign admin role::

                success, message = manager.assign_role_to_user(
                    admin_user, 'user@example.com', UserRole.USER_ADMINISTRATOR
                )
                if success:
                    print("Role assigned successfully")
        """
        try:
            # Validate the assignment
            is_valid, error_msg = RoleManager.validate_role_assignment(
                admin_user.email,
                admin_user.get_roles(),
                target_email,
                role
            )
            
            if not is_valid:
                current_app.logger.warning(
                    f"Role assignment denied: {admin_user.email} -> {target_email} "
                    f"({role.value}): {error_msg}"
                )
                return False, error_msg

            # Check if target user exists
            target_user_data = self.get_user_by_email(target_email)
            if not target_user_data:
                return False, f"User {target_email} not found"

            # Update user roles
            current_roles = set()
            for role_value in target_user_data.get('roles', []):
                try:
                    current_roles.add(UserRole(role_value))
                except ValueError:
                    pass
            
            # Add new role
            current_roles.add(role)
            
            # Update user data
            target_user_data['roles'] = [r.value for r in current_roles]
            target_user_data['role_display'] = [UserRole.get_role_display_name(r) 
                                              for r in current_roles]
            target_user_data['is_admin'] = UserRole.USER_ADMINISTRATOR in current_roles
            
            # Cache the updated user data
            self._users_cache[target_email] = target_user_data
            
            # Update session if it's the current user
            current_user = User.from_session()
            if current_user and current_user.email.lower() == target_email.lower():
                current_user.assign_role(role, admin_user.email)
                current_user.save_to_session()

            current_app.logger.info(
                f"Role {role.value} assigned to {target_email} by {admin_user.email}"
            )
            
            return True, f"Role '{UserRole.get_role_display_name(role)}' assigned successfully"
            
        except Exception as e:
            current_app.logger.error(f"Role assignment error: {e}")
            return False, f"Failed to assign role: {str(e)}"

    def remove_role_from_user(
        self,
        admin_user: User,
        target_email: str,
        role: UserRole
    ) -> Tuple[bool, str]:
        """Remove role from a user.

        :param admin_user: User performing the role removal
        :type admin_user: User
        :param target_email: Email of user losing the role
        :type target_email: str
        :param role: Role to remove
        :type role: UserRole
        :returns: Tuple of (success, message)
        :rtype: Tuple[bool, str]

        Example:
            Remove admin role::

                success, message = manager.remove_role_from_user(
                    admin_user, 'user@example.com', UserRole.USER_ADMINISTRATOR
                )
        """
        try:
            # Check admin permissions
            if not admin_user.has_role(UserRole.USER_ADMINISTRATOR):
                return False, "Insufficient permissions to remove roles"

            # Prevent self-removal of admin role
            if (admin_user.email.lower() == target_email.lower() and 
                role == UserRole.USER_ADMINISTRATOR):
                return False, "Cannot remove User Administrator role from yourself"

            # Check if target user exists
            target_user_data = self.get_user_by_email(target_email)
            if not target_user_data:
                return False, f"User {target_email} not found"

            # Update user roles
            current_roles = set()
            for role_value in target_user_data.get('roles', []):
                try:
                    current_roles.add(UserRole(role_value))
                except ValueError:
                    pass
            
            # Remove role
            current_roles.discard(role)
            
            # Ensure user has at least one role
            if not current_roles:
                current_roles.add(RoleManager.get_default_role())
            
            # Update user data
            target_user_data['roles'] = [r.value for r in current_roles]
            target_user_data['role_display'] = [UserRole.get_role_display_name(r) 
                                              for r in current_roles]
            target_user_data['is_admin'] = UserRole.USER_ADMINISTRATOR in current_roles
            
            # Cache the updated user data
            self._users_cache[target_email] = target_user_data
            
            # Update session if it's the current user
            current_user = User.from_session()
            if current_user and current_user.email.lower() == target_email.lower():
                current_user.remove_role(role)
                current_user.save_to_session()

            current_app.logger.info(
                f"Role {role.value} removed from {target_email} by {admin_user.email}"
            )
            
            return True, f"Role '{UserRole.get_role_display_name(role)}' removed successfully"
            
        except Exception as e:
            current_app.logger.error(f"Role removal error: {e}")
            return False, f"Failed to remove role: {str(e)}"

    def get_user_roles(self, email: str) -> List[UserRole]:
        """Get all roles for a specific user.

        :param email: Email address of the user
        :type email: str
        :returns: List of user roles
        :rtype: List[UserRole]

        Example:
            Check user roles::

                roles = manager.get_user_roles('user@example.com')
                if UserRole.USER_ADMINISTRATOR in roles:
                    print("User is an administrator")
        """
        user_data = self.get_user_by_email(email)
        if not user_data:
            return []
        
        roles = []
        for role_value in user_data.get('roles', []):
            try:
                roles.append(UserRole(role_value))
            except ValueError:
                pass
        
        return roles

    def get_role_statistics(self) -> Dict[str, int]:
        """Get statistics about role distribution.

        :returns: Dictionary with role counts
        :rtype: Dict[str, int]

        Example:
            Get role stats::

                stats = manager.get_role_statistics()
                print(f"Administrators: {stats.get('user_administrator', 0)}")
        """
        users = self.get_all_users()
        stats = {}
        
        for role in UserRole.get_all_roles():
            stats[role.value] = 0
        
        for user in users:
            for role_value in user.get('roles', []):
                if role_value in stats:
                    stats[role_value] += 1
        
        return stats