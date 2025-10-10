
# Tasks Phase Reference

Quick reference for task generation.

## Task Format
```markdown
- [ ] **T-001**: Task description
  - Requirements: US-001, US-002
  - Implementation: [Specific steps]
  - Verification: [How to verify completion]
  - Status: pending
```

## Task Requirements
- **Checkbox format** with unique IDs (T-001, T-002)
- **Requirement references** for traceability
- **Verification criteria** for each task
- **Incremental approach** building on previous tasks

## Approval Process
1. Generate task breakdown from design
2. Ask: "**Does this task list provide a clear and logical plan for implementation? Are the tasks well-defined and actionable?**"
3. Wait for explicit approval
4. Update YAML status to `approved`
5. Run health check before implementation

## Critical Rules
- **MUST NOT** begin implementation during this phase
- **MUST** reference specific requirements
- **MUST** include verification criteria
- **MUST** build incrementally

*See main agent prompt for complete instructions.*
