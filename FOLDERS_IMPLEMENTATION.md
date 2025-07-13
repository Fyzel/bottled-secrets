# Folder Management Implementation

This document describes the implementation of the folder management system for Bottled Secrets.

## Overview

The folder management system allows users to create hierarchical folders to organize their secret values. Each folder has access permissions that grant specific users or groups access. By default, only the user creating the folder is granted access.

## Features Implemented

### ✅ Core Models

- **Folder Model** (`app/models.py`): Hierarchical folder structure with parent/child relationships
- **Secret Model** (`app/models.py`): Encrypted secret storage within folders
- **FolderPermission Model** (`app/models.py`): Granular access control system
- **AccessType Enum** (`app/models.py`): Read, Write, Admin permission levels

### ✅ API Endpoints

- `GET /folders/` - Folder browser interface
- `GET /folders/api/folders` - List accessible folders
- `POST /folders/api/folders` - Create new folder
- `GET /folders/api/folders/<id>` - Get folder details with secrets
- `GET /folders/api/folders/<id>/permissions` - Get folder permissions
- `POST /folders/api/folders/<id>/permissions` - Grant folder access
- `POST /folders/api/folders/<id>/secrets` - Create secret in folder

### ✅ User Interface

- **Responsive folder grid** with folder cards showing icons, paths, and statistics
- **Modal dialogs** for creating folders, adding secrets, and managing permissions
- **Hierarchical navigation** with breadcrumbs and folder tree
- **Access level indicators** showing user's permission level for each folder

### ✅ Security Features

- **Role-based access control** integrated with existing permission system
- **Folder-level permissions** with Read, Write, Admin levels
- **Owner-based access** (creators always have admin access)
- **Encrypted secret storage** using Fernet encryption
- **Authentication requirements** for all folder operations

## Database Schema

### Folders Table
```sql
CREATE TABLE folders (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path VARCHAR(1000) NOT NULL UNIQUE,
    icon VARCHAR(50) NOT NULL DEFAULT 'folder',
    description TEXT,
    created_by VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    parent_id INTEGER REFERENCES folders(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

### Secrets Table
```sql
CREATE TABLE secrets (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    encrypted_value TEXT NOT NULL,
    description TEXT,
    folder_id INTEGER NOT NULL REFERENCES folders(id),
    created_by VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

### Permissions Table
```sql
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER NOT NULL REFERENCES folders(id),
    user_email VARCHAR(255) NOT NULL,
    can_read BOOLEAN NOT NULL DEFAULT TRUE,
    can_write BOOLEAN NOT NULL DEFAULT FALSE,
    can_admin BOOLEAN NOT NULL DEFAULT FALSE,
    granted_by VARCHAR(255) NOT NULL,
    granted_at DATETIME NOT NULL
);
```

## Usage Examples

### Creating a Folder
```javascript
const folderData = {
    name: "Production API Keys",
    path: "/production/api-keys",
    icon: "folder-key",
    description: "API keys for production services",
    parent_id: 1
};

const response = await fetch('/folders/api/folders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(folderData)
});
```

### Adding a Secret
```javascript
const secretData = {
    name: "stripe_api_key",
    value: "sk_live_abcdef123456789",
    description: "Stripe payment processing API key"
};

const response = await fetch('/folders/api/folders/1/secrets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(secretData)
});
```

### Granting Access
```javascript
const permissionData = {
    user_email: "developer@company.com",
    access_type: "write"  // read, write, or admin
};

const response = await fetch('/folders/api/folders/1/permissions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(permissionData)
});
```

## Access Control Levels

1. **Read Only**: Can view folder contents and secret names (not values)
2. **Read/Write**: Can view and create/modify secrets within the folder
3. **Admin**: Full access including permission management
4. **Owner**: Creator of folder, always has admin access

## File Structure

```
app/
├── models.py                          # Database models
├── folders/
│   ├── __init__.py                     # Blueprint initialization
│   ├── routes.py                       # API endpoints and views
│   └── templates/
│       └── folders/
│           └── index.html              # Folder management UI
├── static/
│   └── css/
│       └── style.css                   # Updated with folder styles
└── templates/
    └── base.html                       # Updated with folders nav link

tests/
└── test_folders.py                     # Comprehensive test suite

create_tables.py                        # Database table creation script
```

## Integration

The folder system integrates with the existing Bottled Secrets application:

- **Authentication**: Uses existing SAML authentication system
- **Authorization**: Extends existing role-based permission system
- **UI**: Follows existing design patterns and styling
- **Database**: Uses existing SQLAlchemy setup and configuration

## Testing

Comprehensive test suite covers:
- Model validation and business logic
- API endpoint functionality
- Access control enforcement
- Error handling and edge cases
- Integration with existing auth system

Run tests with: `python -m pytest tests/test_folders.py -v`

## Setup

1. Run database migrations: `python create_tables.py`
2. Set encryption key: `export SECRETS_ENCRYPTION_KEY=<base64-key>`
3. Start application: `flask run`
4. Navigate to `/folders/` to access the folder management interface

## Security Considerations

- **Encryption at Rest**: All secret values are encrypted using Fernet symmetric encryption
- **Access Validation**: Every operation validates user permissions
- **Audit Trail**: All permissions track who granted them and when
- **Session Security**: Requires valid authentication session
- **Path Validation**: Folder paths must follow security constraints
- **SQL Injection Protection**: Uses SQLAlchemy ORM with parameterized queries
