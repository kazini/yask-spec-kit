# Quick Reference

## Commands
```bash
# Project setup
./scripts/spec.sh init
./scripts/spec.sh new "feature-name"

# Management
./scripts/spec.sh list --json
./scripts/spec.sh validate --json
./scripts/spec.sh health

# Sub-specifications
./scripts/manage-subspecs.sh create feature-name component-name
```

## Document Structure
```
.specification/specs/feature-name/
├── requirements.md  # YAML + EARS + JSON
├── design.md       # YAML + Architecture + JSON decisions
└── tasks.md        # YAML + Tasks + requirement refs
```

## EARS Format
```markdown
**User Story (US-001):** As a [role], I want [capability], so that [benefit]

#### Acceptance Criteria
- **AC-001**: WHEN [event] THEN [system] SHALL [response]
- **AC-002**: IF [precondition] THEN [system] SHALL [behavior]
```

## Templates

### Requirements
```yaml
---
id: req-feature-name
title: Feature Requirements
status: draft
version: 1.0.0
---
```

### Design
```yaml
---
id: des-feature-name
title: Feature Design
status: draft
related_docs: [req-feature-name]
---
```

### Tasks
```yaml
---
id: tasks-feature-name
title: Implementation Tasks
status: draft
related_docs: [req-feature-name, des-feature-name]
---
```

## JSON Patterns

### Acceptance Criteria
```json
[{"id": "AC-001", "user_story": "US-001", "type": "WHEN", "event": "...", "response": "..."}]
```

### Design Decisions
```json
[{"id": "DD-001", "decision": "...", "rationale": "...", "impact": "..."}]
```

### Specification Status
```json
{"name": "feature", "phase": "requirements", "status": "draft", "files": {"requirements": true}}
```

## Quality Checklist
- [ ] YAML frontmatter present
- [ ] Unique IDs used (US-001, AC-001)
- [ ] EARS format followed
- [ ] JSON blocks included
- [ ] Requirements traced to design/tasks

## Troubleshooting
```bash
# Validate and fix issues
./scripts/spec.sh validate --json
./scripts/project-health.sh --fix
```

## Related Documents
- **System Governance**: [system/principles.md](system/principles.md) - Core rules and principles
- **Document Patterns**: [interaction/patterns.md](interaction/patterns.md) - Structure guidance
- **AI Collaboration**: [interaction/prompting.md](interaction/prompting.md) - Effective prompting
- **System Philosophy**: [system/methodology.md](system/methodology.md) - Comprehensive approach