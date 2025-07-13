"""Routes for folder management in Bottled Secrets Flask application.

This module defines all routes for creating, managing, and accessing folders
and their associated secrets with proper access control.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.folders.routes
.. platform:: Unix, Windows
.. synopsis:: Folder management routes and API endpoints
"""

from typing import List
from flask import request, jsonify, render_template, redirect, url_for
from app.folders import bp
from app.models import db, Folder, Secret, FolderPermission, AccessType
from app.auth.models import User
from app.admin.decorators import require_permission
from app.auth.roles import Permission


@bp.route("/")
def index():
    """Display folder browser interface.

    :returns: Rendered folder browser template
    :rtype: str
    """
    user = User.from_session()
    if not user:
        return redirect(url_for("auth.login"))

    # Get root folders accessible to user
    accessible_folders = get_accessible_folders(user.email)

    return render_template("folders/index.html", folders=accessible_folders, user=user)


@bp.route("/api/folders", methods=["GET"])
@require_permission(Permission.MANAGE_SECRETS)
def api_list_folders():
    """API endpoint to list folders accessible to current user.

    :returns: JSON response with folders list
    :rtype: flask.Response
    """
    user = User.from_session()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    try:
        folders = get_accessible_folders(user.email)
        folders_data = []

        for folder in folders:
            folders_data.append(
                {
                    "id": folder.id,
                    "name": folder.name,
                    "path": folder.path,
                    "icon": folder.icon,
                    "description": folder.description,
                    "created_by": folder.created_by,
                    "created_at": folder.created_at.isoformat(),
                    "updated_at": folder.updated_at.isoformat(),
                    "parent_id": folder.parent_id,
                    "children_count": len(folder.get_children()),
                    "secrets_count": len(folder.get_secrets()),
                    "access_level": get_user_access_level(folder, user.email),
                }
            )

        return jsonify({"folders": folders_data, "total": len(folders_data)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/folders", methods=["POST"])
@require_permission(Permission.MANAGE_SECRETS)
def api_create_folder():
    """API endpoint to create a new folder.

    :returns: JSON response with created folder data
    :rtype: flask.Response
    """
    user = User.from_session()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON data required"}), 400

        # Validate required fields
        name = data.get("name", "").strip()
        path = data.get("path", "").strip()

        if not name:
            return jsonify({"error": "Folder name is required"}), 400

        if not path:
            return jsonify({"error": "Folder path is required"}), 400

        if not path.startswith("/"):
            return jsonify({"error": 'Path must start with "/"'}), 400

        # Check if path already exists
        existing_folder = Folder.query.filter_by(path=path, is_active=True).first()
        if existing_folder:
            return jsonify({"error": "A folder with this path already exists"}), 409

        # Validate parent folder if specified
        parent_id = data.get("parent_id")
        if parent_id:
            parent_folder = Folder.query.filter_by(id=parent_id, is_active=True).first()
            if not parent_folder:
                return jsonify({"error": "Parent folder not found"}), 404

            # Check if user has write access to parent folder
            if not parent_folder.has_access(user.email, AccessType.WRITE):
                return (
                    jsonify(
                        {"error": "Insufficient permissions to create folder in parent"}
                    ),
                    403,
                )

        # Create the folder
        folder = Folder(
            name=name,
            path=path,
            created_by=user.email,
            icon=data.get("icon", "folder"),
            description=data.get("description"),
            parent_id=parent_id,
        )

        db.session.add(folder)
        db.session.commit()

        return (
            jsonify(
                {
                    "id": folder.id,
                    "name": folder.name,
                    "path": folder.path,
                    "icon": folder.icon,
                    "description": folder.description,
                    "created_by": folder.created_by,
                    "created_at": folder.created_at.isoformat(),
                    "parent_id": folder.parent_id,
                    "message": "Folder created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/folders/<int:folder_id>", methods=["GET"])
@require_permission(Permission.MANAGE_SECRETS)
def api_get_folder(folder_id: int):
    """API endpoint to get folder details.

    :param folder_id: ID of the folder to retrieve
    :type folder_id: int
    :returns: JSON response with folder data
    :rtype: flask.Response
    """
    user = User.from_session()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    try:
        folder = Folder.query.filter_by(id=folder_id, is_active=True).first()
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        # Check read access
        if not folder.has_access(user.email, AccessType.READ):
            return jsonify({"error": "Insufficient permissions"}), 403

        # Get folder children and secrets
        children = folder.get_children()
        secrets = folder.get_secrets()

        folder_data = {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path,
            "icon": folder.icon,
            "description": folder.description,
            "created_by": folder.created_by,
            "created_at": folder.created_at.isoformat(),
            "updated_at": folder.updated_at.isoformat(),
            "parent_id": folder.parent_id,
            "access_level": get_user_access_level(folder, user.email),
            "children": [
                {
                    "id": child.id,
                    "name": child.name,
                    "path": child.path,
                    "icon": child.icon,
                    "access_level": get_user_access_level(child, user.email),
                }
                for child in children
                if child.has_access(user.email, AccessType.READ)
            ],
            "secrets": [
                {
                    "id": secret.id,
                    "name": secret.name,
                    "description": secret.description,
                    "created_by": secret.created_by,
                    "created_at": secret.created_at.isoformat(),
                    "updated_at": secret.updated_at.isoformat(),
                }
                for secret in secrets
            ],
        }

        return jsonify(folder_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/folders/<int:folder_id>/permissions", methods=["GET"])
@require_permission(Permission.MANAGE_SECRETS)
def api_get_folder_permissions(folder_id: int):
    """API endpoint to get folder permissions.

    :param folder_id: ID of the folder
    :type folder_id: int
    :returns: JSON response with permissions data
    :rtype: flask.Response
    """
    user = User.from_session()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    try:
        folder = Folder.query.filter_by(id=folder_id, is_active=True).first()
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        # Check admin access
        if not folder.has_access(user.email, AccessType.ADMIN):
            return jsonify({"error": "Insufficient permissions"}), 403

        permissions_data = []
        for permission in folder.permissions:
            permissions_data.append(
                {
                    "id": permission.id,
                    "user_email": permission.user_email,
                    "can_read": permission.can_read,
                    "can_write": permission.can_write,
                    "can_admin": permission.can_admin,
                    "access_level": permission.get_access_level(),
                    "granted_by": permission.granted_by,
                    "granted_at": permission.granted_at.isoformat(),
                }
            )

        return jsonify(
            {
                "permissions": permissions_data,
                "folder": {
                    "id": folder.id,
                    "name": folder.name,
                    "path": folder.path,
                    "created_by": folder.created_by,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/folders/<int:folder_id>/permissions", methods=["POST"])
@require_permission(Permission.MANAGE_SECRETS)
def api_grant_folder_permission(folder_id: int):
    """API endpoint to grant folder permission to user.

    :param folder_id: ID of the folder
    :type folder_id: int
    :returns: JSON response with operation result
    :rtype: flask.Response
    """
    user = User.from_session()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    try:
        folder = Folder.query.filter_by(id=folder_id, is_active=True).first()
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        # Check admin access
        if not folder.has_access(user.email, AccessType.ADMIN):
            return jsonify({"error": "Insufficient permissions"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        user_email = data.get("user_email", "").strip()
        access_type = data.get("access_type", "").strip()

        if not user_email:
            return jsonify({"error": "User email is required"}), 400

        if access_type not in ["read", "write", "admin"]:
            return jsonify({"error": "Invalid access type"}), 400

        # Grant permission
        access_enum = AccessType(access_type)
        folder.grant_access(user_email, access_enum, user.email)

        db.session.commit()

        return jsonify(
            {
                "message": f"{access_type.title()} access granted to {user_email}",
                "user_email": user_email,
                "access_type": access_type,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/folders/<int:folder_id>/secrets", methods=["POST"])
@require_permission(Permission.MANAGE_SECRETS)
def api_create_secret(folder_id: int):
    """API endpoint to create a secret in a folder.

    :param folder_id: ID of the folder
    :type folder_id: int
    :returns: JSON response with created secret data
    :rtype: flask.Response
    """
    user = User.from_session()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    try:
        folder = Folder.query.filter_by(id=folder_id, is_active=True).first()
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        # Check write access
        if not folder.has_access(user.email, AccessType.WRITE):
            return jsonify({"error": "Insufficient permissions"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        name = data.get("name", "").strip()
        value = data.get("value", "").strip()

        if not name:
            return jsonify({"error": "Secret name is required"}), 400

        if not value:
            return jsonify({"error": "Secret value is required"}), 400

        # Check if secret name already exists in folder
        existing_secret = Secret.query.filter_by(
            folder_id=folder_id, name=name, is_active=True
        ).first()

        if existing_secret:
            return (
                jsonify(
                    {"error": "A secret with this name already exists in the folder"}
                ),
                409,
            )

        # Create the secret
        secret = Secret(
            name=name,
            value=value,
            folder_id=folder_id,
            created_by=user.email,
            description=data.get("description"),
        )

        db.session.add(secret)
        db.session.commit()

        return (
            jsonify(
                {
                    "id": secret.id,
                    "name": secret.name,
                    "description": secret.description,
                    "folder_id": secret.folder_id,
                    "created_by": secret.created_by,
                    "created_at": secret.created_at.isoformat(),
                    "message": "Secret created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def get_accessible_folders(user_email: str) -> List[Folder]:
    """Get all folders accessible to a user.

    :param user_email: User's email address
    :type user_email: str
    :returns: List of accessible folders
    :rtype: List[Folder]
    """
    # Get folders created by user
    owned_folders = Folder.query.filter_by(created_by=user_email, is_active=True).all()

    # Get folders with explicit permissions
    permitted_folders = (
        db.session.query(Folder)
        .join(FolderPermission)
        .filter(FolderPermission.user_email == user_email, Folder.is_active == True)
        .all()
    )

    # Combine and deduplicate
    all_folders = {f.id: f for f in owned_folders + permitted_folders}

    return list(all_folders.values())


def get_user_access_level(folder: Folder, user_email: str) -> str:
    """Get user's access level for a folder.

    :param folder: The folder to check
    :type folder: Folder
    :param user_email: User's email address
    :type user_email: str
    :returns: Access level description
    :rtype: str
    """
    if folder.created_by == user_email:
        return "Owner"

    for permission in folder.permissions:
        if permission.user_email == user_email:
            return permission.get_access_level()

    return "No Access"
