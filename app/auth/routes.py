"""Authentication routes for SAML integration.

This module contains route handlers for SAML authentication including
login, logout, ACS (Assertion Consumer Service), and metadata endpoints.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.auth.routes
.. platform:: Unix, Windows
.. synopsis:: SAML authentication route handlers

Example:
    Access authentication routes::

        GET /auth/login/<provider>  - Initiate SAML login
        POST /auth/acs              - SAML assertion consumer
        GET /auth/logout            - Logout user
        GET /auth/metadata          - SAML metadata
"""

import os
from typing import Dict, Any
from flask import request, redirect, url_for, session, render_template, flash, current_app
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from app.auth import bp
from app.auth.saml_config import get_saml_config
from app.auth.models import User

__all__ = ['login', 'acs', 'logout', 'metadata', 'login_required']


def init_saml_auth(req: Dict[str, Any], provider: str) -> OneLogin_Saml2_Auth:
    """Initialize SAML authentication object.

    :param req: Flask request data formatted for SAML
    :type req: Dict[str, Any]
    :param provider: Identity provider name
    :type provider: str
    :returns: Configured SAML authentication object
    :rtype: OneLogin_Saml2_Auth
    :raises ValueError: If provider configuration fails
    """
    try:
        saml_config = get_saml_config(provider)
        settings = saml_config.get_saml_settings()
        return OneLogin_Saml2_Auth(req, settings)
    except Exception as e:
        current_app.logger.error(f"Failed to initialize SAML auth for {provider}: {e}")
        raise ValueError(f"SAML configuration error for {provider}") from e


def prepare_flask_request(request_obj) -> Dict[str, Any]:
    """Prepare Flask request for SAML processing.

    :param request_obj: Flask request object
    :returns: Dictionary formatted for SAML library
    :rtype: Dict[str, Any]
    """
    url_data = request_obj.url.split('?')
    return {
        'https': 'on' if request_obj.scheme == 'https' else 'off',
        'http_host': request_obj.headers.get('Host', ''),
        'server_port': request_obj.environ.get('SERVER_PORT'),
        'script_name': request_obj.path,
        'get_data': request_obj.args.copy(),
        'post_data': request_obj.form.copy(),
        'query_string': url_data[1] if len(url_data) > 1 else ''
    }


@bp.route('/login/<provider>')
def login(provider: str) -> str:
    """Initiate SAML login with specified provider.

    :param provider: Identity provider ('google' or 'azure')
    :type provider: str
    :returns: Redirect to identity provider or error page
    :rtype: str
    :raises ValueError: If provider is not supported

    Example:
        Login with Google::

            GET /auth/login/google

        Login with Azure::

            GET /auth/login/azure
    """
    try:
        req = prepare_flask_request(request)
        auth = init_saml_auth(req, provider)
        
        # Store provider in session for ACS processing
        session['auth_provider'] = provider
        
        return redirect(auth.login())
    
    except ValueError as e:
        current_app.logger.error(f"Login error for {provider}: {e}")
        flash(f"Authentication error: {e}", 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Unexpected login error for {provider}: {e}")
        flash("Authentication service temporarily unavailable", 'error')
        return redirect(url_for('main.index'))


@bp.route('/acs', methods=['POST'])
def acs() -> str:
    """SAML Assertion Consumer Service endpoint.

    Processes SAML responses from identity providers and creates
    user sessions for successfully authenticated users.

    :returns: Redirect to main page or error page
    :rtype: str
    :raises RuntimeError: If SAML response processing fails
    """
    try:
        provider = session.get('auth_provider')
        if not provider:
            flash("Authentication session expired", 'error')
            return redirect(url_for('main.index'))

        req = prepare_flask_request(request)
        auth = init_saml_auth(req, provider)
        
        auth.process_response()
        
        errors = auth.get_errors()
        if not errors:
            # Authentication successful
            attributes = auth.get_attributes()
            current_app.logger.info(f"SAML attributes received: {list(attributes.keys())}")
            
            try:
                user = User.from_saml_attributes(attributes, provider)
                user.save_to_session()
                
                flash(f"Successfully logged in as {user.name}", 'success')
                current_app.logger.info(f"User {user.email} authenticated via {provider}")
                
                # Redirect to originally requested page or main page
                next_page = session.pop('next_page', url_for('main.index'))
                return redirect(next_page)
                
            except ValueError as e:
                current_app.logger.error(f"User creation error: {e}")
                flash("Unable to process user information from identity provider", 'error')
                return redirect(url_for('main.index'))
        else:
            # Authentication failed
            error_msg = f"SAML authentication failed: {', '.join(errors)}"
            current_app.logger.error(error_msg)
            flash("Authentication failed. Please try again.", 'error')
            return redirect(url_for('main.index'))
            
    except Exception as e:
        current_app.logger.error(f"ACS processing error: {e}")
        flash("Authentication processing error", 'error')
        return redirect(url_for('main.index'))


@bp.route('/logout')
def logout() -> str:
    """Logout user and clear session.

    Removes user session data and optionally initiates SAML logout
    with the identity provider.

    :returns: Redirect to main page
    :rtype: str
    """
    try:
        user = User.from_session()
        if user:
            current_app.logger.info(f"User {user.email} logging out")
            
            # Get provider for potential IdP logout
            provider = user.provider
            
            # Clear local session
            User.logout()
            
            # Optionally initiate IdP logout (if configured)
            if os.environ.get('SAML_ENABLE_SLO', 'false').lower() == 'true':
                try:
                    req = prepare_flask_request(request)
                    auth = init_saml_auth(req, provider)
                    return redirect(auth.logout())
                except Exception as e:
                    current_app.logger.warning(f"IdP logout failed: {e}")
            
            flash("Successfully logged out", 'success')
        else:
            flash("You were not logged in", 'info')
            
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        flash("Logout error occurred", 'error')
    
    return redirect(url_for('main.index'))


@bp.route('/metadata')
def metadata() -> str:
    """Provide SAML metadata for service provider.

    Returns XML metadata that identity providers need to configure
    SAML integration with this application.

    :returns: XML metadata response
    :rtype: str
    :raises RuntimeError: If metadata generation fails
    """
    try:
        # Use Google config as default for metadata (both providers use same SP config)
        provider = request.args.get('provider', 'google')
        saml_config = get_saml_config(provider)
        settings = saml_config.get_saml_settings()
        
        metadata = OneLogin_Saml2_Utils.get_metadata(settings)
        
        response = current_app.response_class(
            metadata,
            mimetype='application/xml'
        )
        return response
        
    except Exception as e:
        current_app.logger.error(f"Metadata generation error: {e}")
        return "Metadata generation failed", 500


def login_required(f):
    """Decorator to require authentication for routes.

    :param f: Function to decorate
    :returns: Decorated function that checks authentication
    :raises Unauthorized: If user is not authenticated

    Example:
        Protect a route::

            @bp.route('/protected')
            @login_required
            def protected_view():
                return "This requires authentication"
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.from_session()
        if not user:
            # Store requested page for post-login redirect
            session['next_page'] = request.url
            flash("Please log in to access this page", 'info')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    
    return decorated_function