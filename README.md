# Bottled Secrets

**🔬 Vibe Coding Experiment using Claude Code**

A Flask web application with enterprise-grade authentication and role-based administration, built entirely through conversational programming with Claude Code.

## What is this?

This project is a **vibe coding experiment** - demonstrating how complex applications can be built through natural language conversations with Claude Code. Starting from a basic Python template, we progressively built a full-featured Flask application with authentication, authorization, and administration capabilities.

## Features

### 🔐 Authentication
- **SAML 2.0 Integration** with Google Workspace and Microsoft Azure AD
- Session-based user management
- Multi-provider authentication support

### 👑 Role-Based Access Control
- **User Administrator** - Full admin privileges
- **Regular User** - Standard application access  
- **Guest** - Limited access
- Granular permission system with decorators

### 🛠️ Administration Module
- User management dashboard
- Role assignment and removal
- Access control enforcement
- Statistics and reporting
- Professional admin interface

### 🧪 Testing & Quality
- Comprehensive test coverage with pytest
- Pylint compliance and code quality
- Type annotations for PyCharm IntelliSense
- Pre-commit hooks for code formatting

## Technology Stack

- **Flask 3.1.1** - Web framework
- **SQLAlchemy 2.0.41** - Database ORM
- **MariaDB** - Database engine
- **python3-saml** - SAML authentication
- **pytest** - Testing framework
- **pylint & mypy** - Code quality tools

## Project Structure

```
bottled-secrets/
├── app/
│   ├── __init__.py           # Application factory
│   ├── main/                 # Main blueprint
│   ├── auth/                 # Authentication module
│   │   ├── models.py         # User model with roles
│   │   ├── roles.py          # Role and permission system
│   │   ├── routes.py         # Auth routes
│   │   └── saml_config.py    # SAML configuration
│   ├── admin/                # Administration module
│   │   ├── routes.py         # Admin routes
│   │   ├── decorators.py     # Access control decorators
│   │   ├── user_manager.py   # User management logic
│   │   └── templates/        # Admin UI templates
│   ├── static/               # CSS, JS, images
│   └── templates/            # Base templates
├── config/
│   └── config.py             # Application configuration
├── tests/                    # Comprehensive test suite
└── requirements.txt          # Dependencies
```

## Getting Started

1. **Create Virtual Environment**
   ```bash
   python3 -m venv venv-wsl
   source venv-wsl/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your SAML and database settings
   ```

4. **Set Environment Variables**
   ```bash
   # For development
   export FLASK_ENV=development
   export FLASK_DEBUG=true
   
   # For production (CRITICAL: Never enable debug in production!)
   export FLASK_ENV=production
   export FLASK_DEBUG=false
   ```

5. **Run Application**
   ```bash
   flask run
   # Or run directly: python app.py
   ```

6. **Access Admin Panel**
   - Navigate to `/admin` (requires User Administrator role)
   - Sign in via SAML provider
   - Manage users and roles

## SAML Identity Provider Integration

This application supports SAML 2.0 authentication with Google Workspace and Microsoft Azure AD.

📋 **[Complete SAML Setup Guide](docs/SAML_SETUP.md)** - Detailed step-by-step instructions

### Quick Setup Overview

**For Google Workspace:**
1. Create custom SAML app in Google Admin Console
2. Configure ACS URL: `https://your-domain.com/auth/acs`
3. Set Entity ID: `https://your-domain.com/auth/metadata`
4. Map email and name attributes
5. Update environment variables with Google's certificate and URLs

**For Microsoft Azure AD:**
1. Create enterprise application in Azure Portal
2. Configure SAML single sign-on
3. Set same ACS URL and Entity ID as above
4. Configure user claims and attributes
5. Update environment variables with Azure's certificate and tenant info

### Required Environment Variables

```bash
# Google Workspace
GOOGLE_SAML_SP_ENTITY_ID=https://your-domain.com/auth/metadata
GOOGLE_SAML_SP_ACS_URL=https://your-domain.com/auth/acs
GOOGLE_SAML_IDP_ENTITY_ID=https://accounts.google.com/o/saml2?idpid=YOUR_IDP_ID
GOOGLE_SAML_IDP_SSO_URL=https://accounts.google.com/o/saml2/idp?idpid=YOUR_IDP_ID
GOOGLE_SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----..."

# Microsoft Azure AD
AZURE_SAML_SP_ENTITY_ID=https://your-domain.com/auth/metadata
AZURE_SAML_SP_ACS_URL=https://your-domain.com/auth/acs
AZURE_SAML_IDP_ENTITY_ID=https://sts.windows.net/TENANT_ID/
AZURE_SAML_IDP_SSO_URL=https://login.microsoftonline.com/TENANT_ID/saml2
AZURE_SAML_IDP_X509_CERT="-----BEGIN CERTIFICATE-----..."
```

### Authentication URLs

Once configured, users can authenticate via:
- **Google**: `https://your-domain.com/auth/login/google`
- **Azure**: `https://your-domain.com/auth/login/azure`

### Troubleshooting

Common issues and solutions are covered in the [detailed setup guide](docs/SAML_SETUP.md), including:
- Certificate format problems
- Clock synchronization issues  
- URL mismatch errors
- Attribute mapping problems
- Network connectivity issues

## Administration Access

Only users with the **User Administrator** role can access admin functions:
- User management at `/admin/users`
- Role assignment and removal
- Dashboard with statistics
- Comprehensive access control

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m pytest tests/test_admin.py -v
python -m pytest tests/test_roles.py -v

# Run with coverage
python -m pytest --cov=app
```

## Code Quality

```bash
# Lint code
pylint app/

# Type checking
mypy app/

# Format code
black app/ tests/
```

## Security Considerations

⚠️ **Critical Security Settings**

### Debug Mode
- **Development**: `FLASK_DEBUG=true` is acceptable for local development
- **Production**: `FLASK_DEBUG=false` must ALWAYS be set in production
- **Why**: Debug mode exposes sensitive information, allows code execution via browser, and reveals application internals

### Environment Configuration
```bash
# ✅ Secure Production Configuration
export FLASK_ENV=production
export FLASK_DEBUG=false
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex())')

# ❌ Insecure Configuration (Development Only!)
export FLASK_ENV=development  
export FLASK_DEBUG=true
export SECRET_KEY=dev-secret-key-change-in-production
```

### Production Deployment Checklist
- [ ] `FLASK_DEBUG=false` 
- [ ] Strong `SECRET_KEY` (64+ random characters)
- [ ] HTTPS enabled for all endpoints
- [ ] Database credentials secured
- [ ] SAML certificates properly configured
- [ ] Error logging configured (not displayed to users)
- [ ] Rate limiting implemented
- [ ] CSRF protection enabled (Flask-WTF)

## The Claude Code Experiment

This project demonstrates:
- **Conversational Programming** - Building complex applications through natural language
- **Iterative Development** - Progressive feature addition and refinement
- **Code Quality** - Maintaining professional standards while coding by conversation
- **Documentation** - Comprehensive docstrings and type annotations
- **Testing** - Full test coverage for reliability

### Development Process
1. Started with basic Python template
2. Created Flask application structure
3. Added SAML authentication
4. Implemented role-based access control
5. Built administration module with UI
6. Added comprehensive testing
7. Ensured code quality and documentation

## Known Issues

- SAML library compatibility (xmlsec/lxml version mismatch) - doesn't affect core functionality
- Session-based user storage (database persistence recommended for production)

## Contributing

This is an experimental project showcasing Claude Code capabilities. Feel free to explore the code and see how complex applications can be built through conversational programming!

## License

MIT License - See LICENSE file for details

---

**Built with Claude Code** - Anthropic's conversational programming assistant