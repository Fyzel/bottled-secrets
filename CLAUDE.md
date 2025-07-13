# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv-wsl
source venv-wsl/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your SAML and database settings
```

### Running the Application
```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=true  # Development only!

# Run Flask application
flask run
# Or directly: python app.py
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m pytest tests/test_admin.py -v
python -m pytest tests/test_roles.py -v

# Run with coverage
python -m pytest --cov=app
```

### Code Quality
```bash
# Lint code
pylint app/

# Type checking
mypy app/

# Format code
black app/ tests/
```

## High-Level Architecture

### Application Factory Pattern
The application uses Flask's application factory pattern implemented in `app/__init__.py:create_app()`. The factory creates Flask instances with proper configuration and blueprint registration.

### Blueprint Structure
- **Main Blueprint** (`app/main/`): Core application routes and landing pages
- **Auth Blueprint** (`app/auth/`): SAML authentication, user models, and role management
- **Admin Blueprint** (`app/admin/`): Administrative interface with role-based access control

### Role-Based Access Control (RBAC)
The application implements a comprehensive RBAC system:

- **Roles**: `UserRole` enum defines USER_ADMINISTRATOR, REGULAR_USER, GUEST
- **Permissions**: `Permission` enum defines granular access rights
- **Role Manager**: `RoleManager` class handles role-permission mappings and validation
- **Decorators**: `@admin_required`, `@require_role()`, `@require_permission()` for route protection

### SAML Authentication Architecture
Multi-provider SAML 2.0 authentication supporting Google Workspace and Microsoft Azure AD:

- **Abstract Base**: `SAMLConfig` class defines common SAML configuration interface
- **Provider Configs**: `GoogleSAMLConfig` and `AzureSAMLConfig` implement provider-specific settings
- **Factory Pattern**: `get_saml_config(provider)` returns appropriate configuration instance
- **User Model**: `User.from_saml_attributes()` creates user instances from SAML assertions

### Session-Based User Management
Users are stored in Flask sessions (not database) with role persistence:

- **Session Storage**: `User.save_to_session()` stores user data and roles
- **Session Retrieval**: `User.from_session()` loads authenticated user
- **Role Assignment**: Admins can assign/remove roles via admin interface

### Configuration System
Environment-based configuration using `config/config.py`:

- **Base Config**: Common settings and environment variable loading
- **Environment Configs**: DevelopmentConfig, ProductionConfig, TestingConfig
- **Config Mapping**: `CONFIG_MAP` dictionary for environment selection

## Important Security Considerations

### Production vs Development
- **CRITICAL**: Always set `FLASK_DEBUG=false` in production
- **CRITICAL**: Use strong `SECRET_KEY` (64+ random characters) in production
- Development mode exposes sensitive information and allows code execution

### SAML Integration
- Certificate validation is essential for security
- Clock synchronization between SP and IdP is critical
- URL matching must be exact between configuration and IdP settings

## Key Files and Locations

### Core Application Files
- `app.py`: Application entry point using factory pattern
- `app/__init__.py`: Application factory and blueprint registration
- `config/config.py`: Environment-based configuration classes

### Authentication Module
- `app/auth/models.py`: User model with SAML attribute parsing
- `app/auth/roles.py`: Complete RBAC system (roles, permissions, validation)
- `app/auth/saml_config.py`: SAML provider configurations
- `app/auth/routes.py`: Authentication routes and SAML handlers

### Administration Module
- `app/admin/decorators.py`: Access control decorators for route protection
- `app/admin/user_manager.py`: User management logic and role assignment
- `app/admin/routes.py`: Admin interface routes
- `app/admin/templates/`: Admin UI templates

### Testing
- `tests/test_admin.py`: Admin functionality and access control tests
- `tests/test_roles.py`: Role-based access control system tests
- `tests/test_basic.py`: Basic application functionality tests

### Environment Configuration
- `.env.example`: Template with required environment variables for SAML providers
- `requirements.txt`: Production dependencies including Flask, SQLAlchemy, python3-saml
- `requirements-ci.txt`: CI/CD specific dependencies
