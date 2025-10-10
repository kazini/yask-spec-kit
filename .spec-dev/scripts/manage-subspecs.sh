#!/bin/bash

# Sub-Specification Management Script
# Manages hierarchical specifications for complex features
# Compatible with various AI development agents

set -e

# Get script directory and source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Configuration
JSON_MODE=false

# Parse command line arguments
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Show help information
show_help() {
    cat << 'EOF'
Sub-Specification Management Script

USAGE:
    manage-subspecs.sh [OPTIONS] <command> [arguments]

COMMANDS:
    create <feature-name> <subspec-name>    Create a sub-specification
    list <feature-name>                     List all sub-specifications
    link <feature-name> <subspec-name>      Add link to main document
    validate <feature-name>                 Validate sub-specification structure

OPTIONS:
    --json      Output results in JSON format
    --help, -h  Show this help message

EXAMPLES:
    manage-subspecs.sh create user-auth authentication-flow
    manage-subspecs.sh list user-auth
    manage-subspecs.sh link user-auth authentication-flow
    manage-subspecs.sh validate user-auth

DESCRIPTION:
    This script helps manage complex specifications by breaking them into
    focused sub-specifications while maintaining proper cross-references
    and navigation aids.
EOF
}

# Create a sub-specification
create_subspec() {
    local feature_name="$1"
    local subspec_name="$2"
    
    if [ -z "$feature_name" ] || [ -z "$subspec_name" ]; then
        echo "Error: Both feature name and sub-specification name are required" >&2
        exit 1
    fi
    
    # Validate project context
    if ! validate_project_context; then
        exit 1
    fi
    
    # Get paths
    eval $(get_spec_paths "$feature_name")
    
    if [ ! -d "$FEATURE_DIR" ]; then
        echo "Error: Feature specification '$feature_name' does not exist" >&2
        echo "Create it first with: ./scripts/spec.sh new $feature_name" >&2
        exit 1
    fi
    
    # Sanitize sub-specification name
    local clean_subspec_name=$(sanitize_feature_name "$subspec_name")
    
    # Determine document type and create appropriate sub-specification
    local doc_type="${ARGS[2]:-requirements}"  # Default to requirements
    
    case "$doc_type" in
        requirements|req)
            create_requirements_subspec "$feature_name" "$clean_subspec_name"
            ;;
        design|des)
            create_design_subspec "$feature_name" "$clean_subspec_name"
            ;;
        tasks|task)
            create_tasks_subspec "$feature_name" "$clean_subspec_name"
            ;;
        *)
            echo "Error: Unknown document type '$doc_type'. Use: requirements, design, or tasks" >&2
            exit 1
            ;;
    esac
}

# Create requirements sub-specification
create_requirements_subspec() {
    local feature_name="$1"
    local subspec_name="$2"
    
    eval $(get_spec_paths "$feature_name")
    local subspec_dir="$FEATURE_DIR/requirements"
    local subspec_file="$subspec_dir/$subspec_name.md"
    
    # Create sub-specification directory
    mkdir -p "$subspec_dir"
    
    # Create sub-specification file
    cat > "$subspec_file" << EOF
# $subspec_name Requirements

## Document Metadata

**Purpose**: Detailed requirements for the $subspec_name component of the $feature_name feature.

**Parent Document**: [Main Requirements](../requirements.md)

**Related Sub-Specifications**:
- [List other related sub-specifications here]

## Requirements

### Requirement 1: [Specific Requirement Title]

**User Story:** As a [role], I want [specific capability], so that [specific benefit]

#### Acceptance Criteria

1. WHEN [specific event] THEN [system] SHALL [specific response]
2. IF [specific condition] THEN [system] SHALL [specific behavior]

### Requirement 2: [Additional Requirement]

**User Story:** As a [role], I want [capability], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN [system] SHALL [response]
2. WHEN [event] AND [condition] THEN [system] SHALL [outcome]

## Integration Requirements

### Dependencies
- [List dependencies on other components]
- [Include integration points and interfaces]

### Constraints
- [Specific constraints for this component]
- [Technical or business limitations]

## Cross-References

**Main Requirements**: [../requirements.md](../requirements.md)
**Related Design**: [../design.md](../design.md)
**Implementation Tasks**: [../tasks.md](../tasks.md)

---

**Document Metadata:**
- Created: $(date +"%Y-%m-%d")
- Type: Sub-Requirements
- Parent: $feature_name
- Component: $subspec_name
EOF

    echo "✓ Created requirements sub-specification: $subspec_file"
    
    # Update main requirements document
    update_main_requirements_with_link "$feature_name" "$subspec_name"
}

# Create design sub-specification
create_design_subspec() {
    local feature_name="$1"
    local subspec_name="$2"
    
    eval $(get_spec_paths "$feature_name")
    local subspec_dir="$FEATURE_DIR/design"
    local subspec_file="$subspec_dir/$subspec_name.md"
    
    # Create sub-specification directory
    mkdir -p "$subspec_dir"
    
    # Create sub-specification file
    cat > "$subspec_file" << EOF
# $subspec_name Design

## Document Metadata

**Purpose**: Detailed design specifications for the $subspec_name component.

**Parent Document**: [Main Design](../design.md)

**Related Components**:
- [List related design components here]

## Component Overview

### Purpose
[Describe what this component does and why it's needed]

### Key Responsibilities
- [Primary responsibility]
- [Secondary responsibility]
- [Additional responsibilities]

## Architecture

### Component Architecture
[Describe the internal architecture of this component]

### Integration Points
- **[Component/Service 1]**: [How this integrates]
- **[Component/Service 2]**: [Integration approach]

### Data Flow
1. **[Step 1]**: [Description of data flow step]
2. **[Step 2]**: [How data moves through component]
3. **[Step 3]**: [Final processing or output]

## Interfaces

### Public Interface
\`\`\`typescript
// Public API for this component
interface ${subspec_name^}Interface {
    method1(param: Type): ReturnType;
    method2(param: Type): Promise<ReturnType>;
}
\`\`\`

### Internal Interface
\`\`\`typescript
// Internal interfaces if needed
\`\`\`

## Implementation Details

### Key Algorithms
[Describe important algorithms or processing logic]

### Performance Considerations
[Performance requirements and optimization strategies]

### Error Handling
[How this component handles errors and edge cases]

## Cross-References

**Main Design**: [../design.md](../design.md)
**Requirements**: [../requirements.md](../requirements.md)
**Implementation Tasks**: [../tasks.md](../tasks.md)

---

**Document Metadata:**
- Created: $(date +"%Y-%m-%d")
- Type: Sub-Design
- Parent: $feature_name
- Component: $subspec_name
EOF

    echo "✓ Created design sub-specification: $subspec_file"
    
    # Update main design document
    update_main_design_with_link "$feature_name" "$subspec_name"
}

# Update main requirements document with sub-specification link
update_main_requirements_with_link() {
    local feature_name="$1"
    local subspec_name="$2"
    
    eval $(get_spec_paths "$feature_name")
    
    # Check if main requirements file exists
    if [ ! -f "$REQUIREMENTS" ]; then
        echo "Warning: Main requirements file not found: $REQUIREMENTS"
        return 1
    fi
    
    # Add sub-specification reference section if it doesn't exist
    if ! grep -q "## Sub-Specifications" "$REQUIREMENTS"; then
        cat >> "$REQUIREMENTS" << EOF

## Sub-Specifications

This feature is broken down into the following detailed sub-specifications:

- **[$subspec_name](requirements/$subspec_name.md)** - Detailed requirements for $subspec_name component

EOF
    else
        # Add link to existing sub-specifications section
        sed -i "/## Sub-Specifications/a\\
- **[$subspec_name](requirements/$subspec_name.md)** - Detailed requirements for $subspec_name component" "$REQUIREMENTS"
    fi
    
    echo "✓ Updated main requirements document with link to $subspec_name"
}

# Update main design document with sub-specification link
update_main_design_with_link() {
    local feature_name="$1"
    local subspec_name="$2"
    
    eval $(get_spec_paths "$feature_name")
    
    # Check if main design file exists
    if [ ! -f "$DESIGN" ]; then
        echo "Warning: Main design file not found: $DESIGN"
        return 1
    fi
    
    # Add detailed specifications reference section if it doesn't exist
    if ! grep -q "## Detailed Specifications" "$DESIGN"; then
        cat >> "$DESIGN" << EOF

## Detailed Specifications

For comprehensive technical details, see the following detailed specifications:

- **[$subspec_name](design/$subspec_name.md)** - Detailed design for $subspec_name component

EOF
    else
        # Add link to existing detailed specifications section
        sed -i "/## Detailed Specifications/a\\
- **[$subspec_name](design/$subspec_name.md)** - Detailed design for $subspec_name component" "$DESIGN"
    fi
    
    echo "✓ Updated main design document with link to $subspec_name"
}

# List all sub-specifications for a feature
list_subspecs() {
    local feature_name="$1"
    
    if [ -z "$feature_name" ]; then
        echo "Error: Feature name is required" >&2
        exit 1
    fi
    
    eval $(get_spec_paths "$feature_name")
    
    if [ ! -d "$FEATURE_DIR" ]; then
        echo "Error: Feature specification '$feature_name' does not exist" >&2
        exit 1
    fi
    
    echo "Sub-specifications for $feature_name:"
    
    local found_any=false
    
    # List requirements sub-specifications
    if [ -d "$FEATURE_DIR/requirements" ]; then
        echo ""
        echo "Requirements Sub-Specifications:"
        for subspec in "$FEATURE_DIR/requirements"/*.md; do
            if [ -f "$subspec" ]; then
                local name=$(basename "$subspec" .md)
                echo "  - $name"
                found_any=true
            fi
        done
    fi
    
    # List design sub-specifications
    if [ -d "$FEATURE_DIR/design" ]; then
        echo ""
        echo "Design Sub-Specifications:"
        for subspec in "$FEATURE_DIR/design"/*.md; do
            if [ -f "$subspec" ]; then
                local name=$(basename "$subspec" .md)
                echo "  - $name"
                found_any=true
            fi
        done
    fi
    
    # List tasks sub-specifications
    if [ -d "$FEATURE_DIR/tasks" ]; then
        echo ""
        echo "Tasks Sub-Specifications:"
        for subspec in "$FEATURE_DIR/tasks"/*.md; do
            if [ -f "$subspec" ]; then
                local name=$(basename "$subspec" .md)
                echo "  - $name"
                found_any=true
            fi
        done
    fi
    
    if [ "$found_any" = false ]; then
        echo "  No sub-specifications found."
        echo "  Use: manage-subspecs.sh create $feature_name <subspec-name> to create one."
    fi
}

# Validate sub-specification structure
validate_subspecs() {
    local feature_name="$1"
    
    if [ -z "$feature_name" ]; then
        echo "Error: Feature name is required" >&2
        exit 1
    fi
    
    eval $(get_spec_paths "$feature_name")
    
    if [ ! -d "$FEATURE_DIR" ]; then
        echo "Error: Feature specification '$feature_name' does not exist" >&2
        exit 1
    fi
    
    echo "Validating sub-specifications for $feature_name:"
    
    local issues=0
    
    # Validate requirements sub-specifications
    if [ -d "$FEATURE_DIR/requirements" ]; then
        for subspec in "$FEATURE_DIR/requirements"/*.md; do
            if [ -f "$subspec" ]; then
                local name=$(basename "$subspec" .md)
                echo "  Validating requirements/$name.md"
                
                # Check for required sections
                if grep -q "## Requirements" "$subspec"; then
                    echo "    ✓ Has Requirements section"
                else
                    echo "    ✗ Missing Requirements section"
                    issues=$((issues + 1))
                fi
                
                # Check for cross-references
                if grep -q "Cross-References" "$subspec"; then
                    echo "    ✓ Has Cross-References section"
                else
                    echo "    ⚠ Missing Cross-References section"
                fi
            fi
        done
    fi
    
    # Validate design sub-specifications
    if [ -d "$FEATURE_DIR/design" ]; then
        for subspec in "$FEATURE_DIR/design"/*.md; do
            if [ -f "$subspec" ]; then
                local name=$(basename "$subspec" .md)
                echo "  Validating design/$name.md"
                
                # Check for required sections
                if grep -q "## Component Overview" "$subspec"; then
                    echo "    ✓ Has Component Overview section"
                else
                    echo "    ✗ Missing Component Overview section"
                    issues=$((issues + 1))
                fi
                
                if grep -q "## Architecture" "$subspec"; then
                    echo "    ✓ Has Architecture section"
                else
                    echo "    ✗ Missing Architecture section"
                    issues=$((issues + 1))
                fi
            fi
        done
    fi
    
    echo ""
    if [ $issues -eq 0 ]; then
        echo "✓ All sub-specifications are valid"
    else
        echo "⚠ Found $issues validation issue(s)"
    fi
}

# Main function
main() {
    local command="${ARGS[0]}"
    
    case "$command" in
        create)
            create_subspec "${ARGS[1]}" "${ARGS[2]}"
            ;;
        list)
            list_subspecs "${ARGS[1]}"
            ;;
        validate)
            validate_subspecs "${ARGS[1]}"
            ;;
        *)
            echo "Error: Unknown command '$command'" >&2
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"