# System Update Checklist

Streamlined checklist for updating the spec-driven development system.

## Pre-Update Assessment
- [ ] **Document rationale** for system changes
- [ ] **Assess impact** on existing specifications
- [ ] **Verify AI agent compatibility** across different platforms
- [ ] **Run health check** on current system state

## Update Process
- [ ] **Update core files**: principles.md, patterns.md, agent prompt
- [ ] **Update templates** with new patterns and metadata
- [ ] **Update examples** to reflect current standards
- [ ] **Test automation scripts** for compatibility
- [ ] **Update version numbers** and timestamps

## Validation
- [ ] **Run system health check**: `spec.sh health --json`
- [ ] **Validate examples** against new patterns
- [ ] **Test with AI agents** to ensure compatibility
- [ ] **Check cross-references** for integrity
- [ ] **Verify JSON output** from all scripts

## Quality Gates
- [ ] **Health score >95** after updates
- [ ] **Zero critical issues** in validation
- [ ] **All examples pass** pattern compliance
- [ ] **Scripts execute successfully** with JSON output
- [ ] **AI agents can parse** all structured data

## Rollback Preparation
- [ ] **Backup current system** before changes
- [ ] **Document rollback process** if needed
- [ ] **Test rollback procedure** in safe environment
- [ ] **Maintain version history** for reference

## Related Documents
- **Core Governance**: [principles.md](principles.md) - System rules and principles
- **Methodology Context**: [methodology.md](methodology.md) - Philosophical foundation
- **Document Patterns**: [../interaction/patterns.md](../interaction/patterns.md) - Structure guidance