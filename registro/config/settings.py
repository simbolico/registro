"""
Configuration settings for the Registro library.

This module provides centralized configuration management for Registro,
including pattern strings, compiled patterns, and reserved words.
"""

import os
import re
import json
from typing import Dict, Optional, Pattern, Set
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from zoneinfo import ZoneInfo

class Settings(BaseModel):
    """
    Configuration settings for Registro.
    
    Handles pattern strings, compiled patterns, reserved words,
    and service/instance defaults.
    """
    
    # Default RID components
    RID_PREFIX: str = "ri"
    DEFAULT_SERVICE: str = "default"
    DEFAULT_INSTANCE: str = "prod"
    TIMEZONE: ZoneInfo = Field(default_factory=lambda: ZoneInfo(os.getenv("REGISTRO_TIMEZONE", "UTC")))
    
    # Environment validation
    ENVIRONMENT: Optional[str] = Field(
        default_factory=lambda: os.getenv("REGISTRO_ENVIRONMENT"),
        description="Application environment (dev, staging, prod)"
    )
    DEBUG: bool = Field(
        default_factory=lambda: os.getenv("REGISTRO_DEBUG", "false").lower() == "true",
        description="Enable debug mode for additional logging"
    )
    
    # Model config to allow private attributes
    model_config = {"extra": "allow"}
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize pattern attributes after super().__init__
        self._pattern_rid_prefix: str = r"^[a-z][a-z0-9-]{0,9}$"
        self._pattern_service: str = r"^[a-z][a-z-]{0,49}$"
        self._pattern_instance: str = r"^[a-z0-9][a-z0-9-]{0,49}$"
        self._pattern_type: str = r"^[a-z][a-z-]{0,49}$"
        self._pattern_locator: str = r"^[0-9A-HJ-KM-NPQRSTVWXYZ]{26}$"
        self._pattern_api_name_object_type: str = r"^(?=.{1,100}$)[A-Z][A-Za-z0-9]*$"
        self._pattern_api_name_link_type: str = r"^(?=.{1,100}$)[a-z][A-Za-z0-9]*$"
        self._pattern_api_name_action_type: str = r"^(?=.{1,100}$)[A-Za-z][A-Za-z0-9_-]*$"
        self._pattern_api_name_query_type: str = r"^(?=.{1,100}$)[a-z][A-Za-z0-9]*$"
        
        self._compiled_patterns_cache: Dict[str, Pattern[str]] = {}
        self._reserved_words: Set[str] = {
            "new", "edit", "delete", "list", "search", "create",
            "update", "remove", "get", "set", "add", "clear", "null"
        }
        self._api_name_patterns_by_type: Dict[str, str] = {
            "object-type": "API_NAME_OBJECT_TYPE",
            "link-type": "API_NAME_LINK_TYPE", 
            "action-type": "API_NAME_ACTION_TYPE",
            "query-type": "API_NAME_QUERY_TYPE",
            "default": "API_NAME_ACTION_TYPE"
        }
        self._initialize()
    
    def _validate_pattern(self, name: str, pattern: str) -> None:
        """Internal method to validate a regex pattern."""
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern for {name}: {e}")

    def _initialize(self) -> None:
        """Initialize settings from environment variables."""
        # Load RID components
        self.RID_PREFIX = os.getenv("REGISTRO_RID_PREFIX", self.RID_PREFIX)
        self.DEFAULT_SERVICE = os.getenv("REGISTRO_DEFAULT_SERVICE", self.DEFAULT_SERVICE)
        self.DEFAULT_INSTANCE = os.getenv("REGISTRO_DEFAULT_INSTANCE", self.DEFAULT_INSTANCE)
        
        # Define pattern names directly since we're not using field attributes
        pattern_names = [
            "rid_prefix", "service", "instance", "type", "locator",
            "api_name_object_type", "api_name_link_type", 
            "api_name_action_type", "api_name_query_type"
        ]
        
        # Load pattern strings from environment
        for pattern_name in pattern_names:
            env_var = f"REGISTRO_PATTERN_{pattern_name.upper()}"
            if env_value := os.getenv(env_var):
                # Validate pattern before setting it
                self._validate_pattern(pattern_name, env_value)
                setattr(self, f"_pattern_{pattern_name}", env_value)
        
        # Validate all default patterns
        for pattern_name in pattern_names:
            pattern_value = getattr(self, f"_pattern_{pattern_name}")
            self._validate_pattern(pattern_name, pattern_value)
        
        # Load reserved words
        if reserved_words := os.getenv("REGISTRO_RESERVED_WORDS"):
            try:
                self._reserved_words = set(word.strip() for word in reserved_words.split(","))
            except Exception:
                pass
                
        # Load API name pattern mapping
        if mapping := os.getenv("REGISTRO_API_NAME_MAPPING"):
            try:
                self._api_name_patterns_by_type.update(json.loads(mapping))
            except Exception:
                pass
        
    def get_pattern_string(self, name: str) -> Optional[str]:
        """Get the pattern string for a given name."""
        # Map common pattern names to their attribute names
        pattern_mapping = {
            "RID_PREFIX": "rid_prefix",
            "SERVICE": "service",
            "INSTANCE": "instance",
            "TYPE": "type",
            "LOCATOR": "locator",
            "API_NAME_OBJECT_TYPE": "api_name_object_type",
            "API_NAME_LINK_TYPE": "api_name_link_type",
            "API_NAME_ACTION_TYPE": "api_name_action_type",
            "API_NAME_QUERY_TYPE": "api_name_query_type"
        }
        
        mapped_name = pattern_mapping.get(name, name.lower())
        attr_name = f"_pattern_{mapped_name}"
        return getattr(self, attr_name, None)

    def get_compiled_pattern(self, name: str) -> Optional[Pattern[str]]:
        """Get or compile the regex pattern for a given name."""
        # First check cache
        if name in self._compiled_patterns_cache:
            return self._compiled_patterns_cache[name]
            
        # Get the pattern string
        if pattern_str := self.get_pattern_string(name):
            try:
                pattern = re.compile(pattern_str)
                self._compiled_patterns_cache[name] = pattern
                return pattern
            except re.error:
                return None
        return None

    def set_pattern(self, name: str, pattern_string: str) -> None:
        """Set a pattern string and clear its compiled cache."""
        attr_name = f"_pattern_{name.lower()}"
        if hasattr(self, attr_name):
            # Validate pattern using our validation method
            self._validate_pattern(name, pattern_string)
            setattr(self, attr_name, pattern_string)
            self._compiled_patterns_cache.pop(name.upper(), None)
        else:
            raise ValueError(f"Unknown pattern name: {name}")

    @property
    def RESERVED_WORDS(self) -> Set[str]:
        """Get the set of reserved words."""
        return self._reserved_words.copy()

    @RESERVED_WORDS.setter
    def RESERVED_WORDS(self, words: Set[str]) -> None:
        """Set the reserved words."""
        self._reserved_words = set(words)

    @property
    def API_NAME_PATTERNS_BY_TYPE(self) -> Dict[str, str]:
        """Get the API name pattern mapping."""
        return self._api_name_patterns_by_type.copy()

    @API_NAME_PATTERNS_BY_TYPE.setter 
    def API_NAME_PATTERNS_BY_TYPE(self, mapping: Dict[str, str]) -> None:
        """Set the API name pattern mapping."""
        self._api_name_patterns_by_type = dict(mapping)
    
    def validate_environment(self, allowed_environments: Set[str] = None) -> bool:
        """
        Validate that the current environment is allowed.
        
        Args:
            allowed_environments: Set of allowed environment names.
                                If None, allows: dev, staging, prod
        
        Returns:
            bool: True if environment is valid, False otherwise
        """
        if allowed_environments is None:
            allowed_environments = {"dev", "staging", "prod", "development", "production"}
        
        if self.ENVIRONMENT and self.ENVIRONMENT not in allowed_environments:
            if self.DEBUG:
                import warnings
                warnings.warn(
                    f"Environment '{self.ENVIRONMENT}' is not in allowed set: {allowed_environments}",
                    UserWarning
                )
            return False
        
        return True
    
    def get_effective_instance(self) -> str:
        """
        Get the effective instance name based on environment.
        
        Returns:
            str: Effective instance name
        """
        if self.ENVIRONMENT:
            env_map = {
                "development": "dev",
                "dev": "dev",
                "staging": "staging",
                "stage": "staging",
                "production": "prod",
                "prod": "prod",
            }
            return env_map.get(self.ENVIRONMENT.lower(), self.DEFAULT_INSTANCE)
        
        return self.DEFAULT_INSTANCE

# Create global settings instance
settings = Settings()
