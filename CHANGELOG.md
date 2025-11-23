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
