#!/bin/bash

# Validate Specification Script
# This script validates specifications against the principles and standards
# Compatible with various AI development agents

set -e

# Get script directory and source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Configuration
JSON_MODE=false
VERBOSE_MODE=false
FIX_MODE=false

# Parse command line arguments
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --verbose|-v)
            VERBOSE_MODE=true
            ;;
        --fix)
            FIX_MODE=true
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
Validate Specification Script

USAGE:
    validate-spec.sh [OPTIONS] [feature-name]

OPTIONS:
    --json         Output results in JSON format
    --verbose, -v  Show detailed validation information
    --fix          Attempt to fix common issues automatically
    --help, -h     Show this help message

ARGUMENTS:
    feature-name   Name of specific specification to validate (optional)
                   If not provided, validates all specifications

EXAMPLES:
    validate-spec.sh                           # Validate all specifications
    validate-spec.sh user-authentication       # Validate specific specification
    validate-spec.sh --json --verbose          # Detailed JSON output for all specs
    validate-spec.sh --fix user-auth           # Validate and fix issues

VALIDATION CHECKS:
    - File structure compliance
    - EARS format in requirements
    - Document completeness
    - Cross-reference consistency
    - Principles compliance
EOF
}

# Main validation function
main() {
    local feature_name="${ARGS[0]}"
    
    # Validate project context
    if ! validate_project_context; then
        exit 1
    fi
    
    # Check if spec structure is initialized
    if ! check_spec_structure; then
        exit 1
    fi
    
    if [ -n "$feature_name" ]; then
        # Validate single specification
        validate_single_specification "$feature_name"
    else
        # Validate all specifications
        validate_all_specifications
    fi
}

# Validate all specifications
validate_all_specifications() {
    local project_root=$(get_project_root)
    local spec_dir=$(get_spec_dir "$project_root")
    local specs_found=false
    local total_issues=0
    
    if [ "$JSON_MODE" = false ]; then
        print_header "Validating All Specifications"
    fi
    
    local results=()
    
    for spec_path in "$spec_dir/specs"/*; do
        if [ -d "$spec_path" ]; then
            specs_found=true
            local spec_name=$(basename "$spec_path")
            local result=$(validate_specification_internal "$spec_name")
            local issues=$(echo "$result" | jq -r '.issues_count' 2>/dev/null || echo "0")
            total_issues=$((total_issues + issues))
            
            if [ "$JSON_MODE" = true ]; then
                results+=("$result")
            fi
        fi
    done
    
    if [ "$specs_found" = false ]; then
        if [ "$JSON_MODE" = true ]; then
            echo '{"status": "no_specs", "message": "No specifications found"}'
        else
            echo "No specifications found."
            echo "Use './scripts/spec.sh new <feature-name>' to create a specification."
        fi
        return 0
    fi
    
    # Output results
    if [ "$JSON_MODE" = true ]; then
        echo "{"
        echo "  \"status\": \"complete\","
        echo "  \"total_issues\": $total_issues,"
        echo "  \"specifications\": ["
        printf '%s\n' "${results[@]}" | paste -sd ',' -
        echo "  ]"
        echo "}"
    else
        echo ""
        if [ $total_issues -eq 0 ]; then
            echo "✓ All specifications passed validation"
        else
            echo "⚠ Found $total_issues total issues across all specifications"
            if [ "$FIX_MODE" = true ]; then
                echo "  (Some issues may have been automatically fixed)"
            fi
        fi
    fi
}

# Validate single specification
validate_single_specification() {
    local feature_name="$1"
    
    if [ "$JSON_MODE" = true ]; then
        validate_specification_internal "$feature_name"
    else
        print_header "Validating Specification: $feature_name"
        validate_specification_internal "$feature_name" | jq -r '.message' 2>/dev/null || echo "Validation completed"
    fi
}

# Internal validation function that returns structured results
validate_specification_internal() {
    local feature_name="$1"
    eval $(get_spec_paths "$feature_name")
    
    local issues=()
    local warnings=()
    local fixes_applied=()
    
    # Check if specification directory exists
    if [ ! -d "$FEATURE_DIR" ]; then
        local error_msg="Specification directory not found: $FEATURE_DIR"
        if [ "$JSON_MODE" = true ]; then
            echo "{\"status\": \"error\", \"feature_name\": \"$feature_name\", \"message\": \"$error_msg\", \"issues_count\": 1}"
        else
            echo "✗ $error_msg"
        fi
        return 1
    fi
    
    # Validate file structure
    validate_file_structure "$feature_name" issues warnings fixes_applied
    
    # Validate requirements document
    if [ -f "$REQUIREMENTS" ]; then
        validate_requirements_document "$REQUIREMENTS" issues warnings fixes_applied
    fi
    
    # Validate design document
    if [ -f "$DESIGN" ]; then
        validate_design_document "$DESIGN" issues warnings fixes_applied
    fi
    
    # Validate tasks document
    if [ -f "$TASKS" ]; then
        validate_tasks_document "$TASKS" issues warnings fixes_applied
    fi
    
    # Validate cross-references
    validate_cross_references "$feature_name" issues warnings fixes_applied
    
    # Generate output
    local issues_count=${#issues[@]}
    local warnings_count=${#warnings[@]}
    local fixes_count=${#fixes_applied[@]}
    
    if [ "$JSON_MODE" = true ]; then
        generate_json_output "$feature_name" "$issues_count" "$warnings_count" "$fixes_count" issues warnings fixes_applied
    else
        generate_text_output "$feature_name" "$issues_count" "$warnings_count" "$fixes_count" issues warnings fixes_applied
    fi
}

# Validate file structure
validate_file_structure() {
    local feature_name="$1"
    local -n issues_ref=$2
    local -n warnings_ref=$3
    local -n fixes_ref=$4
    
    eval $(get_spec_paths "$feature_name")
    
    # Check for requirements.md
    if [ ! -f "$REQUIREMENTS" ]; then
        issues_ref+=("Missing requirements.md file")
        
        if [ "$FIX_MODE" = true ]; then
            create_basic_requirements_template "$REQUIREMENTS" "$feature_name" "$feature_name"
            fixes_ref+=("Created basic requirements.md template")
        fi
    fi
    
    # Check for proper directory structure
    if [ ! -f "$FEATURE_DIR/.spec-metadata" ]; then
        warnings_ref+=("Missing specification metadata")
        
        if [ "$FIX_MODE" = true ]; then
            cat > "$FEATURE_DIR/.spec-metadata" << EOF
# Specification Metadata
created_date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
phase: $(get_spec_phase "$feature_name")
version: 1.0
EOF
            fixes_ref+=("Created specification metadata")
        fi
    fi
}

# Validate requirements document
validate_requirements_document() {
    local requirements_file="$1"
    local -n issues_ref=$2
    local -n warnings_ref=$3
    local -n fixes_ref=$4
    
    # Check for EARS format
    if ! validate_ears_format "$requirements_file"; then
        issues_ref+=("Requirements document does not follow EARS format (WHEN...THEN...SHALL or IF...THEN...SHALL)")
    fi
    
    # Check for user stories
    if ! grep -q "User Story:" "$requirements_file"; then
        issues_ref+=("Requirements document missing user stories")
    fi
    
    # Check for acceptance criteria
    if ! grep -q "Acceptance Criteria" "$requirements_file"; then
        issues_ref+=("Requirements document missing acceptance criteria sections")
    fi
    
    # Check for introduction
    if ! grep -q "## Introduction" "$requirements_file"; then
        warnings_ref+=("Requirements document missing introduction section")
    fi
    
    # Validate document structure
    local req_count=$(grep -c "### Requirement [0-9]" "$requirements_file" 2>/dev/null || echo "0")
    if [ "$req_count" -eq 0 ]; then
        issues_ref+=("No properly formatted requirements found (should use ### Requirement N: format)")
    fi
}

# Validate design document
validate_design_document() {
    local design_file="$1"
    local -n issues_ref=$2
    local -n warnings_ref=$3
    local -n fixes_ref=$4
    
    # Check for required sections
    local required_sections=("Overview" "Architecture" "Components and Interfaces" "Data Models" "Error Handling" "Testing Strategy")
    
    for section in "${required_sections[@]}"; do
        if ! grep -q "## $section" "$design_file"; then
            warnings_ref+=("Design document missing '$section' section")
        fi
    done
}

# Validate tasks document
validate_tasks_document() {
    local tasks_file="$1"
    local -n issues_ref=$2
    local -n warnings_ref=$3
    local -n fixes_ref=$4
    
    # Check for checkbox format
    if ! grep -q "- \[ \]" "$tasks_file"; then
        issues_ref+=("Tasks document missing checkbox format (- [ ] task)")
    fi
    
    # Check for requirement references
    if ! grep -q "_Requirements:" "$tasks_file"; then
        warnings_ref+=("Tasks document missing requirement references")
    fi
}

# Validate cross-references between documents
validate_cross_references() {
    local feature_name="$1"
    local -n issues_ref=$2
    local -n warnings_ref=$3
    local -n fixes_ref=$4
    
    eval $(get_spec_paths "$feature_name")
    
    # This could be enhanced to check for consistency between documents
    # For now, just check that files exist in proper sequence
    
    if [ -f "$DESIGN" ] && [ ! -f "$REQUIREMENTS" ]; then
        issues_ref+=("Design document exists but requirements document is missing")
    fi
    
    if [ -f "$TASKS" ] && [ ! -f "$DESIGN" ]; then
        issues_ref+=("Tasks document exists but design document is missing")
    fi
}

# Generate JSON output
generate_json_output() {
    local feature_name="$1"
    local issues_count="$2"
    local warnings_count="$3"
    local fixes_count="$4"
    local -n issues_ref=$5
    local -n warnings_ref=$6
    local -n fixes_ref=$7
    
    echo "{"
    echo "  \"feature_name\": \"$feature_name\","
    echo "  \"status\": \"$([ $issues_count -eq 0 ] && echo "passed" || echo "failed")\","
    echo "  \"issues_count\": $issues_count,"
    echo "  \"warnings_count\": $warnings_count,"
    echo "  \"fixes_applied\": $fixes_count,"
    
    # Output issues array
    echo "  \"issues\": ["
    for i in "${!issues_ref[@]}"; do
        echo "    \"${issues_ref[$i]}\"$([ $i -lt $((${#issues_ref[@]} - 1)) ] && echo ",")"
    done
    echo "  ],"
    
    # Output warnings array
    echo "  \"warnings\": ["
    for i in "${!warnings_ref[@]}"; do
        echo "    \"${warnings_ref[$i]}\"$([ $i -lt $((${#warnings_ref[@]} - 1)) ] && echo ",")"
    done
    echo "  ],"
    
    # Output fixes array
    echo "  \"fixes\": ["
    for i in "${!fixes_ref[@]}"; do
        echo "    \"${fixes_ref[$i]}\"$([ $i -lt $((${#fixes_ref[@]} - 1)) ] && echo ",")"
    done
    echo "  ]"
    echo "}"
}

# Generate text output
generate_text_output() {
    local feature_name="$1"
    local issues_count="$2"
    local warnings_count="$3"
    local fixes_count="$4"
    local -n issues_ref=$5
    local -n warnings_ref=$6
    local -n fixes_ref=$7
    
    echo "Specification: $feature_name"
    
    # Show issues
    if [ $issues_count -gt 0 ]; then
        echo ""
        echo "Issues Found ($issues_count):"
        for issue in "${issues_ref[@]}"; do
            echo "  ✗ $issue"
        done
    fi
    
    # Show warnings
    if [ $warnings_count -gt 0 ] && [ "$VERBOSE_MODE" = true ]; then
        echo ""
        echo "Warnings ($warnings_count):"
        for warning in "${warnings_ref[@]}"; do
            echo "  ⚠ $warning"
        done
    fi
    
    # Show fixes applied
    if [ $fixes_count -gt 0 ]; then
        echo ""
        echo "Fixes Applied ($fixes_count):"
        for fix in "${fixes_ref[@]}"; do
            echo "  ✓ $fix"
        done
    fi
    
    # Summary
    echo ""
    if [ $issues_count -eq 0 ]; then
        echo "✓ Validation passed"
    else
        echo "✗ Validation failed with $issues_count issue(s)"
    fi
    
    if [ $warnings_count -gt 0 ] && [ "$VERBOSE_MODE" = false ]; then
        echo "  (Use --verbose to see $warnings_count warning(s))"
    fi
}

# Create basic requirements template (reused from create-spec.sh)
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

## Notes

[Any additional notes, constraints, or considerations]
EOF
}

# Run main function
main "$@"