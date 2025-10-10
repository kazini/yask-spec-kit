# Specification Patterns

Streamlined document patterns for AI agents.

## Core Focus
1. **AI Context Efficiency**: Structured, scannable content
2. **Machine-Readable**: YAML frontmatter + JSON blocks
3. **Systematic IDs**: US-001, AC-001, DD-001 for traceability
4. **Focused Content**: Essential information only

## Document Metadata Pattern

Include structured metadata in all specifications:

```yaml
---
id: req-feature-name
title: Feature Name Requirements  
status: draft|approved|implemented
version: 1.0.0
author: [Author/Team]
date: [YYYY-MM-DD]
dependencies: []
---
```

## Requirements Pattern

```yaml
---
id: req-feature-name
title: Feature Requirements
status: draft
version: 1.0.0
dependencies: []
---
```

```markdown
# Feature Requirements

## Introduction
[Concise feature description and technical approach]

## Requirements

### Requirement 1: [Title]
**User Story (US-001):** As [role], I want [capability], so that [benefit]

#### Acceptance Criteria
1. **AC-001**: WHEN [event] THEN [system] SHALL [response]
2. **AC-002**: IF [condition] THEN [system] SHALL [behavior]

## Structured Data
```json
[{"id": "AC-001", "user_story": "US-001", "type": "WHEN", "event": "...", "response": "..."}]
```
```

## Design Pattern

```yaml
---
id: des-feature-name
title: Feature Design
status: draft
version: 1.0.0
related_docs: [req-feature-name]
---
```

```markdown
# Feature Design

## Overview
[System architecture and core innovation]

## Architecture
[Technical design with specific components]

## Components
[Key components and interfaces]

## Data Models
[Data structures and relationships]

## Design Decisions
```json
[{"id": "DD-001", "decision": "...", "rationale": "...", "impact": "..."}]
```
```

## Tasks Pattern

```yaml
---
id: tasks-feature-name
title: Feature Implementation Tasks
status: draft|approved|in-progress|completed
version: 1.0.0
related_docs: [req-feature-name, des-feature-name]
progress:
  total_tasks: 0
  completed_tasks: 0
  in_progress_tasks: 0
---
```

```markdown
# Implementation Tasks

## Development Status
- ✅ **Completed**: 0 tasks
- 🚧 **In Progress**: 0 tasks  
- ⏳ **Pending**: 0 tasks
- 📊 **Progress**: 0% complete

## Tasks

### Foundation
- [ ] **T-001**: [Task description]
  - Requirements: US-001, US-002
  - Verification: [How to verify completion]
  - Status: pending

- [🚧] **T-002**: [In-progress task]
  - Requirements: US-003
  - Verification: [Completion criteria]
  - Status: in-progress

- [x] **T-003**: [Completed task]
  - Requirements: US-001
  - Verification: [Completion criteria]
  - Status: completed

### Core Implementation  
- [ ] **T-004**: [Next task]
  - Requirements: US-003
  - Verification: [Completion criteria]
  - Status: pending
```

## Status Update Patterns

### Task Status Indicators
- `[ ]` - Pending task
- `[🚧]` - In-progress task  
- `[x]` - Completed task

### YAML Progress Tracking
```yaml
progress:
  total_tasks: 8
  completed_tasks: 3
  in_progress_tasks: 1
  completion_percentage: 37.5
```

## Reference Patterns

### Cross-References
```markdown
*See [Detail](path/to/detail.md) for more information.*
Requirements: US-001, US-002
Related: req-feature-name, des-feature-name
```

### JSON Data Blocks

**Acceptance Criteria:**
```json
[{"id": "AC-001", "user_story": "US-001", "type": "WHEN", "event": "...", "response": "..."}]
```

**Design Decisions:**
```json
[{"id": "DD-001", "decision": "...", "rationale": "...", "impact": "..."}]
```

**Specification Status:**
```json
{"name": "feature", "phase": "requirements", "status": "draft", "files": {"requirements": true}}
```

## Quality Standards

### Requirements
- EARS format: `WHEN [event] THEN [system] SHALL [response]`
- Unique IDs: US-001, AC-001
- JSON blocks for AI consumption
- Technical precision

### Design  
- Address all requirements
- Structured decisions with JSON
- Clear architecture
- Component specifications

### Tasks
- Discrete, actionable steps
- Requirement references
- Verification criteria
- Incremental approach

## Health Monitoring Patterns

### Project Health Assessment
```bash
# AI agents should run health checks at key points:
./scripts/spec.sh health --json
```

### Health Check Integration Points
1. **Before Phase Transitions**: Validate current phase before proceeding
2. **After Major Updates**: Check integrity after significant changes
3. **Pre-Implementation**: Comprehensive validation before coding begins
4. **Regular Intervals**: Periodic health assessments during development

### Health Metrics Tracking
```yaml
# Include in specification YAML frontmatter:
health:
  last_check: 2024-12-XX
  score: 95
  issues: 0
  warnings: 2
  compliance: "EARS format: ✓, Cross-refs: ✓, Structure: ✓"
```

### Quality Indicators
- **Health Score**: 0-100 based on issues and warnings
- **Compliance Status**: EARS format, cross-references, structure
- **Progress Metrics**: Completion percentages and phase status
- **Issue Tracking**: Critical issues vs warnings

## Supplementary Documents

### Map Document Pattern
**When to create**: For any project with >3 specification documents
**Purpose**: Project structure overview, status tracking, maintenance guidelines

```markdown
# [Project Name]: Project Structure Map

## Project Organization
[Directory structure with explanations]

## Project Status
**Phase**: [current phase]
**Health Score**: [health check results]
**Progress**: [task completion percentage]

## Document Purposes
[Each document's role and update triggers]

## Maintenance Guidelines
[Update procedures and review process]
```

### Architecture Directory Pattern
**When to create**: When design.md >10 pages or >5 major components
**Purpose**: Detailed architectural specifications organized by system area

```
architecture/
├── README.md           # Architecture navigation
├── core-systems/       # Core component specs
├── interfaces/         # API and data models
└── integration/        # System integration patterns
```

### Data Model Pattern
**When to create**: When data structures need detailed specification
**Purpose**: Comprehensive data schemas, relationships, and API formats

```markdown
# [Feature Name] Data Model

## Core Data Structures
[TypeScript interfaces and enums]

## Database Schema
[SQL table definitions and indexes]

## API Data Formats
[Request/response formats and validation]

## Relationships
[Entity relationships and constraints]
```

## AI Guidelines
1. **Structured Metadata**: Use separated metadata with script management
2. **Unique IDs**: US-001, AC-001, DD-001, T-001 for systematic traceability
3. **JSON Blocks**: Machine-readable data for AI consumption
4. **Health Monitoring**: Run health checks at phase transitions
5. **Status Management**: Update task status using scripts
6. **Approval Workflow**: Use structured approval questions and wait for explicit confirmation
7. **Single Task Focus**: Execute one task at a time with status updates
8. **Quality Assurance**: Address health issues before proceeding
9. **Supplementary Docs**: Create map.md, architecture/, data-model.md when needed
10. **Clear Traceability**: Link requirements → design → tasks → implementation

## Related Documents
- **Core Principles**: [../system/principles.md](../system/principles.md) - System governance and rules
- **AI Collaboration**: [prompting.md](prompting.md) - Effective AI interaction patterns
- **Quick Reference**: [../reference.md](../reference.md) - Commands and patterns
- **System Philosophy**: [../system/methodology.md](../system/methodology.md) - Comprehensive approach