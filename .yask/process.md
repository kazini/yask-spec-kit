# Process & Strategy Guide

Complete workflow, communication, and strategic thinking guide for AI agents.

## Strategic Approach

### Context Assessment Framework

**Situational Analysis**: What exists? What's requested? What's missing? What's the goal?
**User Intent Analysis**: Analyze underlying intent, identify improvements, consider scope adjustments, spot issues
**Phase Identification**: Requirements, Design, Tasks, or Implementation phase
**Context Loading**: Load existing specs, templates, and project context as needed
**Execution Planning**: Content strategy, communication approach, quality checkpoints, error handling

### Decision Logic
```
User Request → Assess Context → Identify Phase → Load Documents → Execute → Summarize → Seek Approval
```

### Decision Logic

#### Phase Identification Decision Tree
```
User Request → 
├─ "Create requirements" → Requirements Phase
├─ "Design this feature" → Design Phase (check for requirements.md)
├─ "Break down tasks" → Tasks Phase (check for requirements.md + design.md)
├─ "Implement task X" → Implementation Phase (check for all documents)
└─ Unclear → Ask for clarification
```

#### Context Loading Strategy
- **Requirements**: Load user input + existing project context + requirements template
- **Design**: Load requirements.md + design template
- **Tasks**: Load requirements.md + design.md + tasks template  
- **Implementation**: Load requirements.md + design.md + tasks.md + current project files

### Scope Change Management

**WHEN scope changes occur**: Pause implementation and assess impact systematically

**THINKING PATTERN**: 
- **ASSESS** what documents and code need updating based on the change
- **PRIORITIZE** core specifications before supplementary documents before implementation
- **VERIFY** traceability and consistency after updates
- **CONFIRM** with user before resuming implementation

**HIERARCHY PRINCIPLE**: Core documents → Referenced documents → Architecture → Code → Tasks

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
- **Complex code issues**: Apply pseudocode reconstruction approach when standard fixes fail
- **File editing failures**: Try alternative methods (different tools, manual steps, user assistance) - NEVER claim completion without actually completing
- **Missing dependencies**: Stop, identify missing components, suggest implementation order
- **Test failures**: Stop, analyze failure, suggest fixes or approach changes
- **Technical difficulties**: Persist with alternative approaches rather than abandoning tasks

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

### Requirements Phase
**Objective**: Create complete `requirements.md` with user stories and EARS acceptance criteria
**Strategy**: Context loading → user intent analysis → strategic planning → content generation → quality validation → summary & approval
**Conceptual Prototyping**: Proactively expand on user ideas, explore possibilities, engage in creative conversation about end ideals

### Design Phase  
**Objective**: Create complete `design.md` addressing all requirements with technical architecture
**Strategy**: Load requirements.md → analyze and plan architecture → create components and design decisions → validate and seek approval

### Tasks Phase
**Objective**: Create complete `tasks.md` with hierarchical implementation tasks  
**Strategy**: Load requirements.md and design.md → plan implementation approach → create hierarchical tasks with traceability → validate and seek approval

### Implementation Phase
**Objective**: Execute tasks systematically with comprehensive summaries
**Strategy**: Load all specs → implement selected task → assess resources → verify → update documents → summarize → mark complete

## Self-Sufficiency & Resource Management

### Enhanced Capability Assessment Framework
**BEFORE starting any task:**
1. **Analyze task requirements**: What tools, libraries, information, or capabilities are needed?
2. **Assess current capabilities**: What can you accomplish directly with available access and tools?
3. **Evaluate data access**: What data can you actually obtain to verify outcomes?
4. **Identify verification limitations**: What aspects cannot be validated with available information?
5. **Identify gaps**: What's missing that prevents task completion or verification?
6. **Plan acquisition strategy**: How can missing resources be obtained?
7. **Consider alternatives**: If direct acquisition isn't possible, what workarounds exist?
8. **Communicate honestly**: Be transparent about capabilities, limitations, and verification boundaries

### Resource Acquisition Strategy

#### Tools & Dependencies
- **PREFER local installations**: Choose workspace-local over global installations when possible for project isolation
- **WHEN task requires tools**: Identify requirements and assess local vs global installation needs
- **IF local installation possible**: Use project-specific installation methods (npm install, pip install, etc.)
- **IF global installation needed**: Ask for user confirmation and explain why global is necessary
- **WHEN installation fails**: Provide alternative methods including manual setup instructions
- **VERIFY installation success**: Test that tools work correctly in the project context

#### Information & Context
- **WHEN missing project context**: Read existing requirements.md, design.md, package.json, README files
- **WHEN unclear about architecture**: Analyze existing code structure and patterns
- **WHEN missing configuration details**: Check config files, environment variables, documentation
- **IF information still missing**: Ask specific, targeted questions rather than generic requests

#### Capabilities & Skills
- **WHEN facing new technology**: Research available documentation and examples
- **WHEN uncertain about approach**: Analyze similar implementations or patterns
- **WHEN lacking specific knowledge**: Acknowledge limitations and suggest learning resources
- **IF task exceeds capabilities**: Propose alternative approaches or request user assistance

### Self-Sufficiency Principles
- **Maximize independence**: Do everything you can within your capabilities before asking for help
- **Be proactive**: Anticipate needs and prepare resources before they become blockers
- **Communicate transparently**: Clearly explain what you can and cannot do
- **Suggest alternatives**: When direct approaches aren't possible, propose workarounds
- **Learn and adapt**: Use each task as an opportunity to expand understanding
- **Confirm when needed**: Ask for user confirmation before making significant changes or installations
- **Enhanced limitation evaluation**: Systematically assess what data you can access and what verification is actually possible
- **Verification boundary awareness**: Clearly distinguish between what you can verify vs. what you must assume
- **Debug data integration**: Actively seek and incorporate diagnostic output, error messages, and system feedback to evaluate actual state
- **Assumption documentation**: When making assumptions due to limited access, explicitly document what cannot be verified
- **No false completion**: NEVER claim tasks are complete without actually completing them - try alternative methods when primary approaches fail

## Communication Strategy

### Core Principles
1. **Be Proactive**: Strategize and implement comprehensively within each phase
2. **Always Load Context**: Read all relevant documents before proceeding
3. **Provide Comprehensive Summaries**: Explain approach, decisions, and rationale
4. **Seek Approval at Phase Boundaries**: Only ask for confirmation when phase is complete
5. **Reference Patterns**: Direct to `patterns.md` for document structures
6. **Flexible Iteration**: When scope changes, update related documents accordingly

### Quality Validation Checkpoints

#### Requirements Phase Validation
- [ ] **EARS Format**: All acceptance criteria use `WHEN [event] THEN [system] SHALL [response]`
- [ ] **User Stories**: Each requirement has clear role, capability, and benefit
- [ ] **Completeness**: All user needs addressed
- [ ] **Testability**: Acceptance criteria are verifiable

#### Design Phase Validation
- [ ] **Requirements Coverage**: Every requirement addressed in design
- [ ] **Architecture Clarity**: System components and interactions clear
- [ ] **Design Decisions**: Options considered, rationale provided, impact explained
- [ ] **Error Handling**: Failure scenarios and recovery strategies defined

#### Tasks Phase Validation
- [ ] **Hierarchical Structure**: Main tasks with logical sub-tasks
- [ ] **Requirement Traceability**: Each task references specific requirements
- [ ] **Optional Tasks**: Testing and non-essential tasks marked with "*"
- [ ] **Incremental Approach**: Tasks build on each other logically

#### Implementation Phase Validation
- [ ] **Context Loaded**: All spec documents read before starting
- [ ] **Single Task Focus**: Only selected task implemented
- [ ] **Resource Acquisition**: Required tools acquired with user confirmation (prefer local)
- [ ] **Code Quality**: Implementation meets verification criteria with diagnostic validation
- [ ] **Comprehensive Summary**: Detailed explanation of what was accomplished
- [ ] **No False Completion**: All required actions actually completed

### Critical Rules

**Context Loading**: Read all existing spec documents, load appropriate templates, understand full project context
**Approval**: Be proactive within phases, seek approval only at phase completion, provide comprehensive summaries, wait for clear confirmation
**Content Quality**: Use EARS format, provide comprehensive summaries, reference specific requirements for traceability
**Implementation**: Work on user-selected task only, mark optional tasks with "*", stop after each task, assess and acquire resources with confirmation, update related documents
**Cross-Document Consistency**: WHEN requirements change → assess design updates, WHEN design changes → assess task updates, WHEN implementing → update requirements and design, MAINTAIN traceability throughout
**Communication**: Explain design decisions and rationale, provide task breakdown explanations, give comprehensive summaries

### Effective Prompting Examples

**Requirements**: "Generate requirements with user stories and EARS acceptance criteria, then provide a comprehensive summary of your approach"

**Design**: "Create technical design addressing all requirements from requirements.md, with clear architecture and design decisions"

**Tasks**: "Generate tasks.md with hierarchical checkbox format, requirement references, and mark optional tasks with '*'"

**Implementation**: "Execute the selected task from tasks.md, read all spec documents for context, implement the functionality, and provide a comprehensive summary"

*For complete document creation guidance, see `patterns.md`*