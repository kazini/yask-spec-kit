# Spec-Driven Development System Guide

Comprehensive system overview for AI agents in structured software development.

## Purpose
AI agent system for structured development: Requirements → Design → Tasks → Implementation

## Core Principles

1. **Clarity Before Code**: Understanding precedes implementation
2. **Iterative Refinement**: Each phase builds on validated foundations  
3. **Clean Documentation**: Focused, actionable content
4. **Manageable Complexity**: Break large features into focused sub-specs

## System Rules

1. **Three-Phase Process**: Requirements → Design → Tasks → Implementation
2. **User Approval**: Explicit approval required between phases
3. **EARS Format**: `WHEN [event] THEN [system] SHALL [response]`
4. **Sub-Specifications**: Break complex features into manageable parts
5. **Direct Implementation**: Simple file creation and editing

## Philosophy

### Clarity Before Code
**Principle**: Clarity of thought and purpose must precede implementation
**Benefits**: Reduce uncertainty, minimize rework, build the right thing correctly
**AI Impact**: Enables AI agents to understand requirements before coding

### Iterative Refinement
**Principle**: Each phase builds on validated foundations with explicit approval gates
**Benefits**: Early issue detection, solid phase progression, quality assurance
**AI Impact**: Structured approval workflow prevents AI agents from proceeding with flawed specs

### Clean Documentation
**Principle**: Focused, actionable content enables effective collaboration
**Benefits**: Clear communication, reduced overhead, better focus
**AI Impact**: Streamlined content allows AI agents to focus on implementation rather than parsing complex structures

### Human Validation
**Principle**: Human judgment guides AI implementation
**Benefits**: Quality control, stakeholder alignment, decision preservation
**AI Impact**: AI agents provide comprehensive summaries while humans make approval decisions

## Quick Commands
```bash
# Project setup
./.spec-dev/system/spec.sh init
./.spec-dev/system/spec.sh new "feature-name"

# Management
./.spec-dev/system/spec.sh list --json
./.spec-dev/system/spec.sh validate feature-name

# Sub-specifications
./.spec-dev/system/spec.sh subspec feature-name component-name
```

## Document Structure
```
.specification/specs/feature-name/
├── requirements.md  # EARS format with user stories
├── design.md       # Technical design with clear decisions
└── tasks.md        # Hierarchical implementation steps
```

## Process Flow
1. **Requirements**: EARS format + user approval
2. **Design**: Technical design + user approval  
3. **Tasks**: Coding tasks + user approval
4. **Implementation**: Execute tasks systematically

## Key Formats
- **EARS**: `WHEN [event] THEN [system] SHALL [response]`
- **Tasks**: Hierarchical with optional tasks marked "*"
- **Design Decisions**: Options considered, rationale, impact, requirements addressed

*See `patterns.md` for complete format examples and templates*

## AI Agent Collaboration

### Human-AI Workflow
1. **Human**: Provides feature idea and context
2. **AI Agent**: Generates structured requirements with comprehensive summaries
3. **Human**: Reviews and approves requirements
4. **AI Agent**: Creates technical design with clear decisions and rationale
5. **Human**: Validates design approach
6. **AI Agent**: Breaks down implementation into hierarchical tasks
7. **Human**: Selects tasks for execution
8. **AI Agent**: Implements tasks with context loading and detailed summaries

### AI Agent Benefits
- **Clear Context**: Requirements, design, and tasks provide comprehensive context
- **Focused Content**: Clean documentation without excessive overhead
- **Systematic Approach**: Structured phases with clear approval gates
- **Comprehensive Summaries**: Detailed explanations of approach and rationale

## Quality Standards
- **EARS format** for acceptance criteria
- **Requirement traceability** through all phases
- **User approval** at phase boundaries
- **Hierarchical task structure** with clear dependencies
- **Comprehensive summaries** explaining approach and rationale

## Core Files
- **`patterns.md`** - Document structure patterns and templates
- **`process.md`** - Complete workflow and communication guidance
- **`templates/`** - Document templates for consistent creation

## Key Features
- **Context Efficient**: Streamlined for AI agent consumption
- **Clean Documentation**: Focused, actionable content
- **Hierarchical Tasks**: Clear implementation structure
- **Human Validation**: User approval over automated metrics
- **Quality Focused**: Essential information without bloat
- **Cross-Platform**: Works across different development environments
- **Template-Based**: Consistent document creation with established patterns

## Implementation Best Practices

### Successful Adoption Strategies
1. **Start Simple**: Begin with small features to learn the methodology
2. **Use Templates**: Leverage provided templates for consistency
3. **Iterative Improvement**: Refine specifications based on feedback
4. **AI Collaboration**: Let AI agents handle structured generation while humans focus on validation
5. **Context Loading**: Always read all spec documents before implementation

### Common Pitfalls and Solutions
- **Skipping Approval Gates** → Always wait for explicit user approval
- **Incomplete Requirements** → Use EARS format for all acceptance criteria
- **Missing Traceability** → Include requirement references in all tasks
- **Inconsistent Formats** → Use templates and established patterns



## Usage Guidelines
1. Load this overview for complete system context and principles
2. Reference `patterns.md` for document creation and templates
3. Reference `process.md` for detailed workflow and communication guidance
4. Use `templates/` for actual template files
5. Follow the three-phase process with explicit approval gates

## Troubleshooting

### AI Agent Issues
**Symptoms**: AI generates incorrect or inconsistent specifications
**Solutions**:
- Provide clear, specific prompts referencing this methodology
- Use structured prompting patterns from process guide
- Reference templates for expected output format
- Break complex requests into smaller, focused tasks

### Approval Workflow Issues
**Symptoms**: Unclear approval status or skipped approvals
**Solutions**:
- Use flexible approval language adapted to circumstances
- Wait for explicit approval ("yes", "approved", "looks good")
- Ensure comprehensive summaries are provided at each phase

### Document Quality Issues
**Symptoms**: Inconsistent or incomplete specifications
**Solutions**:
- Use templates and established patterns
- Ensure EARS format compliance in requirements
- Verify cross-references between documents
- Focus on actionable, clear content

---
*Optimized for AI context efficiency while maintaining quality and structure.*