# Spec-Driven Development Context

Streamlined AI agent context for structured software development.

## Purpose
AI agent system for structured development: Requirements → Design → Tasks → Implementation

## Core Files
- **`reference.md`** - Essential commands and patterns
- **`system/principles.md`** - Core rules with JSON blocks
- **`system/methodology.md`** - Philosophy and approach
- **`system/principles_checklist.md`** - System maintenance procedures

## Interaction Guidance
- **`interaction/patterns.md`** - Document structure patterns
- **`interaction/prompting.md`** - AI collaboration guide

## Document Structure
```
.specification/specs/feature-name/
├── requirements.md  # EARS format with YAML+JSON
├── design.md       # Technical design with decisions
└── tasks.md        # Implementation steps with IDs
```

## Process Flow
1. **Requirements**: EARS format + user approval
2. **Design**: Technical design + user approval  
3. **Tasks**: Coding tasks + user approval
4. **Implementation**: Execute tasks systematically

## Templates
- **`templates/requirements-template.md`** - YAML + EARS + JSON
- **`templates/design-template.md`** - YAML + Architecture + JSON decisions
- **`templates/tasks-template.md`** - YAML + Tasks + requirement refs

## Scripts
- **`scripts/spec.sh`** - Main management (init, new, list, validate)
- **`scripts/project-health.sh`** - Project validation
- **`scripts/manage-subspecs.sh`** - Sub-specification management

## Supporting Documentation
- **`process/`** - Phase-specific guidance
- **`examples/`** - Real-world specification examples

## Key Features
- **AI Context Efficient**: Streamlined for AI agent consumption
- **Structured Metadata**: YAML frontmatter + JSON blocks
- **Systematic IDs**: US-001, AC-001, DD-001, T-001
- **Machine Readable**: JSON output for automation
- **Quality Focused**: Essential information without bloat

## Quality Standards
- YAML frontmatter + JSON blocks
- Unique IDs: US-001, AC-001, DD-001, T-001
- EARS format: WHEN/IF...THEN...SHALL
- Streamlined, AI-friendly content

## Usage
1. AI agents load `../spec-dev-agent.md` as primary context
2. Reference `system/` for governance and methodology
3. Reference `interaction/` for document patterns and AI collaboration
4. Use `templates/` for consistent specification creation
5. Apply `scripts/` for automation and validation

---
*Optimized for AI context efficiency while maintaining quality and structure.*