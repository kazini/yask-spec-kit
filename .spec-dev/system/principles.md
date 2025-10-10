# Principles

Core principles and rules for spec-driven development.

## Principles

1. **Clarity Before Code**: Understanding precedes implementation
2. **Iterative Refinement**: Each phase builds on validated foundations  
3. **Structured Documentation**: Machine-readable specs with metadata
4. **Manageable Complexity**: Break large features into focused sub-specs
5. **AI Context Efficiency**: Streamlined, scannable content for AI agents

## Rules

1. **Three-Phase Process**: Requirements → Design → Tasks → Implementation
2. **User Approval**: Explicit approval required between phases
3. **Structured Metadata**: YAML frontmatter + JSON blocks in all specs
4. **Unique IDs**: US-001, AC-001, DD-001, T-001 for traceability
5. **Sub-Specifications**: Break complex features into manageable parts
6. **EARS Format**: `WHEN [event] THEN [system] SHALL [response]`
7. **Automation Integration**: Use scripts for validation and management

## Structured Principles (AI Consumption)

```json
{
  "principles": [
    {"id": "P-001", "name": "Clarity Before Code", "description": "Understanding precedes implementation"},
    {"id": "P-002", "name": "Iterative Refinement", "description": "Each phase builds on validated foundations"},
    {"id": "P-003", "name": "Structured Documentation", "description": "Machine-readable specs with metadata"},
    {"id": "P-004", "name": "Manageable Complexity", "description": "Break large features into focused sub-specs"},
    {"id": "P-005", "name": "AI Context Efficiency", "description": "Streamlined, scannable content for AI agents"}
  ],
  "rules": [
    {"id": "R-001", "name": "Three-Phase Process", "description": "Requirements → Design → Tasks → Implementation"},
    {"id": "R-002", "name": "User Approval", "description": "Explicit approval required between phases"},
    {"id": "R-003", "name": "Structured Metadata", "description": "YAML frontmatter + JSON blocks in all specs"},
    {"id": "R-004", "name": "Unique IDs", "description": "US-001, AC-001, DD-001, T-001 for traceability"},
    {"id": "R-005", "name": "EARS Format", "description": "WHEN [event] THEN [system] SHALL [response]"}
  ]
}
```

## Related Documents
- **System Maintenance**: [principles_checklist.md](principles_checklist.md) - Update procedures and quality gates
- **Detailed Philosophy**: [methodology.md](methodology.md) - Comprehensive approach and philosophy
- **Document Patterns**: [../interaction/patterns.md](../interaction/patterns.md) - Structure and formatting guidance
- **AI Collaboration**: [../interaction/prompting.md](../interaction/prompting.md) - Effective AI interaction patterns