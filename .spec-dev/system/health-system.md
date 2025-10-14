# Health System (Optional)

## Overview
Optional diagnostic tool for specification quality validation. Use sparingly when quality issues are suspected.

## Diagnostic Approach
Similar to code diagnostics but for specifications:
- **Focus**: Document completeness and basic structure
- **When**: Only when quality issues are suspected or troubleshooting needed
- **Scope**: Requirements, design, tasks documents

## Basic Validation Using Script
```bash
# Check document quality (only when needed)
./.spec-dev/system/spec.sh validate feature-name
```

## Health Criteria (Streamlined)
- **Requirements**: EARS format compliance, user stories present
- **Design**: Addresses all requirements, clear architecture
- **Tasks**: Hierarchical structure, requirement traceability

## Usage Guidelines
- **Diagnostic Tool**: Use like code diagnostics - when problems suspected
- **Human-Driven**: User decides when validation is needed
- **No Blocking**: Validation informs, doesn't prevent progress
- **Focus on Essentials**: File existence, format compliance, basic structure

## Integration with Current Workflow
- **No Automatic Checks**: Run only when troubleshooting
- **Proactive Approach**: AI agents focus on quality during creation, not validation after
- **Human Judgment**: User approval more valuable than automated scoring
- **Simple Validation**: Basic checks for format and completeness

## When to Use
- **Document Quality Issues**: When specifications seem incomplete or inconsistent
- **Troubleshooting**: When workflow isn't proceeding smoothly
- **Format Validation**: When EARS format or structure compliance is questionable
- **Cross-Reference Check**: When traceability between documents is unclear

This system supports the streamlined workflow by providing diagnostic capabilities when needed, without adding overhead to normal operations.