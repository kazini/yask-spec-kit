
# Implementation Phase Reference

Quick reference for task execution.

## Execution Workflow
1. **Task Selection**: User selects specific task
2. **Status Update**: Mark task `[🚧]` in tasks.md
3. **Implementation**: Write code for selected task
4. **Verification**: Test against verification criteria
5. **Completion**: Mark task `[x]` and update progress
6. **Health Check**: Validate changes

## Status Indicators
- `[ ]` - Pending task
- `[🚧]` - In-progress task
- `[x]` - Completed task

## Critical Rules
- **MUST** work on user-selected task only
- **MUST** update task status before/after work
- **MUST** verify completion against criteria
- **MUST NOT** proceed to next task automatically
- **MUST** stop after each task for user review

## Progress Updates
Update YAML frontmatter:
```yaml
progress:
  completed_tasks: 3
  in_progress_tasks: 1
  completion_percentage: 60
```

*See main agent prompt for complete instructions.*
