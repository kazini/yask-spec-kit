#!/bin/bash

# Spec-Driven Development Automation Script
# This script provides utilities for managing spec-driven development workflows
# Compatible with various AI development agents

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/common.sh"

# Initialize a new project with spec-driven development structure
function init() {
    echo "Initializing spec-driven development structure..."
    
    # Create .specification directory structure
    mkdir -p .specification/{specs,templates,docs}
    
    # Copy templates if they exist
    if [ -d "$SCRIPT_DIR/../templates" ]; then
        cp -r "$SCRIPT_DIR/../templates/"* .specification/templates/
        echo "✓ Templates copied to .specification/templates/"
    fi
    
    # Create basic documentation
    cat > .specification/README.md << 'EOF'
# Specification Directory

This directory contains all specification documents for this project following the spec-driven development methodology.

## Structure

- `specs/` - Individual feature specifications
- `templates/` - Document templates for new specifications
- `docs/` - Supporting documentation and guidelines

## Usage

Use the provided scripts or AI agent commands to create and manage specifications.
EOF
    
    echo "✓ Spec-driven development structure initialized"
    echo "  Created: .specification/ directory"
    echo "  Use: ./scripts/spec.sh new <feature-name> to create your first spec"
}

# Create a new specification
function new() {
    local feature_name="$1"
    
    if [ -z "$feature_name" ]; then
        echo "Error: Feature name is required"
        echo "Usage: $0 new <feature-name>"
        exit 1
    fi
    
    # Sanitize feature name
    feature_name=$(echo "$feature_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
    
    local spec_dir=".specification/specs/$feature_name"
    
    if [ -d "$spec_dir" ]; then
        echo "Error: Specification '$feature_name' already exists"
        exit 1
    fi
    
    echo "Creating new specification: $feature_name"
    mkdir -p "$spec_dir"
    
    # Create requirements.md from template
    if [ -f ".specification/templates/requirements-template.md" ]; then
        cp ".specification/templates/requirements-template.md" "$spec_dir/requirements.md"
    else
        create_requirements_template "$spec_dir/requirements.md" "$feature_name"
    fi
    
    echo "✓ Created specification directory: $spec_dir"
    echo "✓ Created requirements.md from template"
    echo ""
    echo "Next steps:"
    echo "1. Edit $spec_dir/requirements.md to define your requirements"
    echo "2. Use your AI agent to iterate through the spec-driven development process"
}

# Create a basic requirements template
function create_requirements_template() {
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
function list() {
    local json_mode=false
    
    # Check for --json flag
    for arg in "$@"; do
        if [ "$arg" = "--json" ]; then
            json_mode=true
            break
        fi
    done
    
    if [ ! -d ".specification/specs" ]; then
        if [ "$json_mode" = true ]; then
            echo '{"specifications": [], "count": 0, "message": "No specifications found"}'
        else
            echo "Available specifications:"
            echo "  No specifications found. Use '$0 init' to initialize or '$0 new <name>' to create a spec."
        fi
        return
    fi
    
    local count=0
    local specs_json=""
    
    for spec_dir in .specification/specs/*/; do
        if [ -d "$spec_dir" ]; then
            local spec_name=$(basename "$spec_dir")
            local status=""
            local phase=""
            local has_requirements=false
            local has_design=false
            local has_tasks=false
            
            # Check file existence
            [ -f "$spec_dir/requirements.md" ] && has_requirements=true
            [ -f "$spec_dir/design.md" ] && has_design=true
            [ -f "$spec_dir/tasks.md" ] && has_tasks=true
            
            # Determine status and phase
            if [ "$has_requirements" = true ] && [ "$has_design" = true ] && [ "$has_tasks" = true ]; then
                status="Complete"
                phase="implementation"
            elif [ "$has_requirements" = true ] && [ "$has_design" = true ]; then
                status="Design Complete"
                phase="tasks"
            elif [ "$has_requirements" = true ]; then
                status="Requirements Only"
                phase="design"
            else
                status="Empty"
                phase="requirements"
            fi
            
            if [ "$json_mode" = true ]; then
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
    
    if [ "$json_mode" = true ]; then
        echo "{\"specifications\":[$specs_json],\"count\":$count}"
    else
        echo "Available specifications:"
        if [ $count -eq 0 ]; then
            echo "  No specifications found."
        fi
    fi
}

# Validate specification compliance with principles
function validate() {
    local json_mode=false
    local spec_name=""
    
    # Parse arguments
    for arg in "$@"; do
        case "$arg" in
            --json)
                json_mode=true
                ;;
            *)
                if [ -z "$spec_name" ]; then
                    spec_name="$arg"
                fi
                ;;
        esac
    done
    
    if [ -z "$spec_name" ]; then
        if [ "$json_mode" = false ]; then
            echo "Validating all specifications..."
        fi
        
        local total_issues=0
        local results=""
        local count=0
        
        for spec_dir in .specification/specs/*/; do
            if [ -d "$spec_dir" ]; then
                local name=$(basename "$spec_dir")
                local result=$(validate_single_spec_json "$name")
                local issues=$(echo "$result" | grep -o '"issues":[0-9]*' | cut -d: -f2 || echo "0")
                total_issues=$((total_issues + issues))
                
                if [ "$json_mode" = true ]; then
                    if [ $count -gt 0 ]; then
                        results="$results,"
                    fi
                    results="$results$result"
                    count=$((count + 1))
                else
                    validate_single_spec "$name"
                fi
            fi
        done
        
        if [ "$json_mode" = true ]; then
            echo "{\"specifications\":[$results],\"total_issues\":$total_issues,\"count\":$count}"
        fi
    else
        if [ "$json_mode" = true ]; then
            validate_single_spec_json "$spec_name"
        else
            validate_single_spec "$spec_name"
        fi
    fi
}

# Validate a single specification
function validate_single_spec() {
    local spec_name="$1"
    local spec_dir=".specification/specs/$spec_name"
    
    echo "Validating specification: $spec_name"
    
    if [ ! -d "$spec_dir" ]; then
        echo "  ✗ Specification directory not found"
        return 1
    fi
    
    local issues=0
    
    # Check for required files
    if [ -f "$spec_dir/requirements.md" ]; then
        echo "  ✓ requirements.md exists"
        
        # Basic content validation
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
    
    if [ -f "$spec_dir/design.md" ]; then
        echo "  ✓ design.md exists"
    else
        echo "  ⚠ design.md not yet created"
    fi
    
    if [ -f "$spec_dir/tasks.md" ]; then
        echo "  ✓ tasks.md exists"
    else
        echo "  ⚠ tasks.md not yet created"
    fi
    
    if [ $issues -eq 0 ]; then
        echo "  ✓ Specification validation passed"
    else
        echo "  ⚠ Specification has $issues issue(s)"
    fi
    
    echo ""
}

# Validate a single specification and return JSON
function validate_single_spec_json() {
    local spec_name="$1"
    local spec_dir=".specification/specs/$spec_name"
    
    if [ ! -d "$spec_dir" ]; then
        echo "{\"name\":\"$spec_name\",\"status\":\"error\",\"message\":\"Specification directory not found\",\"issues\":1}"
        return 1
    fi
    
    local issues=0
    local warnings=0
    local has_requirements=false
    local has_design=false
    local has_tasks=false
    local ears_format=false
    
    # Check for required files and content
    if [ -f "$spec_dir/requirements.md" ]; then
        has_requirements=true
        if grep -q "User Story:" "$spec_dir/requirements.md" && grep -q "WHEN.*THEN.*SHALL" "$spec_dir/requirements.md"; then
            ears_format=true
        else
            issues=$((issues + 1))
        fi
    else
        issues=$((issues + 1))
    fi
    
    [ -f "$spec_dir/design.md" ] && has_design=true || warnings=$((warnings + 1))
    [ -f "$spec_dir/tasks.md" ] && has_tasks=true || warnings=$((warnings + 1))
    
    local status="valid"
    if [ $issues -gt 0 ]; then
        status="invalid"
    elif [ $warnings -gt 0 ]; then
        status="incomplete"
    fi
    
    echo "{\"name\":\"$spec_name\",\"status\":\"$status\",\"issues\":$issues,\"warnings\":$warnings,\"files\":{\"requirements\":$has_requirements,\"design\":$has_design,\"tasks\":$has_tasks},\"ears_format\":$ears_format}"
}

# Show help information
function show_help() {
    cat << EOF
Spec-Driven Development Script

USAGE:
    $0 <command> [arguments]

COMMANDS:
    init                Initialize spec-driven development structure in current project
    new <feature-name>  Create a new specification for a feature
    list [--json]      List all specifications and their status
    validate [--json] [spec]    Validate specification(s) compliance with principles
    health             Run comprehensive project health check
    help               Show this help message

EXAMPLES:
    $0 init                    # Initialize project structure
    $0 new user-authentication # Create new spec for user authentication
    $0 list                    # Show all specifications
    $0 validate                # Validate all specifications
    $0 validate user-auth      # Validate specific specification
    $0 health                  # Run project health check

ADVANCED TOOLS:
    ./scripts/manage-subspecs.sh    # Manage sub-specifications for complex features
    ./scripts/project-health.sh     # Comprehensive project health validation
    ./scripts/validate-spec.sh      # Advanced specification validation

For more information, see the documentation in .spec-dev/
EOF
}

# Main command dispatcher
case "$1" in
    init)
        init
        ;;
    new)
        new "$2"
        ;;
    list)
        list
        ;;
    validate)
        validate "$2"
        ;;
    health)
        if [ -f "$SCRIPT_DIR/project-health.sh" ]; then
            "$SCRIPT_DIR/project-health.sh" "$@"
        else
            echo "Error: project-health.sh not found"
            exit 1
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
