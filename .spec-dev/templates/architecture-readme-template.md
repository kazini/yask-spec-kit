# [Feature Name] Architecture

## Architecture Overview

This directory contains detailed architectural specifications organized by system area.

## Directory Structure

```
architecture/
├── README.md              # This file - architecture navigation
├── core-systems/          # Core component specifications
├── interfaces/            # API and data model specifications
├── integration/           # System integration patterns
└── [additional-areas]/    # Feature-specific architecture areas
```

## Architecture Areas

### Core Systems
**Purpose**: Fundamental system components and their interactions
**Contents**: Core algorithms, system services, foundational components
**When to use**: For components that other systems depend on

### Interfaces
**Purpose**: API specifications, data models, and system boundaries
**Contents**: API definitions, data schemas, interface contracts
**When to use**: For external interfaces and data structure definitions

### Integration
**Purpose**: How different components work together
**Contents**: Integration patterns, communication protocols, coordination mechanisms
**When to use**: For complex inter-component relationships

## Navigation

### From Main Design
- **[Main Design Document](../design.md)** - High-level architecture overview
- **[Data Model](../data-model.md)** - Detailed data structures

### To Implementation
- **[Tasks Document](../tasks.md)** - Implementation task breakdown
- **[Requirements](../requirements.md)** - What this architecture addresses

## Architecture Decisions

Key architectural decisions are documented in the main design.md file with references to detailed specifications in this directory.

### Decision Pattern
```markdown
**Decision**: [What was decided]
**Rationale**: [Why this approach was chosen]
**Alternatives**: [Other options considered]
**Impact**: [Effect on system design]
**Details**: [Link to detailed specification in this directory]
```

## Maintenance

### When to Update
- New architectural components added
- System integration patterns change
- Interface specifications evolve
- Performance or security requirements change

### Update Process
1. Update relevant architecture documents
2. Update main design.md with references
3. Verify task breakdown still accurate
4. Run health check to validate changes