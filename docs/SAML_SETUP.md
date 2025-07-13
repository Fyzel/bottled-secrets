# SAML Identity Provider Setup Guide

This guide provides detailed instructions for configuring SAML authentication with Google Workspace and Microsoft Azure AD.

## Prerequisites

- Domain with HTTPS certificate (required for production SAML)
- Admin access to Google Workspace or Azure AD
- Bottled Secrets application deployed and accessible

## Development vs Production Setup

### Development Environment

For local development and testing:

1. **Copy development environment template:**
   ```bash
   cp .env.dev .env
   ```

2. **Start with local development:**
   - Uses SQLite database (no setup required)
   - Debug mode enabled for detailed error messages
   - Localhost URLs for basic testing
   - Development-safe placeholder values

3. **Test without SAML first:**
   - Verify application starts: `flask run`
   - Check basic functionality before adding SAML complexity

### Production Environment

For production deployment:

1. **Copy production environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure for production:**
   - HTTPS-only URLs (required for SAML)
   - Strong secret keys and secure database credentials
   - Proper IdP certificates and configurations
   - Debug mode disabled for security

## Google Workspace Configuration

### Step 1: Access Google Admin Console

1. Navigate to [Google Admin Console](https://admin.google.com)
2. Sign in with your Google Workspace admin account
3. Go to **Apps** → **Web and mobile apps**

### Step 2: Create Custom SAML Application

1. Click **Add app** → **Add custom SAML app**
2. Enter application details:
   - **App name**: `Bottled Secrets`
   - **Description**: `Enterprise secret management application`
   - **App icon**: Upload your logo (optional)
3. Click **Continue**

### Step 3: Configure Google Identity Provider

1. On the "Google Identity Provider details" page, note these values:
   ```
   SSO URL: https://accounts.google.com/o/saml2/idp?idpid=C03az79cb
   Entity ID: https://accounts.google.com/o/saml2?idpid=C03az79cb
   ```
2. Download the **Certificate** (you'll need this for your .env file)
3. Click **Continue**

### Step 4: Configure Service Provider Details

Enter these values exactly:

```
ACS URL: https://your-domain.com/auth/acs
Entity ID: https://your-domain.com/auth/metadata
Start URL: https://your-domain.com/auth/login/google
Name ID format: EMAIL
Name ID: Basic Information > Primary email
```

**Advanced Settings:**
- ✅ **Signed response**: Checked
- ❌ **Assertion signed**: Unchecked (optional)

Click **Continue**

### Step 5: Attribute Mapping

Configure these attribute mappings:

| Google Directory attributes | App attributes |
|----------------------------|----------------|
| Basic Information > First name | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname` |
| Basic Information > Last name | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname` |
| Basic Information > Primary email | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` |
| Basic Information > Primary email | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name` |

Click **Finish**

### Step 6: Enable Application

1. Go to **User access** section
2. Select **ON for everyone** or configure specific organizational units
3. Click **Save**

### Step 7: Update Environment Variables

Add these to your `.env` file:

```bash
# Replace YOUR_IDP_ID with the actual ID from Google (e.g., C03az79cb)
GOOGLE_SAML_SP_ENTITY_ID=https://your-domain.com/auth/metadata
GOOGLE_SAML_SP_ACS_URL=https://your-domain.com/auth/acs
GOOGLE_SAML_IDP_ENTITY_ID=https://accounts.google.com/o/saml2?idpid=YOUR_IDP_ID
GOOGLE_SAML_IDP_SSO_URL=https://accounts.google.com/o/saml2/idp?idpid=YOUR_IDP_ID
GOOGLE_SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
MIIDdDCCAlygAwIBAgIGAVm...your certificate content here...
-----END CERTIFICATE-----"
```

## Microsoft Azure AD Configuration

### Step 1: Access Azure Portal

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure AD admin account
3. Go to **Azure Active Directory** → **Enterprise applications**

### Step 2: Create Enterprise Application

1. Click **+ New application**
2. Click **+ Create your own application**
3. Enter application details:
   - **Name**: `Bottled Secrets`
   - **What are you looking to do with your application?**:
     Select "Integrate any other application you don't find in the gallery (Non-gallery)"
4. Click **Create**

### Step 3: Configure Single Sign-On

1. In your new application, go to **Single sign-on**
2. Select **SAML** as the single sign-on method
3. Click **Edit** on "Basic SAML Configuration"

### Step 4: Basic SAML Configuration

Enter these values:

```
Identifier (Entity ID): https://your-domain.com/auth/metadata
Reply URL (Assertion Consumer Service URL): https://your-domain.com/auth/acs
Sign on URL: https://your-domain.com/auth/login/azure
Relay State: (leave blank)
Logout URL: https://your-domain.com/auth/logout (optional)
```

Click **Save**

### Step 5: SAML Signing Certificate

1. In the **SAML Signing Certificate** section
2. Download **Certificate (Base64)**
3. Note the **Thumbprint** (for verification)

### Step 6: Azure AD Identifiers

In the "Set up Bottled Secrets" section, note these values:
- **Login URL**: `https://login.microsoftonline.com/{tenant-id}/saml2`
- **Azure AD Identifier**: `https://sts.windows.net/{tenant-id}/`
- **Logout URL**: `https://login.microsoftonline.com/{tenant-id}/saml2` (optional)

### Step 7: User Attributes & Claims

Configure these claims:

| Claim name | Source | Source attribute |
|------------|--------|------------------|
| `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` | Attribute | user.mail |
| `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name` | Attribute | user.displayname |
| `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname` | Attribute | user.givenname |
| `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname` | Attribute | user.surname |

### Step 8: Assign Users/Groups

1. Go to **Users and groups**
2. Click **+ Add user/group**
3. Select users or groups that should have access
4. Click **Assign**

### Step 9: Update Environment Variables

Add these to your `.env` file:

```bash
# Replace {TENANT_ID} with your actual Azure AD tenant ID
AZURE_SAML_SP_ENTITY_ID=https://your-domain.com/auth/metadata
AZURE_SAML_SP_ACS_URL=https://your-domain.com/auth/acs
AZURE_SAML_IDP_ENTITY_ID=https://sts.windows.net/{TENANT_ID}/
AZURE_SAML_IDP_SSO_URL=https://login.microsoftonline.com/{TENANT_ID}/saml2
AZURE_SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----
MIIDdDCCAlygAwIBAgIGAVm...your certificate content here...
-----END CERTIFICATE-----"
```

## Testing SAML Integration

### 1. Verify Application Metadata

Test that your application can provide metadata to IdPs:

```bash
# Test Google provider metadata
curl -s https://your-domain.com/auth/metadata?provider=google | xmllint --format -

# Test Azure provider metadata
curl -s https://your-domain.com/auth/metadata?provider=azure | xmllint --format -
```

### 2. Test Authentication Flow

**Google Workspace:**
1. Visit: `https://your-domain.com/auth/login/google`
2. Should redirect to Google sign-in page
3. After successful authentication, should redirect back to your app

**Azure AD:**
1. Visit: `https://your-domain.com/auth/login/azure`
2. Should redirect to Microsoft sign-in page
3. After successful authentication, should redirect back to your app

### 3. Debug SAML Responses

Enable debug logging to troubleshoot issues:

```bash
# Add to .env
FLASK_DEBUG=true
LOG_LEVEL=DEBUG

# Monitor SAML responses
tail -f app.log | grep "SAML"
```

## Common Issues and Solutions

### Certificate Format Issues

**Problem**: Certificate not being recognized
**Solution**: Ensure proper PEM format:

```bash
# Verify certificate format
openssl x509 -in certificate.crt -text -noout

# Convert if needed
openssl x509 -in certificate.der -inform DER -out certificate.pem -outform PEM
```

### Clock Skew Issues

**Problem**: SAML assertion timestamp validation fails
**Solution**:
- Ensure server time is synchronized with NTP
- SAML has a ±5 minute tolerance for clock differences

```bash
# Check server time
timedatectl status

# Sync with NTP if needed
sudo timedatectl set-ntp true
```

### URL Mismatch Issues

**Problem**: ACS URL or Entity ID mismatch
**Solution**: Verify exact URL matching:
- Check for trailing slashes
- Ensure HTTP vs HTTPS consistency
- Verify port numbers if using non-standard ports

### Attribute Mapping Issues

**Problem**: User information not being received
**Solution**: Check SAML response attributes:

```python
# Add temporary debug code in auth/routes.py
attributes = auth.get_attributes()
current_app.logger.info(f"Received SAML attributes: {attributes}")
```

### Network/Firewall Issues

**Problem**: Cannot reach IdP endpoints
**Solution**: Verify network connectivity:

```bash
# Test connectivity to Google
curl -v https://accounts.google.com/o/saml2/idp

# Test connectivity to Azure
curl -v https://login.microsoftonline.com/{tenant-id}/saml2
```

## Security Best Practices

### 1. Certificate Management
- Store certificates securely
- Monitor certificate expiration dates
- Implement certificate rotation procedures

### 2. URL Validation
- Always use HTTPS in production
- Validate all redirect URLs
- Implement proper CSRF protection

### 3. User Provisioning
- Implement proper role assignment based on IdP groups
- Review user access regularly
- Implement user deprovisioning procedures

### 4. Logging and Monitoring
- Log all authentication events
- Monitor for suspicious activity
- Implement alerting for authentication failures

## Production Checklist

Before going live with SAML authentication:

- [ ] HTTPS certificate properly configured
- [ ] All URLs use HTTPS (no HTTP)
- [ ] Certificates stored securely
- [ ] Debug logging disabled in production
- [ ] User access properly configured in IdP
- [ ] Test authentication flow end-to-end
- [ ] Backup authentication method configured
- [ ] Monitoring and alerting configured
- [ ] User training completed
- [ ] Incident response procedures documented

## Support and Troubleshooting

For additional support:
1. Check application logs for detailed error messages
2. Use browser developer tools to inspect SAML requests/responses
3. Verify IdP configuration matches application expectations
4. Test with a minimal SAML validation tool
5. Consult IdP-specific documentation for advanced configuration options
