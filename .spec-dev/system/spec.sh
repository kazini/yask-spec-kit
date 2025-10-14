#!/bin/bash

# Streamlined Spec-Driven Development Script
# Single script for all spec management functionality

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Configuration
JSON_MODE=false
FORCE_MODE=false

# Utility functions
get_project_root() {
    if git rev-parse --show-toplevel 2>/dev/null; then
        return 0
    fi
    
    local current_dir="$(pwd)"
    while [ "$current_dir" != "/" ]; do
        if [ -d "$current_dir/.specification" ]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    
    pwd
}

sanitize_feature_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Parse global flags
parse_flags() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --json)
                JSON_MODE=true
                shift
                ;;
            --force)
                FORCE_MODE=true
                shift
                ;;
            *)
                break
                ;;
        esac
    done
    echo "$@"
}

# Initialize project structure
init_project() {
    echo "Initializing spec-driven development structure..."
    
    mkdir -p .specification/{specs,templates,docs}
    
    if [ -d "$SCRIPT_DIR/../templates" ]; then
        cp -r "$SCRIPT_DIR/../templates/"* .specification/templates/
        echo "✓ Templates copied to .specification/templates/"
    fi
    
    cat > .specification/README.md << 'EOF'
# Specification Directory

This directory contains all specification documents for this project following the spec-driven development methodology.

## Structure

- `specs/` - Individual feature specifications
- `templates/` - Document templates for new specifications
- `docs/` - Supporting documentation and guidelines

## Usage

Use the spec-dev.sh script to create and manage specifications.
EOF
    
    echo "✓ Spec-driven development structure initialized"
    echo "  Use: ./scripts/spec-dev.sh new <feature-name> to create your first spec"
}

# Create new specification
create_spec() {
    local feature_name="$1"
    
    if [ -z "$feature_name" ]; then
        echo "Error: Feature name is required"
        echo "Usage: $0 new <feature-name>"
        exit 1
    fi
    
    feature_name=$(sanitize_feature_name "$feature_name")
    local spec_dir=".specification/specs/$feature_name"
    
    if [ -d "$spec_dir" ] && [ "$FORCE_MODE" = false ]; then
        echo "Error: Specification '$feature_name' already exists"
        echo "Use --force to overwrite"
        exit 1
    fi
    
    echo "Creating new specification: $feature_name"
    mkdir -p "$spec_dir"
    
    # Create requirements.md from template or basic version
    if [ -f ".specification/templates/requirements-template.md" ]; then
        cp ".specification/templates/requirements-template.md" "$spec_dir/requirements.md"
    else
        create_basic_requirements "$spec_dir/requirements.md" "$feature_name"
    fi
    
    if [ "$JSON_MODE" = true ]; then
        echo "{\"feature_name\":\"$feature_name\",\"spec_dir\":\"$spec_dir\",\"status\":\"created\"}"
    else
        echo "✓ Created specification directory: $spec_dir"
        echo "✓ Created requirements.md"
        echo ""
        echo "Next steps:"
        echo "1. Edit $spec_dir/requirements.md to define your requirements"
        echo "2. Use your AI agent to iterate through the development process"
    fi
}

# Create basic requirements template
create_basic_requirements() {
    local file_path="$1"
    local feature_name="$2"
    
    cat > "$file_path" << EOF
# Requirements Document

## Introduction

[Provide a clear summary of the $feature_name feature and its purpose]

## Requirements

### Requirement 1: [Requirement Title]

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN [system] SHALL [response]
2. IF [precondition] THEN [system] SHALL [response]

### Requirement 2: [Requirement Title]

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [event] THEN [system] SHALL [response]
2. WHEN [event] AND [condition] THEN [system] SHALL [response]

## Notes

[Any additional notes, constraints, or considerations]
EOF
}

# List all specifications
list_specs() {
    if [ ! -d ".specification/specs" ]; then
        if [ "$JSON_MODE" = true ]; then
            echo '{"specifications": [], "count": 0, "message": "No specifications found"}'
        else
            echo "No specifications found. Use 'spec-dev.sh init' to initialize."
        fi
        return
    fi
    
    local count=0
    local specs_json=""
    
    for spec_dir in .specification/specs/*/; do
        if [ -d "$spec_dir" ]; then
            local spec_name=$(basename "$spec_dir")
            local has_requirements=false
            local has_design=false
            local has_tasks=false
            
            [ -f "$spec_dir/requirements.md" ] && has_requirements=true
            [ -f "$spec_dir/design.md" ] && has_design=true
            [ -f "$spec_dir/tasks.md" ] && has_tasks=true
            
            local status="Empty"
            local phase="requirements"
            
            if [ "$has_requirements" = true ] && [ "$has_design" = true ] && [ "$has_tasks" = true ]; then
                status="Complete"
                phase="implementation"
            elif [ "$has_requirements" = true ] && [ "$has_design" = true ]; then
                status="Design Complete"
                phase="tasks"
            elif [ "$has_requirements" = true ]; then
                status="Requirements Only"
                phase="design"
            fi
            
            if [ "$JSON_MODE" = true ]; then
                if [ $count -gt 0 ]; then
                    specs_json="$specs_json,"
                fi
                specs_json="$specs_json{\"name\":\"$spec_name\",\"status\":\"$status\",\"phase\":\"$phase\",\"files\":{\"requirements\":$has_requirements,\"design\":$has_design,\"tasks\":$has_tasks}}"
            else
                echo "  $spec_name [$status]"
            fi
            
            count=$((count + 1))
        fi
    done
    
    if [ "$JSON_MODE" = true ]; then
        echo "{\"specifications\":[$specs_json],\"count\":$count}"
    else
        echo "Available specifications:"
        if [ $count -eq 0 ]; then
            echo "  No specifications found."
        fi
    fi
}

# Validate specification
validate_spec() {
    local spec_name="$1"
    
    if [ -z "$spec_name" ]; then
        echo "Error: Specification name is required"
        exit 1
    fi
    
    local spec_dir=".specification/specs/$spec_name"
    
    if [ ! -d "$spec_dir" ]; then
        echo "Error: Specification '$spec_name' not found"
        exit 1
    fi
    
    echo "Validating specification: $spec_name"
    
    local issues=0
    
    if [ -f "$spec_dir/requirements.md" ]; then
        echo "  ✓ requirements.md exists"
        
        if grep -q "User Story:" "$spec_dir/requirements.md" && grep -q "WHEN.*THEN.*SHALL" "$spec_dir/requirements.md"; then
            echo "  ✓ requirements.md contains proper EARS format"
        else
            echo "  ⚠ requirements.md may not follow EARS format properly"
            issues=$((issues + 1))
        fi
    else
        echo "  ✗ requirements.md missing"
        issues=$((issues + 1))
    fi
    
    [ -f "$spec_dir/design.md" ] && echo "  ✓ design.md exists" || echo "  ⚠ design.md not yet created"
    [ -f "$spec_dir/tasks.md" ] && echo "  ✓ tasks.md exists" || echo "  ⚠ tasks.md not yet created"
    
    if [ $issues -eq 0 ]; then
        echo "  ✓ Specification validation passed"
    else
        echo "  ⚠ Specification has $issues issue(s)"
    fi
}

# Create sub-specification
create_subspec() {
    local feature_name="$1"
    local subspec_name="$2"
    local doc_type="${3:-requirements}"
    
    if [ -z "$feature_name" ] || [ -z "$subspec_name" ]; then
        echo "Error: Both feature name and sub-specification name are required"
        exit 1
    fi
    
    local spec_dir=".specification/specs/$feature_name"
    
    if [ ! -d "$spec_dir" ]; then
        echo "Error: Feature specification '$feature_name' does not exist"
        exit 1
    fi
    
    subspec_name=$(sanitize_feature_name "$subspec_name")
    local subspec_dir="$spec_dir/$doc_type"
    local subspec_file="$subspec_dir/$subspec_name.md"
    
    mkdir -p "$subspec_dir"
    
    cat > "$subspec_file" << EOF
# $subspec_name $(echo $doc_type | sed 's/.*/\u&/')

## Document Metadata

**Purpose**: Detailed $doc_type for the $subspec_name component of the $feature_name feature.

**Parent Document**: [Main $(echo $doc_type | sed 's/.*/\u&/')](../$doc_type.md)

## Content

[Add detailed content here based on the document type]

## Cross-References

**Main $(echo $doc_type | sed 's/.*/\u&/')**: [../$doc_type.md](../$doc_type.md)

---

**Document Metadata:**
- Created: $(date +"%Y-%m-%d")
- Type: Sub-$(echo $doc_type | sed 's/.*/\u&/')
- Parent: $feature_name
- Component: $subspec_name
EOF

    echo "✓ Created $doc_type sub-specification: $subspec_file"
}

# Show help
show_help() {
    cat << EOF
Streamlined Spec-Driven Development Script

USAGE:
    $0 [OPTIONS] <command> [arguments]

GLOBAL OPTIONS:
    --json      Output results in JSON format
    --force     Force overwrite existing files

COMMANDS:
    init                        Initialize spec-driven development structure
    new <feature-name>          Create a new specification
    list                        List all specifications and their status
    validate <spec-name>        Validate specification compliance
    subspec <feature> <name> [type]  Create sub-specification (type: requirements|design|tasks)
    help                        Show this help message

EXAMPLES:
    $0 init                           # Initialize project structure
    $0 new user-authentication       # Create new spec
    $0 list                          # Show all specifications
    $0 validate user-auth            # Validate specific specification
    $0 subspec user-auth login-flow  # Create sub-specification

For more information, see the documentation in .spec-dev/
EOF
}

# Main command dispatcher
main() {
    local remaining_args=$(parse_flags "$@")
    set -- $remaining_args
    
    local command="$1"
    shift
    
    case "$command" in
        init)
            init_project
            ;;
        new)
            create_spec "$1"
            ;;
        list)
            list_specs
            ;;
        validate)
            validate_spec "$1"
            ;;
        subspec)
            create_subspec "$1" "$2" "$3"
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            echo "Error: Unknown command '$command'"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"