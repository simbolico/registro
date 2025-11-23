"""
Global registry for resource types in Registro.

This module provides a centralized registry for managing resource types
and their corresponding model classes, allowing for dynamic resource
lookup and instantiation.
"""

from typing import Dict, Type, Optional, Any, List
import logging

from .simple_resource_base import ResourceTypeBaseModel

logger = logging.getLogger(__name__)

class Registry:
    """
    Global registry for resource types.
    
    This registry maintains a mapping between type names and their
    corresponding model classes, enabling dynamic resource lookup
    and instantiation.
    """
    
    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._types: Dict[str, Type[ResourceTypeBaseModel]] = {}
        self._initialized: bool = False
        
    def register(self, name: str, cls: Type[ResourceTypeBaseModel]) -> None:
        """
        Register a resource type with the given name.
        
        Args:
            name (str): The name to register the type under
            cls (Type[ResourceTypeBaseModel]): The model class to register
            
        Raises:
            ValueError: If name is empty or cls is not a ResourceTypeBaseModel subclass
            TypeError: If cls is not a class
        """
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
            
        if not isinstance(cls, type):
            raise TypeError(f"cls must be a class, got {type(cls)}")
            
        if not issubclass(cls, ResourceTypeBaseModel):
            raise ValueError(f"cls must be a subclass of ResourceTypeBaseModel, got {cls}")
            
        if name in self._types:
            logger.warning(f"Overriding existing registration for '{name}'")
            
        self._types[name] = cls
        logger.debug(f"Registered resource type '{name}' -> {cls.__name__}")
        
    def get(self, name: str) -> Type[ResourceTypeBaseModel]:
        """
        Get a resource type by name.
        
        Args:
            name (str): The name of the resource type
            
        Returns:
            Type[ResourceTypeBaseModel]: The registered model class
            
        Raises:
            KeyError: If the name is not registered
        """
        if name not in self._types:
            available_types = list(self._types.keys())
            raise KeyError(f"Resource type '{name}' not registered. Available types: {available_types}")
            
        return self._types[name]
        
    def unregister(self, name: str) -> Type[ResourceTypeBaseModel]:
        """
        Unregister a resource type.
        
        Args:
            name (str): The name of the resource type to unregister
            
        Returns:
            Type[ResourceTypeBaseModel]: The previously registered class
            
        Raises:
            KeyError: If the name is not registered
        """
        if name not in self._types:
            available_types = list(self._types.keys())
            raise KeyError(f"Resource type '{name}' not registered. Available types: {available_types}")
            
        cls = self._types.pop(name)
        logger.debug(f"Unregistered resource type '{name}'")
        return cls
        
    def list_types(self) -> List[str]:
        """
        Get a list of all registered type names.
        
        Returns:
            List[str]: List of registered type names
        """
        return list(self._types.keys())
        
    def get_all(self) -> Dict[str, Type[ResourceTypeBaseModel]]:
        """
        Get a copy of all registered types.
        
        Returns:
            Dict[str, Type[ResourceTypeBaseModel]]: Copy of the type registry
        """
        return self._types.copy()
        
    def clear(self) -> None:
        """Clear all registered types."""
        self._types.clear()
        logger.debug("Cleared all registered resource types")
        
    def is_registered(self, name: str) -> bool:
        """
        Check if a resource type is registered.
        
        Args:
            name (str): The name to check
            
        Returns:
            bool: True if the name is registered, False otherwise
        """
        return name in self._types
        
    def create_instance(self, type_name: str, **kwargs: Any) -> ResourceTypeBaseModel:
        """
        Create an instance of a registered resource type.
        
        Args:
            type_name (str): The name of the resource type
            **kwargs: Arguments to pass to the resource type constructor
            
        Returns:
            ResourceTypeBaseModel: An instance of the resource type
            
        Raises:
            KeyError: If the type_name is not registered
            Exception: If instantiation fails
        """
        cls = self.get(type_name)
        try:
            return cls(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create instance of '{type_name}': {e}")
            raise
            
    def mark_initialized(self) -> None:
        """Mark the registry as initialized."""
        self._initialized = True
        logger.debug("Registry marked as initialized")
        
    @property
    def is_initialized(self) -> bool:
        """
        Check if the registry is initialized.
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized

# Global registry instance
registry = Registry()
