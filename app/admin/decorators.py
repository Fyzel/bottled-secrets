"""Access control decorators for administration functions.

This module provides decorators for enforcing role-based access control
in administrative routes and functions.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.admin.decorators
.. platform:: Unix, Windows
.. synopsis:: Role-based access control decorators

Example:
    Protect admin route::

        @bp.route('/users')
        @require_role(UserRole.USER_ADMINISTRATOR)
        def list_users():
            return render_template('users.html')
"""

from functools import wraps
from typing import Callable, List, Union
from flask import flash, redirect, url_for, current_app, request, session
from app.auth.models import User
from app.auth.roles import UserRole, Permission

__all__ = ['require_role', 'require_permission', 'admin_required']


def require_role(required_roles: Union[UserRole, List[UserRole]]) -> Callable:
    """Decorator to require specific user role(s) for route access.

    :param required_roles: Role or list of roles required for access
    :type required_roles: Union[UserRole, List[UserRole]]
    :returns: Decorated function that checks roles
    :rtype: Callable
    :raises Unauthorized: If user doesn't have required role

    Example:
        Require single role::

            @require_role(UserRole.USER_ADMINISTRATOR)
            def admin_function():
                pass

        Require multiple roles (any one)::

            @require_role([UserRole.USER_ADMINISTRATOR, UserRole.REGULAR_USER])
            def multi_role_function():
                pass
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = User.from_session()
            if not user:
                current_app.logger.warning(f"Unauthenticated access attempt to {request.endpoint}")
                flash("Please log in to access this page", 'error')
                session['next_page'] = request.url
                return redirect(url_for('main.index'))

            # Convert single role to list for uniform processing
            roles_to_check = required_roles if isinstance(required_roles, list) else [required_roles]
            
            if not user.user_permissions.has_any_role(roles_to_check):
                current_app.logger.warning(
                    f"User {user.email} attempted to access {request.endpoint} "
                    f"without required roles: {[r.value for r in roles_to_check]}"
                )
                flash("You don't have permission to access this page", 'error')
                return redirect(url_for('main.index'))

            current_app.logger.info(f"User {user.email} accessed {request.endpoint}")
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_permission(required_permissions: Union[Permission, List[Permission]]) -> Callable:
    """Decorator to require specific permission(s) for route access.

    :param required_permissions: Permission or list of permissions required
    :type required_permissions: Union[Permission, List[Permission]]
    :returns: Decorated function that checks permissions
    :rtype: Callable
    :raises Unauthorized: If user doesn't have required permission

    Example:
        Require single permission::

            @require_permission(Permission.MANAGE_USERS)
            def manage_users():
                pass

        Require multiple permissions (all required)::

            @require_permission([Permission.MANAGE_USERS, Permission.VIEW_ADMIN_PANEL])
            def advanced_admin():
                pass
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = User.from_session()
            if not user:
                current_app.logger.warning(f"Unauthenticated access attempt to {request.endpoint}")
                flash("Please log in to access this page", 'error')
                session['next_page'] = request.url
                return redirect(url_for('main.index'))

            # Convert single permission to list for uniform processing
            perms_to_check = (required_permissions if isinstance(required_permissions, list) 
                             else [required_permissions])
            
            # Check if user has ALL required permissions
            missing_permissions = []
            for perm in perms_to_check:
                if not user.has_permission(perm):
                    missing_permissions.append(perm.value)
            
            if missing_permissions:
                current_app.logger.warning(
                    f"User {user.email} attempted to access {request.endpoint} "
                    f"without required permissions: {missing_permissions}"
                )
                flash("You don't have permission to access this page", 'error')
                return redirect(url_for('main.index'))

            current_app.logger.info(f"User {user.email} accessed {request.endpoint}")
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator shorthand for requiring User Administrator role.

    This is equivalent to @require_role(UserRole.USER_ADMINISTRATOR)
    but provides a more convenient syntax for admin-only routes.

    :param f: Function to decorate
    :type f: Callable
    :returns: Decorated function
    :rtype: Callable

    Example:
        Protect admin route::

            @bp.route('/admin')
            @admin_required
            def admin_dashboard():
                return render_template('admin.html')
    """
    return require_role(UserRole.USER_ADMINISTRATOR)(f)


def check_user_access(user: User, required_role: UserRole) -> tuple[bool, str]:
    """Check if user has access based on role requirements.

    This function provides programmatic access control checking
    without the decorator pattern.

    :param user: User to check access for
    :type user: User
    :param required_role: Role required for access
    :type required_role: UserRole
    :returns: Tuple of (has_access, error_message)
    :rtype: tuple[bool, str]

    Example:
        Check access in view logic::

            user = User.from_session()
            has_access, error = check_user_access(user, UserRole.USER_ADMINISTRATOR)
            if not has_access:
                flash(error, 'error')
                return redirect(url_for('main.index'))
    """
    if not user:
        return False, "Authentication required"
    
    if not user.has_role(required_role):
        return False, f"Role '{required_role.value}' required"
    
    return True, ""