#!/bin/bash

# Create New Specification Script
# This script creates a new specification with proper structure and templates
# Compatible with various AI development agents

set -e

# Get script directory and source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Configuration
JSON_MODE=false
FORCE_MODE=false

# Parse command line arguments
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --force)
            FORCE_MODE=true
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
Create New Specification Script

USAGE:
    create-spec.sh [OPTIONS] <feature-description>

OPTIONS:
    --json      Output results in JSON format
    --force     Overwrite existing specification if it exists
    --help, -h  Show this help message

ARGUMENTS:
    feature-description    Description of the feature to create specification for

EXAMPLES:
    create-spec.sh "user authentication system"
    create-spec.sh --json "payment processing"
    create-spec.sh --force "existing feature update"

OUTPUT:
    Creates a new specification directory with:
    - requirements.md (from template)
    - Proper directory structure
    - Initial documentation

    In JSON mode, outputs paths for programmatic use:
    {
        "feature_name": "user-authentication-system",
        "feature_dir": "/path/to/.specification/specs/user-authentication-system",
        "requirements_file": "/path/to/.specification/specs/user-authentication-system/requirements.md"
    }
EOF
}

# Main function
main() {
    local feature_description="${ARGS[*]}"
    
    if [ -z "$feature_description" ]; then
        echo "Error: Feature description is required" >&2
        show_help
        exit 1
    fi
    
    # Validate project context
    if ! validate_project_context; then
        exit 1
    fi
    
    # Check if spec structure is initialized
    if ! check_spec_structure; then
        exit 1
    fi
    
    # Sanitize feature name
    local feature_name=$(sanitize_feature_name "$feature_description")
    
    # Get paths
    eval $(get_spec_paths "$feature_name")
    
    # Check if specification already exists
    if [ -d "$FEATURE_DIR" ] && [ "$FORCE_MODE" = false ]; then
        echo "Error: Specification '$feature_name' already exists" >&2
        echo "Use --force to overwrite or choose a different name" >&2
        exit 1
    fi
    
    # Create specification
    create_specification "$feature_name" "$feature_description"
    
    # Output results
    if [ "$JSON_MODE" = true ]; then
        output_json_result "$feature_name"
    else
        output_text_result "$feature_name"
    fi
}

# Create the specification structure
create_specification() {
    local feature_name="$1"
    local feature_description="$2"
    
    eval $(get_spec_paths "$feature_name")
    
    log_action "Creating specification: $feature_name"
    
    # Create directory structure
    mkdir -p "$FEATURE_DIR"
    
    # Create requirements.md from template
    create_requirements_file "$REQUIREMENTS" "$feature_name" "$feature_description"
    
    # Create placeholder files for future phases
    create_placeholder_files "$FEATURE_DIR"
    
    log_action "Specification created successfully"
}

# Create requirements.md file
create_requirements_file() {
    local requirements_file="$1"
    local feature_name="$2"
    local feature_description="$3"
    
    # Use template if available
    local template_file="$SPEC_DIR/templates/requirements-template.md"
    
    if [ -f "$template_file" ]; then
        # Copy template and customize
        cp "$template_file" "$requirements_file"
        
        # Replace placeholders if they exist
        if command_exists sed; then
            sed -i.bak "s/\[FEATURE_NAME\]/$feature_name/g" "$requirements_file" 2>/dev/null || true
            sed -i.bak "s/\[FEATURE_DESCRIPTION\]/$feature_description/g" "$requirements_file" 2>/dev/null || true
            rm -f "$requirements_file.bak" 2>/dev/null || true
        fi
    else
        # Create basic requirements template
        create_basic_requirements_template "$requirements_file" "$feature_name" "$feature_description"
    fi
}

# Create basic requirements template
create_basic_requirements_template() {
    local file="$1"
    local feature_name="$2"
    local feature_description="$3"
    
    cat > "$file" << EOF
# Requirements Document

## Introduction

The $feature_description is designed to [provide a clear summary of the feature and its purpose].

## Requirements

### Requirement 1: [Core Functionality]

**User Story:** As a [role], I want [feature capability], so that [benefit/value]

#### Acceptance Criteria

1. WHEN [trigger event] THEN [system] SHALL [expected response]
2. IF [precondition] THEN [system] SHALL [required behavior]
3. WHEN [user action] AND [context] THEN [system] SHALL [specific outcome]

### Requirement 2: [Secondary Functionality]

**User Story:** As a [role], I want [additional capability], so that [benefit/value]

#### Acceptance Criteria

1. WHEN [event occurs] THEN [system] SHALL [response]
2. IF [condition is met] THEN [system] SHALL [behavior]

## Constraints and Assumptions

- [List any technical constraints]
- [List any business constraints]
- [List any assumptions made]

## Success Criteria

- [Define what success looks like]
- [Include measurable outcomes where possible]

## Notes

[Any additional notes, considerations, or future enhancements to consider]
EOF
}

# Create placeholder files for future phases
create_placeholder_files() {
    local feature_dir="$1"
    
    # Create .gitkeep or similar to ensure directory structure is preserved
    touch "$feature_dir/.spec-metadata"
    
    # Add metadata about the specification
    cat > "$feature_dir/.spec-metadata" << EOF
# Specification Metadata
created_date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
phase: requirements
version: 1.0
EOF
}

# Output results in JSON format
output_json_result() {
    local feature_name="$1"
    eval $(get_spec_paths "$feature_name")
    
    cat << EOF
{
    "feature_name": "$feature_name",
    "feature_dir": "$FEATURE_DIR",
    "requirements_file": "$REQUIREMENTS",
    "phase": "requirements",
    "status": "created"
}
EOF
}

# Output results in text format
output_text_result() {
    local feature_name="$1"
    eval $(get_spec_paths "$feature_name")
    
    print_header "Specification Created"
    
    echo "Feature Name: $feature_name"
    echo "Directory: $FEATURE_DIR"
    echo "Requirements: $REQUIREMENTS"
    echo ""
    echo "Next Steps:"
    echo "1. Edit the requirements.md file to define your specific requirements"
    echo "2. Use your AI agent to iterate through the spec-driven development process"
    echo "3. Progress through: Requirements → Design → Tasks → Implementation"
    echo ""
    echo "Available Commands:"
    echo "  ./scripts/spec.sh list                    # List all specifications"
    echo "  ./scripts/spec.sh validate $feature_name  # Validate this specification"
}

# Run main function
main "$@"