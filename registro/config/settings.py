"""
Configuration settings for the Registro library.

This module provides centralized configuration management for Registro,
including pattern strings, compiled patterns, and reserved words.
"""

import os
import re
import json
from typing import Dict, Optional, Pattern, Set
from pydantic import BaseModel, Field
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
    
    # Pattern strings with defaults
    _pattern_rid_prefix: str = r"^[a-z][a-z0-9-]{0,9}$"
    _pattern_service: str = r"^[a-z][a-z-]{0,49}$"
    _pattern_instance: str = r"^[a-z0-9][a-z0-9-]{0,49}$"
    _pattern_type: str = r"^[a-z][a-z-]{0,49}$"
    _pattern_locator: str = r"^[0-9A-HJ-KM-NPQRSTVWXYZ]{26}$"
    _pattern_api_name_object_type: str = r"^(?=.{1,100}$)[A-Z][A-Za-z0-9]*$"
    _pattern_api_name_link_type: str = r"^(?=.{1,100}$)[a-z][A-Za-z0-9]*$"
    _pattern_api_name_action_type: str = r"^(?=.{1,100}$)[A-Za-z][A-Za-z0-9_-]*$"
    _pattern_api_name_query_type: str = r"^(?=.{1,100}$)[a-z][A-Za-z0-9]*$"
    
    def __init__(self, **data):
        super().__init__(**data)
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

    def _initialize(self) -> None:
        """Initialize settings from environment variables."""
        # Load RID components
        self.RID_PREFIX = os.getenv("REGISTRO_RID_PREFIX", self.RID_PREFIX)
        self.DEFAULT_SERVICE = os.getenv("REGISTRO_DEFAULT_SERVICE", self.DEFAULT_SERVICE)
        self.DEFAULT_INSTANCE = os.getenv("REGISTRO_DEFAULT_INSTANCE", self.DEFAULT_INSTANCE)
        
        # Load pattern strings
        for pattern_name in [name[8:] for name in vars(self) if name.startswith("_pattern_")]:
            env_var = f"REGISTRO_PATTERN_{pattern_name.upper()}"
            if env_value := os.getenv(env_var):
                setattr(self, f"_pattern_{pattern_name}", env_value)
        
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
        attr_name = f"_pattern_{name.lower()}"
        return getattr(self, attr_name, None)

    def get_compiled_pattern(self, name: str) -> Optional[Pattern[str]]:
        """Get or compile the regex pattern for a given name."""
        if name in self._compiled_patterns_cache:
            return self._compiled_patterns_cache[name]
            
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
            try:
                # Validate pattern can be compiled
                re.compile(pattern_string)
                setattr(self, attr_name, pattern_string)
                self._compiled_patterns_cache.pop(name.upper(), None)
            except re.error as e:
                raise ValueError(f"Invalid pattern string for {name}: {e}")
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

# Create global settings instance
settings = Settings()
