# System Maintenance Checklist

Checklist for system administrators updating the spec-driven development system.

**Purpose**: This checklist is for maintaining and updating the system itself, not for daily workflow execution. For workflow guidance, see `process.md`.

## Pre-Update Assessment
- [ ] **Document rationale** for system changes
- [ ] **Assess impact** on existing specifications
- [ ] **Verify AI agent compatibility** across different platforms
- [ ] **Test current system** with sample specifications

## Update Process
- [ ] **Update core files**: overview.md, patterns.md, process.md, spec-dev-agent.md
- [ ] **Update templates** with new patterns and structures
- [ ] **Update examples** to reflect current standards
- [ ] **Test automation script** (system/spec.sh) for compatibility
- [ ] **Update cross-references** between documents

## Validation
- [ ] **Test script functionality**: `./.spec-dev/system/spec.sh --help`
- [ ] **Validate examples** against new patterns
- [ ] **Test with AI agents** to ensure compatibility
- [ ] **Check cross-references** for integrity
- [ ] **Verify template consistency** with patterns

## Quality Gates
- [ ] **All core files updated** and consistent
- [ ] **Zero broken references** in validation
- [ ] **All examples follow** current patterns
- [ ] **Script executes successfully** with all commands
- [ ] **AI agents can understand** all guidance documents

## Rollback Preparation
- [ ] **Backup current system** before changes
- [ ] **Document rollback process** if needed
- [ ] **Test rollback procedure** in safe environment
- [ ] **Maintain version history** for reference

## Post-Update Verification
- [ ] **Create test specification** using new system
- [ ] **Verify workflow** through all phases (Requirements → Design → Tasks → Implementation)
- [ ] **Test AI agent interaction** with updated guidance
- [ ] **Validate template usage** and document creation
- [ ] **Confirm cross-platform compatibility**

## Related Documents
- **System Overview**: [../overview.md](../overview.md) - Complete system guide with principles and philosophy
- **Document Patterns**: [../patterns.md](../patterns.md) - Structure and template guidance
- **Process Guide**: [../process.md](../process.md) - Workflow and communication guidance