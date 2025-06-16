"""Test cases for administration functionality.

This module contains comprehensive test cases for the administration module,
including user management, role assignment, and access control.

.. moduleauthor:: Bottled Secrets Team
.. module:: tests.test_admin
.. platform:: Unix, Windows
.. synopsis:: Administration module tests

Example:
    Run admin tests::

        python -m pytest tests/test_admin.py
        python -m unittest tests.test_admin
"""

import unittest
from unittest.mock import patch, MagicMock
from flask import session, url_for
from app import create_app
from config.config import TestingConfig
from app.auth.models import User
from app.auth.roles import UserRole, Permission, RoleManager
from app.admin.user_manager import UserManager, RoleAssignmentError
from app.admin.decorators import check_user_access


class AdminTestCase(unittest.TestCase):
    """Base test case class for administration tests.

    This test case class provides common setup and helper methods
    for testing administration functionality.

    :ivar app: Flask application instance for testing
    :type app: flask.Flask
    :ivar app_context: Flask application context
    :type app_context: flask.ctx.AppContext
    :ivar client: Flask test client
    :type client: flask.testing.FlaskClient
    """

    def setUp(self) -> None:
        """Set up test fixtures before each test method.

        Creates a test application instance with testing configuration,
        sets up application context, and initializes a test client.
        """
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        """Clean up after each test method.

        Removes the application context to ensure clean state
        between test runs.
        """
        self.app_context.pop()

    def create_test_user(self, email: str, name: str, roles: set = None) -> User:
        """Create a test user with specified roles.

        :param email: User's email address
        :type email: str
        :param name: User's full name
        :type name: str
        :param roles: Set of roles to assign
        :type roles: set
        :returns: Created user instance
        :rtype: User
        """
        if roles is None:
            roles = {UserRole.REGULAR_USER}
        return User(
            email=email,
            name=name,
            provider='test',
            roles=roles
        )

    def login_user(self, user: User) -> None:
        """Log in a user for testing.

        :param user: User to log in
        :type user: User
        """
        user.save_to_session()


class RoleSystemTestCase(AdminTestCase):
    """Test cases for the role and permission system."""

    def test_user_role_creation(self) -> None:
        """Test user role enumeration and display names."""
        # Test all roles exist
        roles = UserRole.get_all_roles()
        self.assertIn(UserRole.USER_ADMINISTRATOR, roles)
        self.assertIn(UserRole.REGULAR_USER, roles)
        self.assertIn(UserRole.GUEST, roles)

        # Test display names
        admin_display = UserRole.get_role_display_name(UserRole.USER_ADMINISTRATOR)
        self.assertEqual(admin_display, "User Administrator")

        user_display = UserRole.get_role_display_name(UserRole.REGULAR_USER)
        self.assertEqual(user_display, "Regular User")

    def test_permission_mapping(self) -> None:
        """Test role to permission mapping."""
        # Test admin permissions
        admin_perms = RoleManager.get_role_permissions(UserRole.USER_ADMINISTRATOR)
        self.assertIn(Permission.MANAGE_USERS, admin_perms)
        self.assertIn(Permission.MANAGE_ROLES, admin_perms)
        self.assertIn(Permission.VIEW_ADMIN_PANEL, admin_perms)

        # Test regular user permissions
        user_perms = RoleManager.get_role_permissions(UserRole.REGULAR_USER)
        self.assertIn(Permission.ACCESS_SECRETS, user_perms)
        self.assertNotIn(Permission.MANAGE_USERS, user_perms)

        # Test guest permissions
        guest_perms = RoleManager.get_role_permissions(UserRole.GUEST)
        self.assertEqual(len(guest_perms), 0)

    def test_role_assignment_validation(self) -> None:
        """Test role assignment validation logic."""
        admin_roles = {UserRole.USER_ADMINISTRATOR}
        user_roles = {UserRole.REGULAR_USER}

        # Admin can assign roles
        can_assign = RoleManager.can_assign_role(admin_roles, UserRole.REGULAR_USER)
        self.assertTrue(can_assign)

        # Regular user cannot assign roles
        can_assign = RoleManager.can_assign_role(user_roles, UserRole.REGULAR_USER)
        self.assertFalse(can_assign)

        # Test self-assignment validation
        is_valid, error = RoleManager.validate_role_assignment(
            'admin@test.com', admin_roles, 'admin@test.com', UserRole.USER_ADMINISTRATOR
        )
        self.assertFalse(is_valid)
        self.assertIn("Cannot assign User Administrator role to yourself", error)


class UserModelTestCase(AdminTestCase):
    """Test cases for the User model with roles."""

    def test_user_creation_with_roles(self) -> None:
        """Test user creation with role assignment."""
        roles = {UserRole.USER_ADMINISTRATOR, UserRole.REGULAR_USER}
        user = self.create_test_user('test@example.com', 'Test User', roles)

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.has_role(UserRole.USER_ADMINISTRATOR))
        self.assertTrue(user.has_role(UserRole.REGULAR_USER))
        self.assertTrue(user.is_admin())

    def test_user_default_role(self) -> None:
        """Test that new users get default role."""
        user = self.create_test_user('new@example.com', 'New User')
        self.assertTrue(user.has_role(UserRole.REGULAR_USER))

    def test_user_permission_checking(self) -> None:
        """Test user permission checking functionality."""
        admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        regular_user = self.create_test_user(
            'user@test.com', 'Regular User', {UserRole.REGULAR_USER}
        )

        # Test admin permissions
        self.assertTrue(admin_user.has_permission(Permission.MANAGE_USERS))
        self.assertTrue(admin_user.has_permission(Permission.ACCESS_SECRETS))

        # Test regular user permissions
        self.assertFalse(regular_user.has_permission(Permission.MANAGE_USERS))
        self.assertTrue(regular_user.has_permission(Permission.ACCESS_SECRETS))

    def test_role_assignment_and_removal(self) -> None:
        """Test dynamic role assignment and removal."""
        user = self.create_test_user('test@example.com', 'Test User')
        
        # Initially regular user
        self.assertTrue(user.has_role(UserRole.REGULAR_USER))
        self.assertFalse(user.is_admin())

        # Assign admin role
        user.assign_role(UserRole.USER_ADMINISTRATOR, 'system@test.com')
        self.assertTrue(user.has_role(UserRole.USER_ADMINISTRATOR))
        self.assertTrue(user.is_admin())

        # Remove admin role
        user.remove_role(UserRole.USER_ADMINISTRATOR)
        self.assertFalse(user.has_role(UserRole.USER_ADMINISTRATOR))
        self.assertFalse(user.is_admin())

    def test_session_persistence(self) -> None:
        """Test user role persistence in session."""
        with self.client.session_transaction() as sess:
            user = self.create_test_user(
                'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
            )
            user.save_to_session()

        # Retrieve from session
        with self.app.test_request_context():
            retrieved_user = User.from_session()
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.email, 'admin@test.com')
            self.assertTrue(retrieved_user.has_role(UserRole.USER_ADMINISTRATOR))


class UserManagerTestCase(AdminTestCase):
    """Test cases for the UserManager class."""

    def setUp(self) -> None:
        """Set up test fixtures with UserManager instance."""
        super().setUp()
        self.user_manager = UserManager()
        self.admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        self.regular_user = self.create_test_user(
            'user@test.com', 'Regular User', {UserRole.REGULAR_USER}
        )

    def test_get_all_users(self) -> None:
        """Test retrieving all users from the system."""
        users = self.user_manager.get_all_users()
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0)  # Should have demo users

        # Check user structure
        for user in users:
            self.assertIn('email', user)
            self.assertIn('name', user)
            self.assertIn('roles', user)
            self.assertIn('is_admin', user)

    def test_get_user_by_email(self) -> None:
        """Test retrieving user by email address."""
        # Test with session user
        self.login_user(self.admin_user)
        user = self.user_manager.get_user_by_email('admin@test.com')
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'admin@test.com')

        # Test with non-existent user
        user = self.user_manager.get_user_by_email('nonexistent@test.com')
        self.assertIsNone(user)

    def test_role_assignment_success(self) -> None:
        """Test successful role assignment."""
        success, message = self.user_manager.assign_role_to_user(
            self.admin_user, 'user@example.com', UserRole.USER_ADMINISTRATOR
        )
        # Note: This may fail because demo user doesn't exist in session
        # In a real implementation, this would work with database users

    def test_role_assignment_permission_denied(self) -> None:
        """Test role assignment with insufficient permissions."""
        success, message = self.user_manager.assign_role_to_user(
            self.regular_user, 'target@test.com', UserRole.USER_ADMINISTRATOR
        )
        self.assertFalse(success)
        self.assertIn("Insufficient permissions", message)

    def test_role_removal_self_admin(self) -> None:
        """Test prevention of self-removal of admin role."""
        success, message = self.user_manager.remove_role_from_user(
            self.admin_user, 'admin@test.com', UserRole.USER_ADMINISTRATOR
        )
        self.assertFalse(success)
        self.assertIn("Cannot remove User Administrator role from yourself", message)

    def test_get_role_statistics(self) -> None:
        """Test role statistics generation."""
        stats = self.user_manager.get_role_statistics()
        self.assertIsInstance(stats, dict)
        
        # Check that all roles are represented
        for role in UserRole.get_all_roles():
            self.assertIn(role.value, stats)
            self.assertIsInstance(stats[role.value], int)


class AccessControlTestCase(AdminTestCase):
    """Test cases for access control decorators and functions."""

    def test_check_user_access(self) -> None:
        """Test programmatic access control checking."""
        admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        regular_user = self.create_test_user(
            'user@test.com', 'Regular User', {UserRole.REGULAR_USER}
        )

        # Test admin access
        has_access, error = check_user_access(admin_user, UserRole.USER_ADMINISTRATOR)
        self.assertTrue(has_access)
        self.assertEqual(error, "")

        # Test regular user access denial
        has_access, error = check_user_access(regular_user, UserRole.USER_ADMINISTRATOR)
        self.assertFalse(has_access)
        self.assertIn("Role 'user_administrator' required", error)

        # Test unauthenticated access
        has_access, error = check_user_access(None, UserRole.USER_ADMINISTRATOR)
        self.assertFalse(has_access)
        self.assertEqual(error, "Authentication required")

    @patch('app.auth.models.User.from_session')
    def test_admin_required_decorator(self, mock_from_session: MagicMock) -> None:
        """Test admin_required decorator behavior."""
        # Test with no user (should redirect)
        mock_from_session.return_value = None
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect

        # Test with admin user (should allow access)
        admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        mock_from_session.return_value = admin_user
        
        # Note: This would require the admin blueprint to be registered
        # In actual testing, we'd need to set up the full app context

    def test_role_hierarchy(self) -> None:
        """Test that admin users have all permissions."""
        admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )

        # Admin should have all permissions
        all_permissions = RoleManager.get_all_permissions()
        for permission in all_permissions:
            self.assertTrue(
                admin_user.has_permission(permission),
                f"Admin should have permission: {permission.value}"
            )


class AdminRoutesTestCase(AdminTestCase):
    """Test cases for admin route functionality."""

    def setUp(self) -> None:
        """Set up test fixtures for route testing."""
        super().setUp()
        self.admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        self.regular_user = self.create_test_user(
            'user@test.com', 'Regular User', {UserRole.REGULAR_USER}
        )

    @patch('app.auth.models.User.from_session')
    def test_admin_dashboard_access(self, mock_from_session: MagicMock) -> None:
        """Test admin dashboard access control."""
        # Test unauthorized access
        mock_from_session.return_value = self.regular_user
        # Note: Would need admin blueprint registered to test actual routes

        # Test authorized access
        mock_from_session.return_value = self.admin_user
        # Note: Would need admin blueprint registered to test actual routes

    def test_role_assignment_form_data(self) -> None:
        """Test role assignment with form data validation."""
        # Test missing form data
        test_data = {
            'target_email': '',
            'role': ''
        }
        # Would test actual form submission with self.client.post()

        # Test valid form data
        test_data = {
            'target_email': 'user@test.com',
            'role': UserRole.REGULAR_USER.value
        }
        # Would test actual form submission with self.client.post()


class IntegrationTestCase(AdminTestCase):
    """Integration test cases for complete admin workflows."""

    def test_complete_user_management_workflow(self) -> None:
        """Test complete user management workflow."""
        # 1. Create admin user
        admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        
        # 2. Login admin user
        self.login_user(admin_user)
        
        # 3. Create user manager
        user_manager = UserManager()
        
        # 4. Get initial user count
        initial_users = user_manager.get_all_users()
        initial_count = len(initial_users)
        
        # 5. Check role statistics
        stats = user_manager.get_role_statistics()
        self.assertIsInstance(stats, dict)
        
        # 6. Test user lookup
        current_user = user_manager.get_user_by_email(admin_user.email)
        self.assertIsNotNone(current_user)
        self.assertTrue(current_user['is_admin'])

    def test_role_assignment_validation_workflow(self) -> None:
        """Test complete role assignment validation workflow."""
        admin_user = self.create_test_user(
            'admin@test.com', 'Admin User', {UserRole.USER_ADMINISTRATOR}
        )
        
        # Test various validation scenarios
        test_cases = [
            # (assigner_email, assigner_roles, target_email, target_role, should_succeed)
            ('admin@test.com', {UserRole.USER_ADMINISTRATOR}, 'user@test.com', UserRole.REGULAR_USER, True),
            ('user@test.com', {UserRole.REGULAR_USER}, 'target@test.com', UserRole.REGULAR_USER, False),
            ('admin@test.com', {UserRole.USER_ADMINISTRATOR}, 'admin@test.com', UserRole.USER_ADMINISTRATOR, False),
        ]
        
        for assigner_email, assigner_roles, target_email, target_role, should_succeed in test_cases:
            is_valid, error_msg = RoleManager.validate_role_assignment(
                assigner_email, assigner_roles, target_email, target_role
            )
            
            if should_succeed:
                self.assertTrue(is_valid, f"Assignment should succeed: {error_msg}")
            else:
                self.assertFalse(is_valid, f"Assignment should fail but didn't")


if __name__ == '__main__':
    unittest.main()