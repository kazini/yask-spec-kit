# [Project Name]: Project Structure Map

## Project Organization

```
project-root/
├── .blueprint/[feature-name]/
│   ├── requirements.md          # WHAT we need to build
│   ├── design.md               # HOW we'll build it
│   ├── tasks.md                # Implementation steps
│   ├── map.md                  # Project structure and status
│   └── architecture/           # Detailed architectural specs
│       ├── core-systems/       # Core component specifications
│       ├── interfaces/         # API specifications
│       └── integration/        # System integration patterns
├── src/                        # Implementation code
├── tests/                      # Test suites
└── docs/                       # Generated documentation
```

## Document Purposes

### Core Specifications
- **requirements.md**: User stories and EARS acceptance criteria
- **design.md**: Technical architecture overview with references
- **tasks.md**: Actionable implementation tasks with verification
- **map.md**: Project structure, status, and maintenance guide

### Detailed Specifications
- **architecture/**: Detailed technical specifications by system area

## Navigation Guide

### By Development Phase
- **Planning**: [Requirements](requirements.md) → [Design](design.md) → [Tasks](tasks.md)
- **Implementation**: [Tasks](tasks.md) → Implementation Code
- **Validation**: [Testing Strategy](design.md#testing-strategy) → [Acceptance Criteria](requirements.md#acceptance-criteria)

### By Component
- **Core Systems**: [Component A](architecture/component-a.md) → [Component B](architecture/component-b.md)
- **Integration**: [System Integration](architecture/integration.md)

### Cross-Reference Patterns
- **Internal References**: *See [Detailed Architecture](architecture/component-name/detailed-spec.md) for comprehensive information.*
- **Requirement Traceability**: _Requirements: 1.1, 1.2, 4.6_
- **Document Relationships**: Links between requirements → design → tasks → implementation

## Project Status

### Current Phase
**Phase**: [requirements|design|tasks|implementation]
**Status**: [draft|approved|implemented]

### Development Progress
**Completion**: [X]% complete (based on task checkboxes)

## Document Relationships

```
requirements.md (WHAT) → design.md (HOW) → tasks.md (WHEN) → implementation
                ↓              ↓              ↓
            architecture/  data-model.md   progress tracking
                ↓              ↓              ↓
            detailed specs  schemas      task completion
```

## Maintenance Guidelines

### Update Triggers
- **requirements.md**: New features, scope changes, acceptance criteria updates
- **design.md**: Architecture decisions, technical challenges, interface changes
- **tasks.md**: Implementation approach changes, task completion
- **map.md**: Project structure changes, status updates
- **architecture/**: Detailed specification changes, new system components
- **data-model.md**: Data structure changes, schema updates

### Status Updates
- Update task checkboxes in tasks.md as work progresses
- Update phase status in map.md when transitioning between phases
- Use validation tools only when document quality is questionable

### Review Process
1. **Requirements**: Stakeholder review → Technical feasibility
2. **Design**: Architecture review → Implementation feasibility
3. **Tasks**: Development team review → Effort estimation
4. **Map**: Team review → Organization clarity

## Development Phases

### Phase 1: Requirements
**Goal**: Define WHAT needs to be built
**Output**: Approved requirements.md with EARS format
**Success**: All user stories have testable acceptance criteria

### Phase 2: Design
**Goal**: Define HOW it will be built
**Output**: Technical design with architecture references
**Success**: All requirements addressed in design

### Phase 3: Tasks
**Goal**: Define implementation steps
**Output**: Actionable task breakdown with verification
**Success**: Clear implementation roadmap approved

### Phase 4: Implementation
**Goal**: Build the feature systematically
**Output**: Working implementation with tests
**Success**: All tasks completed and verified

## File Organization

### Naming Conventions
- **Specifications**: Descriptive names (requirements.md, design.md)
- **Architecture**: System-based organization (core-systems/, interfaces/)
- **Implementation**: Follow project conventions


### Directory Principles
- **Separation of concerns**: Specs, code, tests, docs in separate directories
- **Logical grouping**: Related functionality grouped together
- **Scalability**: Structure supports growth without reorganization
- **Clarity**: Directory names clearly indicate purpose