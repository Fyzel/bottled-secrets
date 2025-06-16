"""Administration routes for user and role management.

This module contains route handlers for the administration interface,
including user management, role assignment, and system overview.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.admin.routes
.. platform:: Unix, Windows
.. synopsis:: Administration route handlers

Example:
    Access admin routes::

        GET /admin/              - Admin dashboard
        GET /admin/users         - User management
        POST /admin/users/assign - Assign role to user
"""

from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from app.admin import bp
from app.admin.decorators import admin_required, require_permission
from app.admin.user_manager import UserManager
from app.auth.models import User
from app.auth.roles import UserRole, Permission

__all__ = ['dashboard', 'list_users', 'assign_role', 'remove_role', 'user_details']


@bp.route('/')
@bp.route('/dashboard')
@admin_required
def dashboard() -> str:
    """Render the administration dashboard.

    Provides an overview of system statistics, user counts,
    and administrative functions.

    :returns: Rendered admin dashboard template
    :rtype: str
    :raises Unauthorized: If user is not an administrator
    """
    try:
        user_manager = UserManager()
        current_user = User.from_session()
        
        # Get system statistics
        all_users = user_manager.get_all_users()
        role_stats = user_manager.get_role_statistics()
        
        stats = {
            'total_users': len(all_users),
            'administrators': role_stats.get(UserRole.USER_ADMINISTRATOR.value, 0),
            'regular_users': role_stats.get(UserRole.REGULAR_USER.value, 0),
            'guest_users': role_stats.get(UserRole.GUEST.value, 0),
            'recent_users': sorted(all_users, key=lambda x: x.get('last_seen', ''), reverse=True)[:5]
        }
        
        current_app.logger.info(f"Admin dashboard accessed by {current_user.email}")
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             current_user=current_user)
    
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        flash("Error loading dashboard", 'error')
        return redirect(url_for('main.index'))


@bp.route('/users')
@require_permission([Permission.VIEW_ADMIN_PANEL, Permission.VIEW_USER_LIST])
def list_users() -> str:
    """List all users in the system.

    Displays a table of all users with their roles and basic information.
    Allows role management for administrators.

    :returns: Rendered user list template
    :rtype: str
    :raises Unauthorized: If user lacks required permissions
    """
    try:
        user_manager = UserManager()
        current_user = User.from_session()
        
        users = user_manager.get_all_users()
        available_roles = UserRole.get_all_roles()
        
        # Add role display names for template
        role_choices = []
        for role in available_roles:
            role_choices.append({
                'value': role.value,
                'display': UserRole.get_role_display_name(role)
            })
        
        current_app.logger.info(f"User list accessed by {current_user.email}")
        
        return render_template('admin/users.html',
                             users=users,
                             role_choices=role_choices,
                             current_user=current_user)
    
    except Exception as e:
        current_app.logger.error(f"User list error: {e}")
        flash("Error loading user list", 'error')
        return redirect(url_for('admin.dashboard'))


@bp.route('/users/assign', methods=['POST'])
@require_permission(Permission.MANAGE_ROLES)
def assign_role() -> str:
    """Assign role to a user.

    Processes role assignment requests from the admin interface.
    Validates permissions and updates user roles.

    :returns: Redirect to user list with status message
    :rtype: str
    :raises Unauthorized: If user cannot manage roles
    """
    try:
        user_manager = UserManager()
        current_user = User.from_session()
        
        target_email = request.form.get('target_email', '').strip()
        role_value = request.form.get('role', '').strip()
        
        if not target_email or not role_value:
            flash("Email and role are required", 'error')
            return redirect(url_for('admin.list_users'))
        
        try:
            role = UserRole(role_value)
        except ValueError:
            flash(f"Invalid role: {role_value}", 'error')
            return redirect(url_for('admin.list_users'))
        
        success, message = user_manager.assign_role_to_user(
            current_user, target_email, role
        )
        
        if success:
            flash(message, 'success')
            current_app.logger.info(
                f"Role {role.value} assigned to {target_email} by {current_user.email}"
            )
        else:
            flash(message, 'error')
        
        return redirect(url_for('admin.list_users'))
    
    except Exception as e:
        current_app.logger.error(f"Role assignment error: {e}")
        flash("Error assigning role", 'error')
        return redirect(url_for('admin.list_users'))


@bp.route('/users/remove', methods=['POST'])
@require_permission(Permission.MANAGE_ROLES)
def remove_role() -> str:
    """Remove role from a user.

    Processes role removal requests from the admin interface.
    Validates permissions and updates user roles.

    :returns: Redirect to user list with status message
    :rtype: str
    :raises Unauthorized: If user cannot manage roles
    """
    try:
        user_manager = UserManager()
        current_user = User.from_session()
        
        target_email = request.form.get('target_email', '').strip()
        role_value = request.form.get('role', '').strip()
        
        if not target_email or not role_value:
            flash("Email and role are required", 'error')
            return redirect(url_for('admin.list_users'))
        
        try:
            role = UserRole(role_value)
        except ValueError:
            flash(f"Invalid role: {role_value}", 'error')
            return redirect(url_for('admin.list_users'))
        
        success, message = user_manager.remove_role_from_user(
            current_user, target_email, role
        )
        
        if success:
            flash(message, 'success')
            current_app.logger.info(
                f"Role {role.value} removed from {target_email} by {current_user.email}"
            )
        else:
            flash(message, 'error')
        
        return redirect(url_for('admin.list_users'))
    
    except Exception as e:
        current_app.logger.error(f"Role removal error: {e}")
        flash("Error removing role", 'error')
        return redirect(url_for('admin.list_users'))


@bp.route('/users/<email>')
@require_permission(Permission.VIEW_USER_LIST)
def user_details(email: str) -> str:
    """Display detailed information about a specific user.

    Shows user profile, roles, permissions, and activity history.

    :param email: Email address of the user
    :type email: str
    :returns: Rendered user details template
    :rtype: str
    :raises Unauthorized: If user cannot view user details
    :raises NotFound: If user is not found
    """
    try:
        user_manager = UserManager()
        current_user = User.from_session()
        
        user_data = user_manager.get_user_by_email(email)
        if not user_data:
            flash(f"User {email} not found", 'error')
            return redirect(url_for('admin.list_users'))
        
        # Get user roles and permissions
        user_roles = user_manager.get_user_roles(email)
        
        current_app.logger.info(f"User details for {email} accessed by {current_user.email}")
        
        return render_template('admin/user_details.html',
                             user_data=user_data,
                             user_roles=user_roles,
                             current_user=current_user)
    
    except Exception as e:
        current_app.logger.error(f"User details error: {e}")
        flash("Error loading user details", 'error')
        return redirect(url_for('admin.list_users'))


@bp.route('/api/users')
@require_permission(Permission.VIEW_USER_LIST)
def api_users() -> str:
    """API endpoint to get user list as JSON.

    Provides user data for AJAX requests and API integrations.

    :returns: JSON response with user list
    :rtype: str
    :raises Unauthorized: If user cannot view users
    """
    try:
        user_manager = UserManager()
        users = user_manager.get_all_users()
        
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
    
    except Exception as e:
        current_app.logger.error(f"API users error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/roles/stats')
@admin_required
def api_role_stats() -> str:
    """API endpoint to get role statistics as JSON.

    Provides role distribution data for dashboard charts and reports.

    :returns: JSON response with role statistics
    :rtype: str
    :raises Unauthorized: If user is not an administrator
    """
    try:
        user_manager = UserManager()
        stats = user_manager.get_role_statistics()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        current_app.logger.error(f"API role stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500