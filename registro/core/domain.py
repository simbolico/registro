import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from registro.core.resource import Resource as PhysicalResource
from registro.models.rid import RID

T = TypeVar("T", bound="DomainResource")

class DomainResource(BaseModel):
    """
    Recurso de Domínio Lógico.
    
    Esta classe representa a visão da aplicação sobre o dado.
    Ela é agnóstica ao banco de dados (não herda de SQLModel),
    mas possui métodos para converter-se em um registro físico (Envelope).
    
    Capabilities:
    - Schema Evolution: Campos não mapeados no SQL vão para um JSON Bag.
    - Type Safety: Validação Pydantic completa.
    - Identity: Gestão automática de RID.
    """
    
    # Configuração Pydantic V2 SotA
    model_config = ConfigDict(
        extra='allow',                # Permite campos dinâmicos (Schema-on-Read)
        arbitrary_types_allowed=True, # Permite tipos complexos (Grafos, etc)
        validate_assignment=True,
        populate_by_name=True
    )

    # Campos Lógicos Base (Espelham colunas físicas chaves)
    rid: str = Field(default_factory=lambda: RID.generate(type_="resource"))
    version: int = Field(default=1, description="Otimistic Locking Version")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    
    # Cache interno do registro físico (Performance optimization)
    _physical_cache: Optional[PhysicalResource] = PrivateAttr(default=None)

    def to_envelope(self) -> PhysicalResource:
        """
        Converte este Objeto de Domínio para o Envelope Físico (Tabela SQL).
        
        Estratégia SotA:
        1. Identifica colunas que existem fisicamente na tabela 'Resource'.
        2. Tudo que NÃO é coluna física é serializado para 'meta_tags' (JSONB).
        """
        data = self.model_dump()
        
        # Lista hardcoded ou introspectada das colunas SQL reais
        # Em produção, isso poderia vir de PhysicalResource.__table__.columns.keys()
        sql_columns = {
            'id', 'rid', 'service', 'instance', 'resource_type',
            'created_at', 'updated_at', 'valid_from', 'valid_to',
            'tx_from', 'tx_to', 'version', 'archived_at', 'deleted_at', 'expired_at'
        }
        
        # Separação Payload vs Envelope
        envelope_data = {k: v for k, v in data.items() if k in sql_columns}
        payload_data = {k: v for k, v in data.items() if k not in sql_columns}
        
        # Garante integridade do ID (extrai do RID se necessário)
        if 'rid' in envelope_data and ('id' not in envelope_data or not envelope_data['id']):
            try:
                envelope_data['id'] = envelope_data['rid'].split('.')[-1]
            except IndexError:
                pass

        # Instancia a tabela física
        return PhysicalResource(
            **envelope_data,
            meta_tags=payload_data # O SQLModel serializa isso automaticamente para JSON
        )

    @classmethod
    def from_envelope(cls: Type[T], record: PhysicalResource) -> T:
        """
        Hidrata um Objeto de Domínio a partir de um registro físico SQL.
        Realiza o 'Flattening' do JSON Bag de volta para atributos de topo.
        """
        # 1. Extrai dados das colunas SQL
        data = record.model_dump()
        
        # 2. Recupera o Payload JSON (meta_tags)
        # O SQLModel/SQLAlchemy já deve ter deserializado o JSON para dict aqui
        meta_tags = data.pop('meta_tags', {}) or {}
        
        if isinstance(meta_tags, str):
            try:
                meta_tags = json.loads(meta_tags)
            except json.JSONDecodeError:
                meta_tags = {}

        # 3. Merge: Dados do JSON sobrescrevem colunas se houver conflito (ou vice-versa)
        # Geralmente preferimos que colunas SQL sejam a verdade estrutural
        full_data = {**meta_tags, **data}
        
        # 4. Instancia o Domínio
        instance = cls(**full_data)
        instance._physical_cache = record # Link reverso para otimização
        return instance
