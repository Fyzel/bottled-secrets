# Google Workspace SAML Attribute Mapping Configuration

## 📋 Overview

This document provides the complete attribute mapping configuration for Google Workspace SAML integration with Bottled Secrets. Configure these mappings in your Google Admin Console to ensure user profile data is properly extracted and stored.

## 🔧 Google Admin Console Configuration

### Access the Configuration
1. Go to [admin.google.com](https://admin.google.com)
2. Navigate to **Apps** → **Web and mobile apps**
3. Find your Bottled Secrets SAML app
4. Click **SAML attribute mapping**

## 📊 Required Attribute Mappings

Configure the following mappings in your Google Admin Console:

### **Primary Attributes (Required)**
```
Google Directory Attribute → App Attribute Name
═══════════════════════════════════════════════
Primary email              → email
First name                 → firstName
Last name                  → lastName
```

### **Extended Attributes (Recommended)**
```
Google Directory Attribute → App Attribute Name
═══════════════════════════════════════════════
Department                 → department
Job title                  → jobTitle
Phone number              → phone
Employee ID               → employeeId
Organizational unit       → organizationalUnit
```

### **Group Membership (Optional)**
```
Google Directory Attribute → App Attribute Name
═══════════════════════════════════════════════
Group membership          → groups
```

## 🔍 Detailed Configuration Steps

### 1. Basic User Information
**In Google Admin Console → SAML attribute mapping:**

| Google Directory | App Attribute | Purpose |
|------------------|---------------|---------|
| `Primary email` | `email` | User identification and login |
| `First name` | `firstName` | User's given name |
| `Last name` | `lastName` | User's family name |

### 2. Organizational Information
**Add these optional but recommended mappings:**

| Google Directory | App Attribute | Purpose |
|------------------|---------------|---------|
| `Department` | `department` | User's department/division |
| `Job title` | `jobTitle` | User's role/position |
| `Organizational unit` | `organizationalUnit` | OU membership |

### 3. Contact Information
**For additional user context:**

| Google Directory | App Attribute | Purpose |
|------------------|---------------|---------|
| `Phone number` | `phone` | Contact information |
| `Employee ID` | `employeeId` | Internal employee identifier |

### 4. Group Membership
**For role-based access control:**

| Google Directory | App Attribute | Purpose |
|------------------|---------------|---------|
| `Group membership` | `groups` | Google Groups for access control |

## 🏢 Example Configuration Screenshot Guide

### Step-by-Step in Google Admin Console:

1. **Navigate to SAML App**
   - Apps → Web and mobile apps → [Your Bottled Secrets App]

2. **Click "SAML attribute mapping"**

3. **Add Primary Mappings:**
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ Google Directory attributes → App attributes            │
   ├─────────────────────────────────────────────────────────┤
   │ Primary email           → email                         │
   │ First name             → firstName                      │
   │ Last name              → lastName                       │
   └─────────────────────────────────────────────────────────┘
   ```

4. **Add Extended Mappings:**
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ Department             → department                     │
   │ Job title              → jobTitle                       │
   │ Phone number           → phone                          │
   │ Employee ID            → employeeId                     │
   │ Organizational unit    → organizationalUnit             │
   └─────────────────────────────────────────────────────────┘
   ```

5. **Add Group Mapping (if using Groups for access control):**
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ Group membership       → groups                         │
   └─────────────────────────────────────────────────────────┘
   ```

## 🧪 Testing the Configuration

### 1. Test SAML Assertion
After configuring mappings, test with Google's SAML test tool:

1. In Google Admin Console, go to your SAML app
2. Click **Test SAML login**
3. Check the SAML response for attribute values
4. Verify attributes are being sent correctly

### 2. Expected SAML Response
Your SAML response should include attributes like:
```xml
<saml:AttributeStatement>
    <saml:Attribute Name="email">
        <saml:AttributeValue>user@yourdomain.com</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="firstName">
        <saml:AttributeValue>John</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="lastName">
        <saml:AttributeValue>Doe</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="department">
        <saml:AttributeValue>Engineering</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="jobTitle">
        <saml:AttributeValue>Software Engineer</saml:AttributeValue>
    </saml:Attribute>
    <!-- Additional attributes... -->
</saml:AttributeStatement>
```

## 📝 Code Implementation Details

### User Model Enhancement
The Bottled Secrets User model has been enhanced to extract these attributes:

```python
# Attributes extracted from Google SAML response:
user.email          # Primary email address
user.name           # Full display name
user.first_name     # Given name
user.last_name      # Family name
user.department     # Department/division
user.job_title      # Job title/position
user.phone          # Phone number
user.employee_id    # Employee identifier
user.groups         # Group memberships (list)
```

### Attribute Extraction Logic
The system checks multiple possible attribute names for compatibility:

```python
# Example: First name extraction
self.first_name = (
    self.attributes.get('first_name', [''])[0] or
    self.attributes.get('firstName', [''])[0] or
    self.attributes.get('givenName', [''])[0] or
    ''
)
```

## 🔒 Security Considerations

### 1. Attribute Privacy
- Only map attributes that are necessary for your application
- Consider data privacy regulations (GDPR, CCPA)
- Review what information is being shared

### 2. Group-Based Access Control
If using groups for access control:
- Create specific Google Groups for Bottled Secrets access
- Map groups to application roles appropriately
- Regularly review group memberships

### 3. Data Validation
- Bottled Secrets validates all incoming attributes
- Invalid or missing attributes are handled gracefully
- No sensitive data is logged in plaintext

## 🚨 Troubleshooting

### Common Issues:

**1. Attributes Not Appearing**
- Verify exact spelling of app attribute names
- Check that users have the required directory attributes populated
- Test with Google's SAML test tool

**2. Empty Values**
- Ensure users have all directory fields populated in Google Admin
- Some attributes may be optional and empty for some users

**3. Group Mapping Issues**
- Verify users are members of the groups you're mapping
- Group names are case-sensitive
- Test with users who are definitely group members

### Debug Steps:
1. Test SAML login in Google Admin Console
2. Check SAML response XML for attribute values
3. Review Flask application logs for attribute extraction
4. Verify user session data includes expected attributes

## 📋 Quick Reference Card

**Copy this configuration to your Google Admin Console:**

```
Primary email     → email
First name       → firstName
Last name        → lastName
Department       → department
Job title        → jobTitle
Phone number     → phone
Employee ID      → employeeId
Group membership → groups
```

## ✅ Verification Checklist

- [ ] Primary email mapped to `email`
- [ ] First name mapped to `firstName`
- [ ] Last name mapped to `lastName`
- [ ] Department mapped to `department` (optional)
- [ ] Job title mapped to `jobTitle` (optional)
- [ ] Phone mapped to `phone` (optional)
- [ ] Employee ID mapped to `employeeId` (optional)
- [ ] Groups mapped to `groups` (optional)
- [ ] Test SAML login successful
- [ ] Attributes visible in SAML response
- [ ] User profile data populated in Bottled Secrets

Your Google Workspace SAML integration is now configured to provide comprehensive user profile information to Bottled Secrets! 🚀
