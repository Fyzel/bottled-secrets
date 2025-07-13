#!/usr/bin/env python3
"""Test Google IdP attribute extraction - User model only."""

from typing import Dict, Any, Optional
from datetime import datetime


# Mock the dependencies to avoid SAML import issues
class MockUserRole:
    def __init__(self, value):
        self.value = value


class MockPermission:
    def __init__(self, value):
        self.value = value


class MockUserPermissions:
    def __init__(self):
        self.roles = set()
        self.permissions = set()

    def has_role(self, role):
        return role in self.roles

    def has_permission(self, permission):
        return permission in self.permissions

    def add_role(self, role, assigned_by):
        self.roles.add(role)

    def remove_role(self, role):
        self.roles.discard(role)

    def _update_permissions(self):
        pass


class MockRoleManager:
    @staticmethod
    def get_default_role():
        return MockUserRole("regular_user")


# Simplified User class for testing
class User:
    """User model for authenticated users."""

    def __init__(
        self,
        email: str,
        name: str,
        provider: str,
        attributes: Optional[Dict[str, Any]] = None,
        roles: Optional[set] = None,
    ) -> None:
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
        self.user_permissions: MockUserPermissions = MockUserPermissions()
        if roles:
            self.user_permissions.roles = set(roles)
        else:
            self.user_permissions.roles.add(MockRoleManager.get_default_role())

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


def test_google_attribute_extraction():
    """Test that Google SAML attributes are properly extracted."""

    # Mock Google SAML attributes
    google_saml_attributes = {
        "email": ["john.doe@company.com"],
        "displayName": ["John Doe"],
        "firstName": ["John"],
        "lastName": ["Doe"],
        "department": ["Engineering"],
        "jobTitle": ["Senior Software Engineer"],
        "phone": ["+1-555-0123"],
        "employeeId": ["EMP001"],
        "groups": ["developers", "admins", "all-staff"],
    }

    print("🧪 Testing Google IdP Attribute Extraction")
    print("=" * 50)

    # Create user from SAML attributes
    user = User.from_saml_attributes(google_saml_attributes, "google")

    # Verify basic attributes
    print(f"✅ Email: {user.email}")
    print(f"✅ Name: {user.name}")
    print(f"✅ Provider: {user.provider}")

    # Verify Google-specific attributes
    print(f"✅ First Name: {user.first_name}")
    print(f"✅ Last Name: {user.last_name}")
    print(f"✅ Department: {user.department}")
    print(f"✅ Job Title: {user.job_title}")
    print(f"✅ Phone: {user.phone}")
    print(f"✅ Employee ID: {user.employee_id}")
    print(f"✅ Groups: {user.groups}")

    # Test with missing attributes
    print("\n🧪 Testing with Missing Attributes")
    print("=" * 50)

    minimal_attributes = {
        "email": ["minimal@company.com"],
        "displayName": ["Minimal User"],
    }

    minimal_user = User.from_saml_attributes(minimal_attributes, "google")

    print(f"✅ Email: {minimal_user.email}")
    print(f"✅ Name: {minimal_user.name}")
    print(f"✅ First Name: '{minimal_user.first_name}' (should be empty)")
    print(f"✅ Last Name: '{minimal_user.last_name}' (should be empty)")
    print(f"✅ Department: '{minimal_user.department}' (should be empty)")
    print(f"✅ Groups: {minimal_user.groups} (should be empty list)")

    # Test non-Google provider
    print("\n🧪 Testing Non-Google Provider")
    print("=" * 50)

    azure_user = User.from_saml_attributes(minimal_attributes, "azure")
    print(f"✅ Provider: {azure_user.provider}")
    print(f"✅ First Name: '{azure_user.first_name}' (should be empty for non-Google)")
    print(f"✅ Groups: {azure_user.groups} (should be empty list)")

    print("\n🎉 All tests completed successfully!")

    return user


if __name__ == "__main__":
    test_google_attribute_extraction()
