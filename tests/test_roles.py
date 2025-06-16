"""Test cases for role and permission system.

This module contains focused test cases for the role-based access control
system, including role definitions, permission mappings, and validation logic.

.. moduleauthor:: Bottled Secrets Team
.. module:: tests.test_roles
.. platform:: Unix, Windows
.. synopsis:: Role system tests

Example:
    Run role tests::

        python -m pytest tests/test_roles.py -v
        python -m unittest tests.test_roles.RoleSystemTestCase.test_role_permissions
"""

import unittest
from datetime import datetime
from app.auth.roles import (
    UserRole, Permission, RoleManager, UserPermissions
)


class RoleEnumTestCase(unittest.TestCase):
    """Test cases for role enumeration functionality."""

    def test_user_role_values(self) -> None:
        """Test that user roles have correct string values."""
        self.assertEqual(UserRole.USER_ADMINISTRATOR.value, "user_administrator")
        self.assertEqual(UserRole.REGULAR_USER.value, "regular_user")
        self.assertEqual(UserRole.GUEST.value, "guest")

    def test_get_all_roles(self) -> None:
        """Test getting all available roles."""
        all_roles = UserRole.get_all_roles()
        
        self.assertIsInstance(all_roles, list)
        self.assertEqual(len(all_roles), 3)
        self.assertIn(UserRole.USER_ADMINISTRATOR, all_roles)
        self.assertIn(UserRole.REGULAR_USER, all_roles)
        self.assertIn(UserRole.GUEST, all_roles)

    def test_role_display_names(self) -> None:
        """Test role display name generation."""
        test_cases = [
            (UserRole.USER_ADMINISTRATOR, "User Administrator"),
            (UserRole.REGULAR_USER, "Regular User"),
            (UserRole.GUEST, "Guest User")
        ]
        
        for role, expected_display in test_cases:
            display_name = UserRole.get_role_display_name(role)
            self.assertEqual(display_name, expected_display)

    def test_permission_values(self) -> None:
        """Test that permissions have correct string values."""
        self.assertEqual(Permission.MANAGE_USERS.value, "manage_users")
        self.assertEqual(Permission.MANAGE_ROLES.value, "manage_roles")
        self.assertEqual(Permission.VIEW_ADMIN_PANEL.value, "view_admin_panel")
        self.assertEqual(Permission.VIEW_USER_LIST.value, "view_user_list")
        self.assertEqual(Permission.ACCESS_SECRETS.value, "access_secrets")


class UserPermissionsTestCase(unittest.TestCase):
    """Test cases for UserPermissions class functionality."""

    def setUp(self) -> None:
        """Set up test fixtures for permission testing."""
        self.user_permissions = UserPermissions()

    def test_empty_permissions_initialization(self) -> None:
        """Test empty permissions initialization."""
        self.assertEqual(len(self.user_permissions.roles), 0)
        self.assertEqual(len(self.user_permissions.permissions), 0)
        self.assertIsNone(self.user_permissions.assigned_by)
        self.assertIsInstance(self.user_permissions.assigned_at, datetime)

    def test_has_role_functionality(self) -> None:
        """Test role checking functionality."""
        # Initially no roles
        self.assertFalse(self.user_permissions.has_role(UserRole.REGULAR_USER))
        
        # Add role
        self.user_permissions.add_role(UserRole.REGULAR_USER, "admin@test.com")
        self.assertTrue(self.user_permissions.has_role(UserRole.REGULAR_USER))
        self.assertFalse(self.user_permissions.has_role(UserRole.USER_ADMINISTRATOR))

    def test_has_permission_functionality(self) -> None:
        """Test permission checking functionality."""
        # Add admin role (should get all permissions)
        self.user_permissions.add_role(UserRole.USER_ADMINISTRATOR, "system@test.com")
        
        self.assertTrue(self.user_permissions.has_permission(Permission.MANAGE_USERS))
        self.assertTrue(self.user_permissions.has_permission(Permission.ACCESS_SECRETS))

    def test_has_any_role_functionality(self) -> None:
        """Test checking for any of multiple roles."""
        self.user_permissions.add_role(UserRole.REGULAR_USER, "admin@test.com")
        
        # Should match one of the roles
        roles_to_check = [UserRole.USER_ADMINISTRATOR, UserRole.REGULAR_USER]
        self.assertTrue(self.user_permissions.has_any_role(roles_to_check))
        
        # Should not match any roles
        roles_to_check = [UserRole.USER_ADMINISTRATOR, UserRole.GUEST]
        self.assertFalse(self.user_permissions.has_any_role(roles_to_check))

    def test_add_role_functionality(self) -> None:
        """Test adding roles to user permissions."""
        assigned_by = "admin@test.com"
        self.user_permissions.add_role(UserRole.REGULAR_USER, assigned_by)
        
        self.assertTrue(self.user_permissions.has_role(UserRole.REGULAR_USER))
        self.assertEqual(self.user_permissions.assigned_by, assigned_by)
        self.assertIsInstance(self.user_permissions.assigned_at, datetime)

    def test_remove_role_functionality(self) -> None:
        """Test removing roles from user permissions."""
        # Add then remove role
        self.user_permissions.add_role(UserRole.REGULAR_USER, "admin@test.com")
        self.assertTrue(self.user_permissions.has_role(UserRole.REGULAR_USER))
        
        self.user_permissions.remove_role(UserRole.REGULAR_USER)
        self.assertFalse(self.user_permissions.has_role(UserRole.REGULAR_USER))

    def test_permissions_update_on_role_change(self) -> None:
        """Test that permissions update when roles change."""
        # Add admin role
        self.user_permissions.add_role(UserRole.USER_ADMINISTRATOR, "system@test.com")
        admin_permissions = self.user_permissions.permissions.copy()
        
        # Should have admin permissions
        self.assertIn(Permission.MANAGE_USERS, admin_permissions)
        self.assertIn(Permission.MANAGE_ROLES, admin_permissions)
        
        # Remove admin role, add regular user role
        self.user_permissions.remove_role(UserRole.USER_ADMINISTRATOR)
        self.user_permissions.add_role(UserRole.REGULAR_USER, "system@test.com")
        
        # Should only have regular user permissions
        self.assertNotIn(Permission.MANAGE_USERS, self.user_permissions.permissions)
        self.assertIn(Permission.ACCESS_SECRETS, self.user_permissions.permissions)


class RoleManagerTestCase(unittest.TestCase):
    """Test cases for RoleManager class functionality."""

    def test_get_role_permissions_admin(self) -> None:
        """Test getting permissions for administrator role."""
        admin_perms = RoleManager.get_role_permissions(UserRole.USER_ADMINISTRATOR)
        
        expected_permissions = {
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ADMIN_PANEL,
            Permission.VIEW_USER_LIST,
            Permission.ACCESS_SECRETS
        }
        
        self.assertEqual(admin_perms, expected_permissions)

    def test_get_role_permissions_regular_user(self) -> None:
        """Test getting permissions for regular user role."""
        user_perms = RoleManager.get_role_permissions(UserRole.REGULAR_USER)
        
        expected_permissions = {Permission.ACCESS_SECRETS}
        self.assertEqual(user_perms, expected_permissions)

    def test_get_role_permissions_guest(self) -> None:
        """Test getting permissions for guest role."""
        guest_perms = RoleManager.get_role_permissions(UserRole.GUEST)
        self.assertEqual(len(guest_perms), 0)

    def test_get_all_permissions(self) -> None:
        """Test getting all available permissions."""
        all_perms = RoleManager.get_all_permissions()
        
        expected_permissions = {
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ADMIN_PANEL,
            Permission.VIEW_USER_LIST,
            Permission.ACCESS_SECRETS
        }
        
        self.assertEqual(all_perms, expected_permissions)

    def test_can_assign_role_admin(self) -> None:
        """Test that administrators can assign roles."""
        admin_roles = {UserRole.USER_ADMINISTRATOR}
        
        # Admin can assign any role
        self.assertTrue(RoleManager.can_assign_role(admin_roles, UserRole.REGULAR_USER))
        self.assertTrue(RoleManager.can_assign_role(admin_roles, UserRole.USER_ADMINISTRATOR))
        self.assertTrue(RoleManager.can_assign_role(admin_roles, UserRole.GUEST))

    def test_can_assign_role_non_admin(self) -> None:
        """Test that non-administrators cannot assign roles."""
        user_roles = {UserRole.REGULAR_USER}
        guest_roles = {UserRole.GUEST}
        
        # Regular users and guests cannot assign roles
        self.assertFalse(RoleManager.can_assign_role(user_roles, UserRole.REGULAR_USER))
        self.assertFalse(RoleManager.can_assign_role(guest_roles, UserRole.GUEST))

    def test_validate_role_assignment_success(self) -> None:
        """Test successful role assignment validation."""
        admin_roles = {UserRole.USER_ADMINISTRATOR}
        
        is_valid, error_msg = RoleManager.validate_role_assignment(
            "admin@test.com",
            admin_roles,
            "user@test.com",
            UserRole.REGULAR_USER
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")

    def test_validate_role_assignment_insufficient_permissions(self) -> None:
        """Test role assignment validation with insufficient permissions."""
        user_roles = {UserRole.REGULAR_USER}
        
        is_valid, error_msg = RoleManager.validate_role_assignment(
            "user@test.com",
            user_roles,
            "target@test.com",
            UserRole.REGULAR_USER
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Insufficient permissions", error_msg)

    def test_validate_role_assignment_self_admin(self) -> None:
        """Test prevention of self-assignment of admin role."""
        admin_roles = {UserRole.USER_ADMINISTRATOR}
        
        is_valid, error_msg = RoleManager.validate_role_assignment(
            "admin@test.com",
            admin_roles,
            "admin@test.com",  # Same email
            UserRole.USER_ADMINISTRATOR
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Cannot assign User Administrator role to yourself", error_msg)

    def test_validate_role_assignment_invalid_role(self) -> None:
        """Test role assignment validation with invalid role."""
        # Create a mock invalid role by manipulating the enum
        admin_roles = {UserRole.USER_ADMINISTRATOR}
        
        # Note: This test would need to be adapted based on how we handle
        # invalid roles in practice. The current implementation expects
        # valid UserRole enum values.

    def test_get_default_role(self) -> None:
        """Test getting the default role for new users."""
        default_role = RoleManager.get_default_role()
        self.assertEqual(default_role, UserRole.REGULAR_USER)


class RolePermissionMappingTestCase(unittest.TestCase):
    """Test cases for role-permission mapping consistency."""

    def test_all_roles_have_permission_mapping(self) -> None:
        """Test that all roles have permission mappings defined."""
        all_roles = UserRole.get_all_roles()
        
        for role in all_roles:
            permissions = RoleManager.get_role_permissions(role)
            # Even if empty (like guest), should return a set
            self.assertIsInstance(permissions, set)

    def test_permission_hierarchy(self) -> None:
        """Test that permission hierarchy is maintained."""
        admin_perms = RoleManager.get_role_permissions(UserRole.USER_ADMINISTRATOR)
        user_perms = RoleManager.get_role_permissions(UserRole.REGULAR_USER)
        guest_perms = RoleManager.get_role_permissions(UserRole.GUEST)
        
        # Admin should have more permissions than users
        self.assertGreater(len(admin_perms), len(user_perms))
        
        # Users should have more permissions than guests
        self.assertGreaterEqual(len(user_perms), len(guest_perms))
        
        # Admin should have all user permissions
        self.assertTrue(user_perms.issubset(admin_perms))

    def test_permission_isolation(self) -> None:
        """Test that sensitive permissions are properly isolated."""
        user_perms = RoleManager.get_role_permissions(UserRole.REGULAR_USER)
        guest_perms = RoleManager.get_role_permissions(UserRole.GUEST)
        
        # Regular users should not have admin permissions
        self.assertNotIn(Permission.MANAGE_USERS, user_perms)
        self.assertNotIn(Permission.MANAGE_ROLES, user_perms)
        self.assertNotIn(Permission.VIEW_ADMIN_PANEL, user_perms)
        
        # Guests should not have any management permissions
        management_permissions = {
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ADMIN_PANEL,
            Permission.VIEW_USER_LIST,
            Permission.ACCESS_SECRETS
        }
        
        self.assertTrue(management_permissions.isdisjoint(guest_perms))

    def test_role_permission_immutability(self) -> None:
        """Test that role permissions are returned as copies."""
        admin_perms_1 = RoleManager.get_role_permissions(UserRole.USER_ADMINISTRATOR)
        admin_perms_2 = RoleManager.get_role_permissions(UserRole.USER_ADMINISTRATOR)
        
        # Should be equal but not the same object
        self.assertEqual(admin_perms_1, admin_perms_2)
        self.assertIsNot(admin_perms_1, admin_perms_2)
        
        # Modifying one should not affect the other
        admin_perms_1.add(Permission.ACCESS_SECRETS)  # Already there, but safe
        original_length = len(admin_perms_2)
        admin_perms_1.clear()
        
        # admin_perms_2 should be unchanged
        self.assertEqual(len(admin_perms_2), original_length)


class EdgeCaseTestCase(unittest.TestCase):
    """Test cases for edge cases and error conditions."""

    def test_empty_role_set_validation(self) -> None:
        """Test validation with empty role sets."""
        empty_roles = set()
        
        can_assign = RoleManager.can_assign_role(empty_roles, UserRole.REGULAR_USER)
        self.assertFalse(can_assign)

    def test_multiple_role_assignment(self) -> None:
        """Test user with multiple roles."""
        user_permissions = UserPermissions()
        
        # Add multiple roles
        user_permissions.add_role(UserRole.USER_ADMINISTRATOR, "system@test.com")
        user_permissions.add_role(UserRole.REGULAR_USER, "system@test.com")
        
        # Should have both roles
        self.assertTrue(user_permissions.has_role(UserRole.USER_ADMINISTRATOR))
        self.assertTrue(user_permissions.has_role(UserRole.REGULAR_USER))
        
        # Should have union of all permissions
        admin_perms = RoleManager.get_role_permissions(UserRole.USER_ADMINISTRATOR)
        user_perms = RoleManager.get_role_permissions(UserRole.REGULAR_USER)
        expected_perms = admin_perms.union(user_perms)
        
        self.assertEqual(user_permissions.permissions, expected_perms)

    def test_role_removal_nonexistent(self) -> None:
        """Test removing a role that user doesn't have."""
        user_permissions = UserPermissions()
        user_permissions.add_role(UserRole.REGULAR_USER, "admin@test.com")
        
        # Remove role user doesn't have (should not error)
        user_permissions.remove_role(UserRole.USER_ADMINISTRATOR)
        
        # Should still have original role
        self.assertTrue(user_permissions.has_role(UserRole.REGULAR_USER))


if __name__ == '__main__':
    unittest.main()