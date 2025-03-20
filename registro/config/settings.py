"""
Centralized configuration for the Registro library.

This module provides a unified interface for configuring Registro through
environment variables or programmatic settings. It serves as the source of
truth for library-wide settings.

The settings can be configured in these ways (in order of precedence):
1. Direct modification of Settings attributes
2. Environment variables
3. Default values

Usage:
    from registro.config import settings
    
    # Read a setting
    rid_prefix = settings.RID_PREFIX
    
    # Change a setting programmatically
    settings.RID_PREFIX = "custom"
    
    # Environment variable override (set before import)
    # export REGISTRO_RID_PREFIX="custom"
"""

import logging
import os
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo, available_timezones

logger = logging.getLogger(__name__)

class Settings:
    """
    Configuration settings for the Registro library.
    
    Attributes:
        RID_PREFIX (str): Prefix for resource identifiers (default: "ri")
        DEFAULT_SERVICE (str): Default service name (default: "registro")
        DEFAULT_INSTANCE (str): Default instance name (default: "main")
        TIMEZONE (ZoneInfo): Default timezone for timestamps (default: UTC)
    """
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize settings from environment variables or defaults."""
        # RID Prefix - used in all resource identifiers
        self._rid_prefix = os.getenv("REGISTRO_RID_PREFIX", "ri")
        
        # Default service and instance names
        self._default_service = os.getenv("REGISTRO_DEFAULT_SERVICE", "registro")
        self._default_instance = os.getenv("REGISTRO_DEFAULT_INSTANCE", "main")
        
        # Default timezone
        tz_name = os.getenv("REGISTRO_TIMEZONE", "UTC")
        try:
            self._timezone = ZoneInfo(tz_name)
        except Exception as e:
            logger.warning(f"Invalid timezone {tz_name}, falling back to UTC: {e}")
            self._timezone = ZoneInfo("UTC")
    
    @property
    def RID_PREFIX(self) -> str:
        """Get the RID prefix."""
        return self._rid_prefix
    
    @RID_PREFIX.setter
    def RID_PREFIX(self, value: str):
        """Set the RID prefix, with validation."""
        if not isinstance(value, str):
            raise TypeError(f"RID_PREFIX must be a string, got {type(value).__name__}")
        if not value.isalnum() or not value.islower() or len(value) > 10:
            raise ValueError("RID_PREFIX must be alphanumeric, lowercase, and max 10 chars")
        self._rid_prefix = value
    
    @property
    def DEFAULT_SERVICE(self) -> str:
        """Get the default service name."""
        return self._default_service
    
    @DEFAULT_SERVICE.setter
    def DEFAULT_SERVICE(self, value: str):
        """Set the default service name, with validation."""
        if not isinstance(value, str):
            raise TypeError(f"DEFAULT_SERVICE must be a string, got {type(value).__name__}")
        if not value.islower() or not value.replace("-", "").isalnum():
            raise ValueError("DEFAULT_SERVICE must contain only lowercase letters, numbers, and hyphens")
        self._default_service = value
    
    @property
    def DEFAULT_INSTANCE(self) -> str:
        """Get the default instance name."""
        return self._default_instance
    
    @DEFAULT_INSTANCE.setter
    def DEFAULT_INSTANCE(self, value: str):
        """Set the default instance name, with validation."""
        if not isinstance(value, str):
            raise TypeError(f"DEFAULT_INSTANCE must be a string, got {type(value).__name__}")
        if not value.islower() or not value.replace("-", "").isalnum():
            raise ValueError("DEFAULT_INSTANCE must contain only lowercase letters, numbers, and hyphens")
        self._default_instance = value
    
    @property
    def TIMEZONE(self) -> ZoneInfo:
        """Get the timezone."""
        return self._timezone
    
    @TIMEZONE.setter
    def TIMEZONE(self, value: str):
        """Set the timezone, with validation."""
        if isinstance(value, str):
            try:
                self._timezone = ZoneInfo(value)
            except Exception as e:
                raise ValueError(f"Invalid timezone {value}: {e}")
        elif isinstance(value, ZoneInfo):
            self._timezone = value
        else:
            raise TypeError(f"TIMEZONE must be a string or ZoneInfo, got {type(value).__name__}")
    
    def as_dict(self) -> Dict[str, Any]:
        """Return all settings as a dictionary."""
        return {
            "RID_PREFIX": self._rid_prefix,
            "DEFAULT_SERVICE": self._default_service,
            "DEFAULT_INSTANCE": self._default_instance,
            "TIMEZONE": str(self._timezone),
        }
    
    def reset(self):
        """Reset all settings to their default/environment values."""
        self._initialize()

# Create a singleton instance
settings = Settings()

# Export the settings instance
__all__ = ["settings"] 