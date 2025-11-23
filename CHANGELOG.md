## [0.5.0] - 2025-11-23
### Added
- **Global Type Registry System**: Catálogo global de tipos para resolução dinâmica de 'nome_do_recurso' -> 'ClassePython'
- **Auto-Registration**: Classes que herdam de ResourceTypeBaseModel são automaticamente registradas via __init_subclass__
- **Kernel Integration**: Suporte para que o Kernel (`malha`) possa instanciar objetos dinamicamente apenas pelos RIDs
- **Enhanced Identity API**: API limpa com funções parse_rid() e get_resource_type_from_rid()

### Features
- `registro/core/global_registry.py` - Implementação do Singleton Registry com thread-safety
- `registro/core/identity.py` - API simplificada para RID parsing e geração
- Auto-registro automático em `registro/core/resource_base.py` via `__init_subclass__`
- Funções facade para facilitar o uso do registry (register, get, create_instance)
- Compatibilidade completa com o sistema existente

### Breaking Changes
- Novas exportações no __init__.py principal (RID, new_rid, parse_rid, registry, etc.)

### Technical Details
- Implementação de Singleton pattern com thread-safety usando Lock
- Validação de conflitos de registro com opções de override
- API para extração de tipo de recurso diretamente do RID
- Suporte para criação dinâmica de instâncias via registry

## [0.4.0] - 2025-11-23
### Added
- Centralized identity management with RID type and new_rid() function
- Simplified ResourceTypeBaseModel for easier resource creation
- Global registry system for dynamic resource type management
- Domains package with example User model
- Automatic ULID-based resource identifier generation
- Built-in timestamp management with touch() method

### Features
- `registro/core/identity.py` - Centralized RID generation using ULID
- `registro/core/simple_resource_base.py` - Unified base model for resource types
- `registro/core/registry.py` - Global registry for resource type management
- `registro/domains/` - Package for domain-specific models
- Example usage in `examples/identity_registry_example.py`

### Breaking Changes
- New module exports added to core package

## [0.3.1] - 2025-11-22
### Fixed
- Fixed Resource.__setattr__ to properly handle initialization state
- Fixed RID generation logic with proper custom RID handling
- Fixed pattern name mapping in settings.py for schema generation

## [0.3.0] - 2025-11-20
### Added
- Smart RID with Pydantic v2 validation and component properties.
- Pure Pydantic schemas (ResourceSchema).
- Bitemporality: TimeAwareSchema and TimeAwareMixin with indexed fields.
- Resource.meta_tags (JSON) for governance and global indexing.

### Compatibility
- Public API preserved (ResourceTypeBaseModel).
- RID remains a string-compatible type; generate() unchanged.

### Notes
- DB migration required to add meta_tags to resource table.

