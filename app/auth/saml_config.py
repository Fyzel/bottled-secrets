"""SAML configuration module for authentication providers.

This module defines SAML configuration classes for different identity providers
including Google SAML and Microsoft Azure SAML integration.

.. moduleauthor:: Bottled Secrets Team
.. module:: app.auth.saml_config
.. platform:: Unix, Windows
.. synopsis:: SAML identity provider configurations

Example:
    Get SAML settings for Google::

        config = GoogleSAMLConfig()
        settings = config.get_saml_settings()

    Get SAML settings for Azure::

        config = AzureSAMLConfig()
        settings = config.get_saml_settings()
"""

import os
from typing import Dict, Any
from abc import ABC, abstractmethod

__all__ = ['SAMLConfig', 'GoogleSAMLConfig', 'AzureSAMLConfig', 'get_saml_config']


class SAMLConfig(ABC):
    """Abstract base class for SAML configuration.

    This class defines the interface for SAML configuration providers
    and common configuration settings.

    :cvar BASE_URL: Base URL of the application
    :type BASE_URL: str
    """

    def __init__(self) -> None:
        """Initialize SAML configuration with base settings.

        :raises ValueError: If required environment variables are missing
        """
        self.base_url: str = os.environ.get('BASE_URL', 'http://localhost:5000')
        self.entity_id: str = os.environ.get('SAML_ENTITY_ID', f'{self.base_url}/auth/metadata')

    @abstractmethod
    def get_saml_settings(self) -> Dict[str, Any]:
        """Get SAML settings dictionary for the identity provider.

        :returns: Dictionary containing SAML configuration settings
        :rtype: Dict[str, Any]
        :raises NotImplementedError: If not implemented by subclass
        """

    def get_sp_settings(self) -> Dict[str, Any]:
        """Get Service Provider (SP) common settings.

        :returns: Dictionary containing SP configuration
        :rtype: Dict[str, Any]
        """
        return {
            "entityId": self.entity_id,
            "assertionConsumerService": {
                "url": f"{self.base_url}/auth/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "singleLogoutService": {
                "url": f"{self.base_url}/auth/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": os.environ.get('SAML_SP_X509_CERT', ''),
            "privateKey": os.environ.get('SAML_SP_PRIVATE_KEY', '')
        }


class GoogleSAMLConfig(SAMLConfig):
    """Google SAML identity provider configuration.

    This class provides SAML configuration settings specifically for
    Google Workspace SAML integration.

    :cvar SSO_URL: Google SAML SSO endpoint URL
    :type SSO_URL: str
    :cvar ENTITY_ID: Google SAML entity ID
    :type ENTITY_ID: str
    """

    def __init__(self) -> None:
        """Initialize Google SAML configuration.

        :raises ValueError: If required Google SAML environment variables are missing
        """
        super().__init__()
        self.google_entity_id: str = os.environ.get(
            'GOOGLE_SAML_ENTITY_ID',
            'https://accounts.google.com/o/saml2'
        )
        self.google_sso_url: str = os.environ.get(
            'GOOGLE_SAML_SSO_URL',
            'https://accounts.google.com/o/saml2/idp'
        )
        self.google_x509_cert: str = os.environ.get('GOOGLE_SAML_X509_CERT', '')

    def get_saml_settings(self) -> Dict[str, Any]:
        """Get Google SAML settings dictionary.

        :returns: Dictionary containing Google SAML configuration
        :rtype: Dict[str, Any]
        :raises ValueError: If required certificates are missing
        """
        if not self.google_x509_cert:
            raise ValueError("Google SAML X509 certificate is required")

        return {
            "sp": self.get_sp_settings(),
            "idp": {
                "entityId": self.google_entity_id,
                "singleSignOnService": {
                    "url": self.google_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "singleLogoutService": {
                    "url": f"{self.google_sso_url}?GLO=1",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": self.google_x509_cert
            }
        }


class AzureSAMLConfig(SAMLConfig):
    """Microsoft Azure SAML identity provider configuration.

    This class provides SAML configuration settings specifically for
    Microsoft Azure Active Directory SAML integration.

    :cvar TENANT_ID: Azure AD tenant ID
    :type TENANT_ID: str
    :cvar APP_ID: Azure AD application ID
    :type APP_ID: str
    """

    def __init__(self) -> None:
        """Initialize Azure SAML configuration.

        :raises ValueError: If required Azure SAML environment variables are missing
        """
        super().__init__()
        self.tenant_id: str = os.environ.get('AZURE_TENANT_ID', '')
        self.app_id: str = os.environ.get('AZURE_APP_ID', '')
        self.azure_x509_cert: str = os.environ.get('AZURE_SAML_X509_CERT', '')

        if not self.tenant_id:
            raise ValueError("Azure tenant ID is required")
        if not self.app_id:
            raise ValueError("Azure application ID is required")

    def get_saml_settings(self) -> Dict[str, Any]:
        """Get Azure SAML settings dictionary.

        :returns: Dictionary containing Azure SAML configuration
        :rtype: Dict[str, Any]
        :raises ValueError: If required certificates are missing
        """
        if not self.azure_x509_cert:
            raise ValueError("Azure SAML X509 certificate is required")

        azure_base_url = f"https://login.microsoftonline.com/{self.tenant_id}/saml2"

        return {
            "sp": self.get_sp_settings(),
            "idp": {
                "entityId": f"https://sts.windows.net/{self.tenant_id}/",
                "singleSignOnService": {
                    "url": azure_base_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "singleLogoutService": {
                    "url": f"{azure_base_url}/logout",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": self.azure_x509_cert
            }
        }


def get_saml_config(provider: str) -> SAMLConfig:
    """Factory function to get SAML configuration for specified provider.

    :param provider: Identity provider name ('google' or 'azure')
    :type provider: str
    :returns: SAML configuration instance for the provider
    :rtype: SAMLConfig
    :raises ValueError: If provider is not supported

    Example:
        Get Google SAML config::

            config = get_saml_config('google')

        Get Azure SAML config::

            config = get_saml_config('azure')
    """
    providers = {
        'google': GoogleSAMLConfig,
        'azure': AzureSAMLConfig
    }

    if provider.lower() not in providers:
        raise ValueError(f"Unsupported SAML provider: {provider}")

    return providers[provider.lower()]()