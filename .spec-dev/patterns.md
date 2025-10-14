# Document Patterns & Templates

Comprehensive document creation guide for spec-driven development.

## Purpose
This guide provides complete document structures, templates, and formatting guidelines for creating consistent, high-quality specifications.

## Core Principles
1. **Clean, Scannable Content**: Organized, hierarchical format
2. **Essential Information**: Focus on actionable content only
3. **Template-Based Consistency**: Use established patterns
4. **Cross-Reference Support**: Clear links between documents



## Requirements Document

### Template Reference
Use `templates/requirements-template.md` as the starting point.

### Complete Structure
```markdown
# [Feature Name] Requirements

## Introduction
[Concise feature description and technical approach]

## Requirements

### Requirement 1: [Title]

**User Story:** As a [role], I want [capability], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN [system] SHALL [response]
2. IF [precondition] THEN [system] SHALL [behavior]

### Requirement 2: [Title]

**User Story:** As a [role], I want [capability], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN [system] SHALL [response]
2. WHEN [event] AND [condition] THEN [system] SHALL [behavior]

## Constraints & Assumptions

**Constraints:**
- [Technical/business constraints]

**Assumptions:**
- [Key assumptions about system/users]
```

### EARS Format Rules
- **WHEN**: `WHEN [event] THEN [system] SHALL [response]`
- **IF**: `IF [precondition] THEN [system] SHALL [response]`
- **WHERE**: `WHERE [condition] [system] SHALL [behavior]`

### Content Guidelines
- **User Stories**: Clear role, capability, and benefit
- **Acceptance Criteria**: Testable, unambiguous conditions
- **Constraints**: Technical and business limitations
- **Assumptions**: Key assumptions about system or users

## Design Document

### Template Reference
Use `templates/design-template.md` as the starting point.

### Complete Structure
```markdown
# [Feature Name] Design

## Overview
[System architecture summary and core innovation]

## Architecture
[High-level system design and integration points]

## Components

### [Component 1]
**Purpose**: [What this component does]
**Responsibilities**: [Key responsibilities]
**Interface**: [API or interface definition]

### [Component 2]
**Purpose**: [What this component does]
**Responsibilities**: [Key responsibilities]
**Interface**: [API or interface definition]

## Error Handling
- **Validation Errors**: [How input validation failures are handled]
- **System Errors**: [How infrastructure failures are handled]
- **Recovery**: [Fallback mechanisms and graceful degradation]

## Testing Strategy
- **Unit Tests**: [Component testing approach]
- **Integration Tests**: [System integration testing]
- **End-to-End Tests**: [User journey testing]

## Design Decisions

### Decision 1: [What was decided]
**Options considered**: [Option 1], [Option 2]
**Rationale**: [Why this option was chosen]
**Impact**: [Impact on system]
**Requirements addressed**: [Requirement references]
```

### Design Decision Format
Each design decision should include:
- **Options considered**: List alternatives that were evaluated
- **Rationale**: Why this option was chosen over others
- **Impact**: Effect on system architecture, performance, or maintainability
- **Requirements addressed**: Which requirements this decision satisfies

### Content Guidelines
- **Overview**: High-level architecture and key innovations
- **Architecture**: System design and integration points
- **Components**: Detailed component specifications with clear interfaces
- **Error Handling**: Comprehensive error scenarios and recovery strategies
- **Testing Strategy**: Approach for validating the design

## Tasks Document

### Template Reference
Use `templates/tasks-template.md` as the starting point.

### Complete Structure
```markdown
# [Feature Name] Implementation Tasks

## Tasks

- [ ] 1. Set up project structure and core interfaces
  - Create directory structure for models, services, repositories, and API components
  - Define interfaces that establish system boundaries
  - _Requirements: [Requirement references]_

- [ ] 2. Implement data models and validation
- [ ] 2.1 Create core data model interfaces and types
  - Write TypeScript interfaces for all data models
  - Implement validation functions for data integrity
  - _Requirements: [Requirement references]_

- [ ] 2.2 Implement User model with validation
  - Write User class with validation methods
  - _Requirements: [Requirement references]_

- [ ]* 2.3 Write unit tests for data models
  - Create unit tests for User model validation
  - Write unit tests for relationship management
  - _Requirements: [Requirement references]_

- [ ] 3. Create storage mechanism
- [ ] 3.1 Implement database connection utilities
  - Write connection management code
  - Create error handling utilities for database operations
  - _Requirements: [Requirement references]_

- [ ] 3.2 Implement repository pattern for data access
  - Code base repository interface
  - Implement concrete repositories with CRUD operations
  - _Requirements: [Requirement references]_
```

### Task Format Rules
- **Hierarchical Structure**: Use numbered main tasks (1, 2, 3) with sub-tasks (1.1, 1.2)
- **Checkbox Format**: `- [ ]` for pending, `- [x]` for completed
- **Optional Tasks**: Mark with `*` (e.g., `- [ ]* 1.2 Optional sub-task`)
- **Implementation Details**: Include specific steps under each task
- **Requirement References**: Use `_Requirements: [references]_` for traceability

### Content Guidelines
- **Incremental Approach**: Each task builds on previous tasks
- **Discrete Steps**: Tasks should be independently completable
- **Clear Verification**: Include how to verify task completion
- **Requirement Traceability**: Link tasks back to specific requirements

## Status Update Patterns

### Task Status Indicators
- `[ ]` - Pending task
- `[🚧]` - In-progress task  
- `[x]` - Completed task

## Reference Patterns

### Cross-References
```markdown
_Requirements: [Requirement references]_
_See design.md for technical details_
```

## Quality Standards

### Requirements
- EARS format: `WHEN [event] THEN [system] SHALL [response]`
- Clear user stories
- Technical precision

### Design  
- Address all requirements
- Clear architecture and rationale
- Component specifications

### Tasks
- Hierarchical structure with sub-tasks
- Discrete, actionable steps
- Requirement references
- Incremental approach

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



## AI Guidelines
1. **Clean Content**: Focus on clear, actionable content
2. **Proactive Behavior**: Comprehensive summaries and explanations
3. **Context Loading**: Always read requirements.md, design.md, tasks.md before implementation
4. **Hierarchical Tasks**: Structure with optional tasks marked "*"
5. **Single Task Focus**: Execute one task at a time with comprehensive summaries
6. **Human Validation**: User approval over automated metrics
7. **Quality Focus**: Working code over documentation compliance
8. **Diagnostic Approach**: Use health system sparingly when issues suspected
9. **Supplementary Docs**: Create map.md, architecture/ when needed
10. **Clear Traceability**: Link requirements → design → tasks → implementation

## AI Agent Communication Patterns

### Requirements Phase
- **Prompt**: Generate requirements with user stories and EARS acceptance criteria
- **Approval**: Ask for user approval to proceed to design phase
- **Behavior**: Provide comprehensive summary of approach and rationale

### Design Phase
- **Prompt**: Create technical design addressing all requirements with clear decisions
- **Approval**: Ask for user approval to proceed to implementation planning
- **Behavior**: Explain design decisions, trade-offs, and how they address requirements

### Tasks Phase
- **Prompt**: Break design into hierarchical tasks with requirement references
- **Approval**: Ask for user approval, explaining the task prioritization approach
- **Behavior**: Explain task breakdown, dependencies, and implementation approach

### Implementation Phase
- **Prompt**: "Execute user-selected task, read all spec documents for context, provide comprehensive summary"
- **Approval**: Get task selection from user, complete one task at a time
- **Behavior**: Context-aware implementation with detailed summaries

## Effective Prompting Guidelines

1. **Be Phase-Specific**: Reference the current phase and expected outputs
2. **Request Comprehensive Summaries**: Ask for explanations of approach and rationale
3. **Specify Context Loading**: Mention reading all spec documents before implementation
4. **Use Exact Approval Questions**: Use the specific approval questions from each phase
5. **Reference Standards**: Mention EARS format, hierarchical tasks, and verification criteria

## Common Prompting Mistakes

❌ **Avoid**: "Create a design document"
✅ **Use**: "Create a design.md document addressing all requirements from requirements.md, with clear architecture and design decisions"

❌ **Avoid**: "Make a task list"  
✅ **Use**: "Generate tasks.md with hierarchical checkbox format, requirement references, and mark optional tasks with '*'"

❌ **Avoid**: "Implement the feature"
✅ **Use**: "Execute the selected task from tasks.md, read all spec documents for context, implement the functionality, and provide a comprehensive summary"

## Related Documents
- **System Overview**: [overview.md](overview.md) - Complete system guide with principles and philosophy
- **Process Guide**: [process.md](process.md) - Workflow and communication guidance
## 
Available Templates

### Core Document Templates
- **`templates/requirements-template.md`** - EARS-formatted requirements document
- **`templates/design-template.md`** - Comprehensive technical design document  
- **`templates/tasks-template.md`** - Implementation task breakdown

### Specialized Templates
- **`templates/map-template.md`** - Project structure overview for complex features
- **`templates/architecture-readme-template.md`** - Detailed architecture specifications

## Template Usage Guidelines

### For AI Agents
1. **Reference templates** when creating documents (don't copy, use as structure guide)
2. **Follow the established patterns** while adapting content to the specific feature
3. **Maintain consistency** across all specifications in a project
4. **Use placeholder conventions** for customizable elements

### Template Structure Standards
All templates follow a consistent structure:
- **Clear title** with feature name
- **Introduction section** with context and purpose
- **Main content sections** with structured, scannable content
- **Cross-references** to related documents when applicable

### Placeholder Conventions
Templates use these placeholder conventions:
- `[Feature Name]` - Name of the feature being specified
- `[Title]` - Section or requirement title
- `[role]` - User role in user stories
- `[capability]` - What the user wants to do
- `[benefit]` - Why the user wants this capability
- `[event]` - Trigger condition in EARS format
- `[system]` - The system being specified
- `[response]` - Expected system behavior

## Quality Standards

### Document Quality Checklist
- [ ] **Clear structure** with logical section organization
- [ ] **Scannable format** with headers and bullet points
- [ ] **Actionable content** with specific guidance
- [ ] **EARS format** followed in requirements
- [ ] **Design addresses all requirements**
- [ ] **Tasks are hierarchical and actionable**
- [ ] **Requirements traced to design/tasks**
- [ ] **Cross-reference support** for document relationships

### Content Standards
- **Requirements**: EARS format, clear user stories, technical precision
- **Design**: Address all requirements, clear architecture and rationale, component specifications
- **Tasks**: Hierarchical structure with sub-tasks, discrete actionable steps, requirement references, incremental approach

## Supplementary Documents

### Map Document (Complex Projects)
**When to create**: For projects with >3 specification documents
**Template**: `templates/map-template.md`
**Purpose**: Project structure overview, status tracking, navigation guide

### Architecture Directory (Large Systems)
**When to create**: When design.md >10 pages or >5 major components
**Template**: `templates/architecture-readme-template.md`
**Purpose**: Detailed architectural specifications organized by system area

## Cross-References

### Document Relationships
```markdown
_Requirements: [Requirement references]_
_See design.md for technical details_
_Related: requirements.md → design.md → tasks.md_
```

### Navigation Patterns
- **Internal References**: `*See [Section](#section) for details*`
- **External References**: `*See [Design Document](design.md) for architecture*`
- **Requirement Traceability**: `_Requirements: 1.1, 1.2, 4.6_`

## Examples

### Simple Feature Example
A basic user authentication feature demonstrating the streamlined approach:

#### Requirements Structure
```markdown
# User Authentication Requirements

## Introduction
Simple user authentication system allowing account creation, login, and logout functionality.

## Requirements

### Requirement 1: Account Creation

**User Story:** As a new user, I want to create an account, so that I can access the application.

#### Acceptance Criteria

1. WHEN a user provides valid email and password THEN the system SHALL create a new account
2. IF the email already exists THEN the system SHALL display an error message
3. WHEN account creation succeeds THEN the system SHALL redirect to the login page
```

#### Design Structure
```markdown
# User Authentication Design

## Overview
Simple authentication system using JWT tokens for session management.

## Architecture
- Frontend form validation
- Backend API endpoints
- Database user storage
- JWT token generation

## Components

### Authentication Service
**Purpose**: Handle login/logout operations
**Responsibilities**: Validate credentials, generate tokens, manage sessions
**Interface**: REST API endpoints (/login, /logout, /register)

## Design Decisions

### Decision 1: JWT vs Session Cookies
**Options considered**: JWT tokens, Session cookies, OAuth integration
**Rationale**: JWT provides stateless authentication suitable for API-first design
**Impact**: Enables scalable authentication across multiple services
**Requirements addressed**: Account creation, login functionality
```

#### Tasks Structure
```markdown
# User Authentication Implementation Tasks

## Tasks

- [ ] 1. Set up authentication infrastructure
  - Create user database schema
  - Set up JWT token configuration
  - _Requirements: Account creation, login functionality_

- [ ] 2. Implement user registration
- [ ] 2.1 Create registration API endpoint
  - Validate email format and password strength
  - Check for existing users
  - _Requirements: Account creation_

- [ ] 2.2 Implement password hashing
  - Use bcrypt for secure password storage
  - _Requirements: Account creation security_

- [ ]* 2.3 Write registration tests
  - Test valid registration flow
  - Test duplicate email handling
  - _Requirements: Account creation_
```

### Key Patterns Demonstrated
- **Clean Structure**: No YAML frontmatter or JSON blocks
- **EARS Format**: Proper acceptance criteria structure
- **Hierarchical Tasks**: Clear main tasks with sub-tasks
- **Optional Tasks**: Testing marked with "*"
- **Requirement Traceability**: Clear links between phases

### Usage for AI Agents
These examples show the expected output format for each phase. Use them as reference when generating specifications to ensure consistency with current streamlined patterns.

*For workflow and communication guidance, see `process.md`*