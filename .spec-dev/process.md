
# Process & Strategy Guide

Complete workflow, communication, and strategic thinking guide for AI agents.

## Strategic Approach

### Context Assessment Framework

#### Step 1: Situational Analysis
- **What exists?**: Check for existing requirements.md, design.md, tasks.md
- **What's requested?**: Understand the specific user request
- **What's missing?**: Identify gaps in context or documentation
- **What's the goal?**: Determine the desired outcome

#### Step 2: Phase Identification
- **Requirements Phase**: Creating or updating requirements
- **Design Phase**: Creating technical design from requirements
- **Tasks Phase**: Breaking design into implementation steps
- **Implementation Phase**: Executing specific tasks

#### Step 3: Context Loading Strategy
- **Always Load**: All existing spec documents for the feature
- **Phase-Specific**: Additional templates and examples as needed
- **Project Context**: Current codebase and project files for implementation

#### Step 4: Execution Planning
- **Content Strategy**: What to create and how to structure it
- **Communication Strategy**: How to explain approach and seek approval
- **Quality Strategy**: What validation checkpoints to apply
- **Error Handling**: What could go wrong and how to recover

### Decision Logic
```
User Request → Assess Context → Identify Phase → Load Documents → Execute → Summarize → Seek Approval
```

### Decision Trees

#### Phase Identification Decision Tree
```
User Request → 
├─ "Create requirements" → Requirements Phase
├─ "Design this feature" → Design Phase (check for requirements.md)
├─ "Break down tasks" → Tasks Phase (check for requirements.md + design.md)
├─ "Implement task X" → Implementation Phase (check for all documents)
└─ Unclear → Ask for clarification
```

#### Context Loading Decision Tree
```
Phase Identified →
├─ Requirements → Load user input + existing project context
├─ Design → Load requirements.md + user input
├─ Tasks → Load requirements.md + design.md + user input
└─ Implementation → Load requirements.md + design.md + tasks.md + current project files
```

### Error Recovery Strategy

#### Missing Context Recovery
- **No requirements.md**: "I need the requirements document to proceed. Should I create it first?"
- **No design.md**: "I need the design document to create tasks. Should I create the design first?"
- **Incomplete documents**: "The [document] seems incomplete. Should I complete it before proceeding?"

#### Quality Issues Recovery
- **Poor EARS format**: Stop, explain EARS format, provide corrected examples
- **Missing traceability**: Stop, explain requirement references, add missing links
- **Unclear architecture**: Stop, ask specific clarifying questions about components

#### Implementation Issues Recovery
- **Code errors**: Stop, explain the error, suggest specific solutions
- **Missing dependencies**: Stop, identify missing components, suggest implementation order
- **Test failures**: Stop, analyze failure, suggest fixes or approach changes

#### Approval Issues Recovery
- **Unclear response**: Rephrase approval request with more context
- **Partial approval**: Ask specific questions about concerns
- **Rejection**: Ask for specific feedback and suggest revisions

## Workflow Overview
```
Requirements → Design → Tasks → Implementation
     ↓           ↓        ↓         ↓
  User Approval → User Approval → User Approval → Task Execution
```

## Phase Execution

### Phase 1: Requirements
**Objective**: Create complete `requirements.md` with user stories and EARS acceptance criteria

**Proactive Strategy**:
1. **Context Loading**: Load user input and any existing project context
2. **Strategic Planning**: Analyze user needs, identify key requirements, plan structure
3. **Content Generation**: Create comprehensive user stories with EARS format acceptance criteria
4. **Quality Validation**: Apply requirements validation checklist
5. **Summary & Approval**: Provide comprehensive summary of approach and seek phase completion approval

**Document Structure**: See `patterns.md` for complete requirements template

### Phase 2: Design
**Objective**: Create complete `design.md` addressing all requirements with technical architecture

**Proactive Strategy**:
1. **Context Loading**: Load existing `requirements.md` for full context
2. **Strategic Planning**: Analyze requirements, plan architecture, identify key components
3. **Content Generation**: Create architecture, components, design decisions with rationale
4. **Quality Validation**: Apply design validation checklist
5. **Summary & Approval**: Explain design decisions, trade-offs, and seek phase completion approval

**Document Structure**: See `patterns.md` for complete design template

### Phase 3: Tasks
**Objective**: Create complete `tasks.md` with hierarchical implementation tasks

**Proactive Strategy**:
1. **Context Loading**: Load existing `requirements.md` and `design.md`
2. **Strategic Planning**: Analyze design, plan implementation approach, identify dependencies
3. **Content Generation**: Create hierarchical tasks with requirement traceability and optional tasks
4. **Quality Validation**: Apply tasks validation checklist
5. **Summary & Approval**: Explain task breakdown, dependencies, and seek phase completion approval

**Document Structure**: See `patterns.md` for complete tasks template

### Phase 4: Implementation
**Objective**: Execute tasks systematically with comprehensive summaries

**Strategy**:
1. **Context Loading**: Read `requirements.md`, `design.md`, and `tasks.md` for full context
2. **Task Execution**: Implement selected task only
3. **Verification**: Test against verification criteria
4. **Summary**: Provide comprehensive summary of what was accomplished
5. **Status Update**: Mark task complete and stop for user review

**Status Indicators**: `[ ]` pending, `[x]` completed

## Communication Strategy

### Core Principles
1. **Be Proactive**: Strategize and implement comprehensively within each phase
2. **Always Load Context**: Read all relevant documents before proceeding
3. **Provide Comprehensive Summaries**: Explain approach, decisions, and rationale
4. **Seek Approval at Phase Boundaries**: Only ask for confirmation when phase is complete
5. **Reference Patterns**: Direct to `patterns.md` for document structures

### Quality Validation Checkpoints

#### Requirements Phase Validation
- [ ] **EARS Format**: All acceptance criteria use `WHEN [event] THEN [system] SHALL [response]`
- [ ] **User Stories**: Each requirement has clear role, capability, and benefit
- [ ] **Completeness**: All user needs addressed
- [ ] **Testability**: Acceptance criteria are verifiable
- [ ] **Constraints**: Technical and business limitations documented

#### Design Phase Validation
- [ ] **Requirements Coverage**: Every requirement addressed in design
- [ ] **Architecture Clarity**: System components and interactions clear
- [ ] **Design Decisions**: Options considered, rationale provided, impact explained
- [ ] **Error Handling**: Failure scenarios and recovery strategies defined
- [ ] **Testing Strategy**: Validation approach outlined

#### Tasks Phase Validation
- [ ] **Hierarchical Structure**: Main tasks with logical sub-tasks
- [ ] **Requirement Traceability**: Each task references specific requirements
- [ ] **Optional Tasks**: Testing and non-essential tasks marked with "*"
- [ ] **Incremental Approach**: Tasks build on each other logically
- [ ] **Implementation Details**: Specific steps provided for each task

#### Implementation Phase Validation
- [ ] **Context Loaded**: All spec documents read before starting
- [ ] **Single Task Focus**: Only selected task implemented
- [ ] **Code Quality**: Implementation meets verification criteria
- [ ] **Comprehensive Summary**: Detailed explanation of what was accomplished
- [ ] **Status Updated**: Task marked complete in tasks.md

### Critical Rules (All Phases)

#### Context Loading Rules
- **MUST** read all existing spec documents before proceeding with any phase
- **MUST** load appropriate templates from `patterns.md` for document structure
- **MUST** understand full project context before implementation

#### Approval Rules
- **MUST** be proactive in strategizing and implementing within each phase
- **MUST** seek approval only at phase completion, not for micro-decisions
- **MUST** provide comprehensive summary and seek confirmation before moving to next phase
- **MUST** wait for clear confirmation ("yes", "approved", "looks good", etc.) only at phase boundaries

#### Content Quality Rules
- **MUST** use EARS format for all acceptance criteria: `WHEN [event] THEN [system] SHALL [response]`
- **MUST** provide comprehensive summaries explaining approach and rationale
- **MUST** reference specific requirements in design and tasks for traceability

#### Implementation Rules
- **MUST** work on user-selected task only during implementation
- **MUST** mark optional tasks with "*" and not implement unless explicitly requested
- **MUST** stop after each task/phase for user review
- **MUST NOT** proceed to next task automatically

#### Communication Rules
- **MUST** explain design decisions, trade-offs, and rationale
- **MUST** provide task breakdown explanations with dependencies
- **MUST** give comprehensive summaries of what was accomplished

### Effective Prompting Examples

**Requirements**: "Generate requirements with user stories and EARS acceptance criteria, then provide a comprehensive summary of your approach"

**Design**: "Create technical design addressing all requirements from requirements.md, with clear architecture and design decisions"

**Tasks**: "Generate tasks.md with hierarchical checkbox format, requirement references, and mark optional tasks with '*'"

**Implementation**: "Execute the selected task from tasks.md, read all spec documents for context, implement the functionality, and provide a comprehensive summary"

*For complete document creation guidance, see `patterns.md`*
