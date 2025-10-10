
# Design Phase Reference

Quick reference for design generation.

## Required Sections
- **Overview**: System architecture summary
- **Architecture**: Technical design and integration
- **Components**: Component specifications and interfaces
- **Data Models**: Data structures and relationships
- **Error Handling**: Error scenarios and recovery
- **Testing Strategy**: Validation approach

## Design Decisions
Include JSON blocks with structured decisions:
```json
[{"id": "DD-001", "decision": "...", "rationale": "...", "impact": "..."}]
```

## Approval Process
1. Generate design addressing all requirements
2. Ask: "**Does this design document provide a clear and complete technical plan? Are there any areas that need more detail or a different approach?**"
3. Wait for explicit approval
4. Update YAML status to `approved`
5. Run health check before tasks phase

## Critical Rules
- **MUST** address all requirements from requirements.md
- **MUST NOT** proceed without explicit approval
- **MUST** include structured design decisions
- **MUST** run health check before tasks phase

*See main agent prompt for complete instructions.*
