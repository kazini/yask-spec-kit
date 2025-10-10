# Spec-Driven Development Prompting Guide

Effective prompting strategies for AI agents in spec-driven development.

## Spec-Specific Prompting Patterns

### Phase Initiation
```
"Create a requirements document for [feature description] following the spec-driven development process."
```

### Approval Requests
```
"Does this requirements document accurately capture the feature? Are there any missing requirements or clarifications needed?"
```

### Task Execution
```
"Execute task T-001 from the tasks.md file: [task description]"
```

### Health Monitoring
```
"Run a health check on the current specification and report any issues."
```

## AI Agent Communication Patterns

```json
{
  "patterns": [
    {
      "phase": "Requirements",
      "prompt": "Generate requirements with YAML frontmatter, user stories (US-001), and EARS acceptance criteria (AC-001)",
      "approval": "Wait for explicit approval before proceeding to design"
    },
    {
      "phase": "Design", 
      "prompt": "Create technical design addressing all requirements with structured decisions (DD-001)",
      "approval": "Wait for explicit approval before proceeding to tasks"
    },
    {
      "phase": "Tasks",
      "prompt": "Break design into discrete tasks (T-001) with requirement references and verification criteria",
      "approval": "Wait for explicit approval before beginning implementation"
    },
    {
      "phase": "Implementation",
      "prompt": "Execute user-selected task, update status, verify completion, stop for review",
      "approval": "Get task selection from user, complete one task at a time"
    }
  ]
}
```

## Effective Prompting Guidelines

1. **Be Phase-Specific**: Reference the current phase and expected outputs
2. **Use Structured Language**: Request YAML frontmatter, unique IDs, and JSON blocks
3. **Request Health Checks**: Ask for validation at phase transitions
4. **Specify Approval Process**: Use exact approval questions from the system
5. **Reference Standards**: Mention EARS format, traceability, and verification criteria

## Common Prompting Mistakes

❌ **Avoid**: "Create a design document"
✅ **Use**: "Create a design.md document with YAML frontmatter, addressing all requirements from requirements.md, including structured design decisions with DD-001 IDs"

❌ **Avoid**: "Make a task list"  
✅ **Use**: "Generate tasks.md with checkbox format, unique task IDs (T-001), requirement references, and verification criteria for each task"

❌ **Avoid**: "Implement the feature"
✅ **Use**: "Execute task T-003 from tasks.md, update status to in-progress, implement the specified functionality, verify completion, and mark as complete"

## Related Documents
- **Core Principles**: [../system/principles.md](../system/principles.md) - System governance and rules
- **Methodology**: [../system/methodology.md](../system/methodology.md) - Philosophical context and approach
- **Document Patterns**: [patterns.md](patterns.md) - Structure and formatting guidance
- **Quick Commands**: [../reference.md](../reference.md) - Script usage and patterns