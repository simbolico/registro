"""
Identity module for Registro - API limpa para RID e geração de IDs.

Este módulo fornece uma interface simplificada para geração de IDs
e tipos de recursos, facilitando a importação e uso em toda a aplicação.
"""

from __future__ import annotations

from typing import NewType, Union
from registro.models.rid import RID as BaseRID, generate_ulid

# Type alias para Resource Identifier com compatibilidade backward
RID = NewType("RID", str)

def new_rid() -> str:
    """
    Helper para gerar apenas a parte ULID (locator).
    
    Returns:
        str: Novo ULID gerado para uso como locator
    """
    return generate_ulid()

def parse_rid(rid: str) -> dict:
    """
    Parse um RID em seus componentes.
    
    Args:
        rid (str): RID completo no formato prefix.service.instance.type.id
        
    Returns:
        dict: Dicionário com componentes do RID
        
    Raises:
        ValueError: Se o RID for inválido
    """
    try:
        # Converte para BaseRID se for string
        if isinstance(rid, str):
            rid_obj = BaseRID(rid)
        else:
            rid_obj = rid
            
        components = rid_obj.components()
        return {
            "prefix": components.get("prefix"),
            "service": components.get("service"),
            "instance": components.get("instance"),
            "resource_type": components.get("type"),  # A chave é "type", não "resource_type"
            "locator": components.get("locator"),
            "resource_id": components.get("locator")  # locator é o mesmo que resource_id
        }
    except Exception as e:
        raise ValueError(f"Invalid RID '{rid}': {e}")

def get_resource_type_from_rid(rid: Union[str, BaseRID]) -> str:
    """
    Extrai o tipo de recurso de um RID.
    
    Args:
        rid: RID (string ou objeto BaseRID)
        
    Returns:
        str: Tipo do recurso
        
    Raises:
        ValueError: Se o RID for inválido
    """
    try:
        if isinstance(rid, str):
            rid_obj = BaseRID(rid)
        else:
            rid_obj = rid
            
        # Usa o método components() para obter os componentes
        components = rid_obj.components()
        return components.get("type", "")
    except Exception as e:
        raise ValueError(f"Invalid RID '{rid}': {e}")

# Exporta símbolos para compatibilidade backward
__all__ = [
    "RID",
    "new_rid", 
    "parse_rid",
    "get_resource_type_from_rid"
]
