# [Project Name]: Project Structure Map

## Project Organization

```
project-root/
├── .specification/specs/[feature-name]/
│   ├── requirements.md          # WHAT we need to build
│   ├── design.md               # HOW we'll build it
│   ├── tasks.md                # Implementation steps
│   ├── map.md                  # Project structure and status
│   ├── architecture/           # Detailed architectural specs
│   │   ├── core-systems/       # Core component specifications
│   │   ├── interfaces/         # API and data model specs
│   │   └── integration/        # System integration patterns
│   ├── data-model.md           # Data structures and schemas
│   └── .metadata/              # Separated metadata
│       ├── spec-metadata.json  # Core specification info
│       ├── health-status.json  # Health and compliance tracking
│       └── progress.json       # Task progress and completion
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
- **data-model.md**: Data structures, schemas, and relationships

### Metadata (Automated)
- **spec-metadata.json**: Status, phase, version, dependencies
- **health-status.json**: Health score, issues, compliance tracking
- **progress.json**: Task completion and progress metrics

## Project Status

### Current Phase
**Phase**: [requirements|design|tasks|implementation]
**Status**: [draft|approved|implemented]
**Health Score**: [Run: `./.spec-dev/scripts/spec-health.sh [feature-name]`]

### Development Progress
**Tasks**: [Run: `./.spec-dev/scripts/task-progress.sh [feature-name]`]
**Completion**: [X]% complete

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

### Metadata Updates (Automated)
```bash
# Update specification status
./.spec-dev/scripts/spec-meta.sh update [feature-name] --status approved --phase design

# Update task progress
./.spec-dev/scripts/task-progress.sh [feature-name] T-001 completed

# Update health metrics
./.spec-dev/scripts/health-update.sh [feature-name] --score 95

# Run health check
./.spec-dev/scripts/spec-health.sh [feature-name] --json
```

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
- **Metadata**: Automated JSON files in .metadata/

### Directory Principles
- **Separation of concerns**: Specs, code, tests, docs in separate directories
- **Logical grouping**: Related functionality grouped together
- **Scalability**: Structure supports growth without reorganization
- **Clarity**: Directory names clearly indicate purpose