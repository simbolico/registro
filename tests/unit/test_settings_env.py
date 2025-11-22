"""Test environment validation and configuration methods."""

import os
import pytest
from registro.config.settings import Settings


def test_validate_environment_default_allowed():
    """Test environment validation with default allowed environments."""
    # Test with default settings (no ENVIRONMENT set)
    settings = Settings()
    assert settings.validate_environment() is True
    
    # Test with allowed environment
    settings.ENVIRONMENT = "prod"
    assert settings.validate_environment() is True
    
    settings.ENVIRONMENT = "dev"
    assert settings.validate_environment() is True
    
    settings.ENVIRONMENT = "staging"
    assert settings.validate_environment() is True


def test_validate_environment_custom_allowed():
    """Test environment validation with custom allowed environments."""
    settings = Settings()
    
    # Test with custom allowed environments
    allowed = {"test", "qa", "prod"}
    
    settings.ENVIRONMENT = "test"
    assert settings.validate_environment(allowed) is True
    
    settings.ENVIRONMENT = "qa"
    assert settings.validate_environment(allowed) is True
    
    settings.ENVIRONMENT = "prod"
    assert settings.validate_environment(allowed) is True
    
    settings.ENVIRONMENT = "dev"
    assert settings.validate_environment(allowed) is False


def test_validate_environment_debug_warning():
    """Test environment validation with debug warning."""
    settings = Settings()
    settings.DEBUG = True
    settings.ENVIRONMENT = "invalid"
    
    # Should issue warning but still return False for invalid environment
    with pytest.warns(UserWarning, match="Environment 'invalid' is not in allowed set"):
        result = settings.validate_environment({"test", "prod"})
        assert result is False


def test_get_effective_instance():
    """Test getting effective instance name based on environment."""
    settings = Settings()
    
    # Test with no ENVIRONMENT set
    assert settings.get_effective_instance() == "prod"
    
    # Test with various environment mappings
    test_cases = [
        ("dev", "dev"),
        ("development", "dev"),
        ("staging", "staging"),
        ("stage", "staging"),
        ("prod", "prod"),
        ("production", "prod"),
        ("unknown", "prod"),  # Falls back to default
    ]
    
    for env, expected_instance in test_cases:
        settings.ENVIRONMENT = env
        assert settings.get_effective_instance() == expected_instance


def test_get_effective_instance_with_default():
    """Test getting effective instance with custom default."""
    settings = Settings()
    settings.DEFAULT_INSTANCE = "custom"
    
    # Test with no ENVIRONMENT set
    assert settings.get_effective_instance() == "custom"
    
    # Test with unknown environment
    settings.ENVIRONMENT = "unknown"
    assert settings.get_effective_instance() == "custom"


def test_environment_from_env_var():
    """Test environment settings from environment variables."""
    # Set environment variable
    os.environ["REGISTRO_ENVIRONMENT"] = "test"
    os.environ["REGISTRO_DEBUG"] = "true"
    
    try:
        settings = Settings()
        assert settings.ENVIRONMENT == "test"
        assert settings.DEBUG is True
        
        # Test effective instance mapping
        assert settings.get_effective_instance() == "prod"  # test maps to default
        
    finally:
        # Clean up environment variables
        os.environ.pop("REGISTRO_ENVIRONMENT", None)
        os.environ.pop("REGISTRO_DEBUG", None)


def test_debug_from_env_var():
    """Test DEBUG setting from environment variables."""
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("", False),  # Default when not set
    ]
    
    for env_value, expected in test_cases:
        os.environ["REGISTRO_DEBUG"] = env_value
        
        try:
            settings = Settings()
            assert settings.DEBUG is expected
        finally:
            os.environ.pop("REGISTRO_DEBUG", None)
