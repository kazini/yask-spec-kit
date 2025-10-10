
# Process Quick Reference

Streamlined workflow reference for AI agents.

## Workflow Overview
```
Requirements → Design → Tasks → Implementation
     ↓           ↓        ↓         ↓
  User Approval → User Approval → User Approval → Task Execution
```

## Phase Summary
```json
{
  "workflow": [
    {"phase": "Requirements", "output": "requirements.md", "approval": "explicit", "health_check": true},
    {"phase": "Design", "output": "design.md", "approval": "explicit", "health_check": true},
    {"phase": "Tasks", "output": "tasks.md", "approval": "explicit", "health_check": true},
    {"phase": "Implementation", "output": "code", "approval": "per_task", "health_check": "continuous"}
  ]
}
```

## Key Requirements
- **YAML frontmatter** in all documents
- **Unique IDs** for traceability (US-001, AC-001, DD-001, T-001)
- **Health monitoring** at phase transitions
- **Explicit approval** before proceeding
- **Single task focus** during implementation

*See main agent prompt for detailed instructions.*
