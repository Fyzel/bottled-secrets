# Google SAML Configuration for Bottled Secrets

## ✅ HTTPS/TLS Setup Complete

Your Bottled Secrets application is now running with HTTPS/TLS encryption and is ready for Google SAML authentication.

## 🔗 URLs for Google Admin Console

### **Primary Configuration (Use these in Google Admin Console):**

**ACS URL (Assertion Consumer Service):**
```
https://192.168.129.33:5000/auth/acs
```

**Entity ID:**
```
https://192.168.129.33:5000/auth/metadata
```

**Metadata URL (optional):**
```
https://192.168.129.33:5000/auth/metadata
```

## 🔧 Google Admin Console Setup Steps

### 1. Access Google Admin Console
- Go to [admin.google.com](https://admin.google.com)
- Navigate to **Apps** → **Web and mobile apps**
- Find your existing SAML app or create a new one

### 2. Configure Service Provider Details
```
ACS URL: https://192.168.129.33:5000/auth/acs
Entity ID: https://192.168.129.33:5000/auth/metadata
Name ID format: Email address
Name ID: Primary email
```

### 3. Attribute Mapping (Required)
```
Google Directory → App Attributes
Primary email → email
First name → firstName
Last name → lastName
```

**📋 For complete attribute mapping configuration, see:**
**[GOOGLE_ATTRIBUTE_MAPPING.md](./GOOGLE_ATTRIBUTE_MAPPING.md)**

### 4. User Access
- Assign to appropriate organizational units
- Or assign to specific Google Groups
- Test with a limited set of users first

## 🔒 Current HTTPS Status

### **Server Information:**
- **Status**: ✅ Running with HTTPS/TLS
- **URL**: https://192.168.129.33:5000
- **Certificate**: Self-signed (valid for 365 days)
- **Protocol**: TLS 1.2+

### **Access Points:**
- **Main App**: https://192.168.129.33:5000
- **Folders**: https://192.168.129.33:5000/folders/
- **Demo Setup**: https://192.168.129.33:5000/demo-setup
- **SSL Test**: https://192.168.129.33:5000/test-ssl

## ⚠️ Browser Security Warnings

Since this uses a self-signed certificate, browsers will show security warnings:

### **Chrome/Edge:**
1. Click "Advanced"
2. Click "Proceed to 192.168.129.33 (unsafe)"

### **Firefox:**
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

### **Safari:**
1. Click "Show Details"
2. Click "visit this website"
3. Click "Visit Website"

**This is expected and safe for development/testing environments.**

## 🚀 Starting the HTTPS Server

```bash
# Navigate to project directory
cd /srv/user-data/schwabm/github/bottled-secrets

# Activate virtual environment
source venv/bin/activate

# Start HTTPS server
python https_demo.py
```

## 🧪 Testing SAML Integration

### 1. Verify HTTPS Endpoints
- Visit: https://192.168.129.33:5000/auth/metadata
- Should return XML metadata
- Visit: https://192.168.129.33:5000/test-ssl
- Should show certificate information

### 2. Test in Google Admin Console
- Use the "Test SAML Login" feature
- Should redirect to your HTTPS URLs
- Check for any SSL/certificate errors

### 3. Production Considerations
Once working, consider:
- Getting a proper SSL certificate from Let's Encrypt or commercial CA
- Using a proper domain name instead of IP address
- Setting up a reverse proxy (nginx/Apache) for production

## 📋 Configuration Files Updated

### **.env file contains:**
```bash
BASE_URL=https://192.168.129.33:5000
SAML_ENTITY_ID=https://192.168.129.33:5000/auth/metadata
GOOGLE_SAML_SP_ENTITY_ID=https://192.168.129.33:5000/auth/metadata
GOOGLE_SAML_SP_ACS_URL=https://192.168.129.33:5000/auth/acs
GOOGLE_SAML_IDP_ENTITY_ID=https://accounts.google.com/o/saml2?idpid=C01sj9hat
GOOGLE_SAML_IDP_SSO_URL=https://accounts.google.com/o/saml2/idp?idpid=C01sj9hat
```

### **SSL Certificates:**
- **Certificate**: `./certs/cert.pem`
- **Private Key**: `./certs/key.pem`
- **Valid for**: 365 days from creation
- **Subject**: CN=192.168.129.33

## 🔧 Troubleshooting

### Common Issues:
1. **Port 5000 blocked**: Check firewall settings
2. **Certificate errors**: Expected with self-signed certs
3. **SAML validation errors**: Verify exact URL matches in Google Admin Console

### Logs to Check:
- Flask server output for HTTPS requests
- Browser developer console for SSL errors
- Google Admin Console SAML test results

## 🎯 Next Steps

1. **Configure Google Admin Console** with the URLs above
2. **Test SAML authentication** using Google's test feature
3. **Assign users** to the SAML application
4. **Test end-to-end login** flow
5. **Resolve any remaining SAML library conflicts** for full functionality

Your application is now HTTPS-enabled and ready for Google SAML integration! 🚀
