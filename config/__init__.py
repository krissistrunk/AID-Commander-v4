"""
Configuration package for AID Commander v4.0
"""

from .settings import get_settings, validate_configuration, get_ai_provider_config

__all__ = ['get_settings', 'validate_configuration', 'get_ai_provider_config']