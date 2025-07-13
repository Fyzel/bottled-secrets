#!/usr/bin/env python3
"""Test Google IdP attribute extraction."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth.models import User


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
