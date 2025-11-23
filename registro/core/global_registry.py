"""
Global Type Registry for Registro.

Este módulo implementa o catálogo global de tipos de recursos que permite
resolver 'nome_do_recurso' -> 'ClassePython' de forma automática.

O Registry é um Singleton que mantém referências a todas as classes
de recursos registradas no sistema.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Type, List, Any
from threading import Lock

logger = logging.getLogger(__name__)

class GlobalRegistry:
    """
    Catálogo global de tipos de recursos.
    
    Permite resolver 'nome_do_recurso' -> 'ClassePython' para que o Kernel
    possa instanciar objetos dinamicamente apenas pelos seus RIDs.
    
    Este é um Singleton que mantém estado global durante toda a execução
    da aplicação.
    """
    
    _instance: Optional[GlobalRegistry] = None
    _lock: Lock = Lock()
    
    def __new__(cls) -> GlobalRegistry:
        """Implementação do Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Inicializa o registro."""
        if not self._initialized:
            self._types: Dict[str, Type] = {}
            self._initialized = True
            logger.debug("GlobalRegistry initialized")
    
    def register(self, name: str, cls: Type, *, allow_override: bool = False) -> None:
        """
        Registra um modelo no catálogo global.
        
        Args:
            name (str): Nome do recurso (ex: "user", "product")
            cls (Type): Classe Python que implementa o recurso
            allow_override (bool): Se True, permite sobrescrever registros existentes
            
        Raises:
            ValueError: Se name já estiver registrado e allow_override=False
        """
        if not name or not isinstance(name, str):
            raise ValueError("Resource type name must be a non-empty string")
            
        if name in self._types and self._types[name] != cls:
            if allow_override:
                logger.warning(
                    f"Resource type '{name}' being overridden from {self._types[name]} to {cls}"
                )
            else:
                raise ValueError(
                    f"Resource type '{name}' already registered with {self._types[name]}. "
                    f"Use allow_override=True to replace it."
                )
        
        self._types[name] = cls
        logger.debug(f"Resource registered: {name} -> {cls.__name__} ({cls.__module__})")
    
    def get(self, name: str) -> Optional[Type]:
        """
        Retorna a classe associada ao nome do recurso.
        
        Args:
            name (str): Nome do recurso
            
        Returns:
            Optional[Type]: Classe Python associada ou None se não encontrado
        """
        return self._types.get(name)
    
    def get_or_error(self, name: str) -> Type:
        """
        Retorna a classe associada ao nome do recurso ou levanta erro.
        
        Args:
            name (str): Nome do recurso
            
        Returns:
            Type: Classe Python associada
            
        Raises:
            KeyError: Se o tipo de recurso não for encontrado
        """
        if name not in self._types:
            available_types = ", ".join(sorted(self._types.keys()))
            raise KeyError(
                f"Resource type '{name}' not found in registry. "
                f"Available types: {available_types}"
            )
        return self._types[name]
    
    def unregister(self, name: str) -> Optional[Type]:
        """
        Remove um tipo do registro.
        
        Args:
            name (str): Nome do recurso a ser removido
            
        Returns:
            Optional[Type]: Classe que foi removida ou None se não existia
        """
        cls = self._types.pop(name, None)
        if cls:
            logger.debug(f"Resource unregistered: {name} -> {cls.__name__}")
        return cls
    
    def list_types(self) -> List[str]:
        """
        Retorna lista de todos os tipos registrados.
        
        Returns:
            List[str]: Lista de nomes de recursos registrados
        """
        return list(self._types.keys())
    
    def is_registered(self, name: str) -> bool:
        """
        Verifica se um tipo está registrado.
        
        Args:
            name (str): Nome do recurso
            
        Returns:
            bool: True se estiver registrado, False caso contrário
        """
        return name in self._types
    
    def create_instance(self, type_name: str, **kwargs: Any) -> Any:
        """
        Cria uma instância de um tipo registrado.
        
        Args:
            type_name (str): Nome do tipo de recurso
            **kwargs: Argumentos para o construtor da classe
            
        Returns:
            Any: Instância da classe
            
        Raises:
            KeyError: Se o tipo não estiver registrado
            Exception: Se a instanciação falhar
        """
        cls = self.get_or_error(type_name)
        try:
            return cls(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create instance of '{type_name}': {e}")
            raise
    
    def clear(self) -> None:
        """Limpa todos os registros (útil para testes)."""
        self._types.clear()
        logger.debug("GlobalRegistry cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do registro.
        
        Returns:
            Dict[str, Any]: Estatísticas incluindo contagem e tipos registrados
        """
        return {
            "total_types": len(self._types),
            "types": sorted(self._types.keys()),
            "modules": sorted({cls.__module__ for cls in self._types.values()})
        }

# Instância global do Singleton (exportada como 'registry')
registry = GlobalRegistry()

# Facade functions for backward compatibility and easier access
def register(name: str, cls: Type, *, allow_override: bool = False) -> None:
    """Função facade para registry.register()."""
    registry.register(name, cls, allow_override=allow_override)

def get(name: str) -> Optional[Type]:
    """Função facade para registry.get()."""
    return registry.get(name)

def get_or_error(name: str) -> Type:
    """Função facade para registry.get_or_error()."""
    return registry.get_or_error(name)

def list_types() -> List[str]:
    """Função facade para registry.list_types()."""
    return registry.list_types()

def is_registered(name: str) -> bool:
    """Função facade para registry.is_registered()."""
    return registry.is_registered(name)

def create_instance(type_name: str, **kwargs: Any) -> Any:
    """Função facade para registry.create_instance()."""
    return registry.create_instance(type_name, **kwargs)
