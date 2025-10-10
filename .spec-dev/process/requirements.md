
# Requirements Phase Reference

Quick reference for requirements generation.

## Output Format
- **YAML frontmatter** with health tracking
- **User stories** with unique IDs (US-001, US-002)
- **EARS acceptance criteria** with unique IDs (AC-001, AC-002)
- **JSON blocks** for AI consumption

## EARS Format
```
WHEN [event] THEN [system] SHALL [response]
IF [precondition] THEN [system] SHALL [response]
```

## Approval Process
1. Generate requirements with structured format
2. Ask: "**Does this requirements document accurately capture the feature? Are there any missing requirements or clarifications needed?**"
3. Wait for explicit approval
4. Update YAML status to `approved`
5. Run health check before proceeding

## Critical Rules
- **MUST NOT** proceed without explicit approval
- **MUST** use EARS format for all acceptance criteria
- **MUST** include unique IDs for traceability
- **MUST** run health check before design phase

*See main agent prompt for complete instructions.*
