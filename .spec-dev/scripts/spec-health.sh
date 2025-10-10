#!/bin/bash

# Specification Health Check Script
# Comprehensive health assessment with automated validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Default values
FEATURE_NAME=""
JSON_OUTPUT=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$FEATURE_NAME" ]; then
                FEATURE_NAME="$1"
            fi
            shift
            ;;
    esac
done

show_help() {
    cat << 'EOF'
Specification Health Check

USAGE:
    spec-health.sh <feature-name> [options]

OPTIONS:
    --json        Output in JSON format
    --verbose     Show detailed health information
    --help        Show this help message

EXAMPLES:
    spec-health.sh user-auth
    spec-health.sh user-auth --json
    spec-health.sh user-auth --verbose
EOF
}

# Check EARS format compliance
check_ears_compliance() {
    local spec_dir="$1"
    local requirements_file="$spec_dir/requirements.md"
    
    if [ ! -f "$requirements_file" ]; then
        echo "false"
        return
    fi
    
    # Check for EARS format patterns
    if grep -q "WHEN.*THEN.*SHALL" "$requirements_file" && grep -q "User Story" "$requirements_file"; then
        echo "true"
    else
        echo "false"
    fi
}

# Check cross-reference integrity
check_cross_references() {
    local spec_dir="$1"
    local requirements_file="$spec_dir/requirements.md"
    local design_file="$spec_dir/design.md"
    local tasks_file="$spec_dir/tasks.md"
    
    local has_refs=false
    
    # Check if design references requirements
    if [ -f "$design_file" ] && [ -f "$requirements_file" ]; then
        if grep -q "US-\|requirements\|Requirements" "$design_file"; then
            has_refs=true
        fi
    fi
    
    # Check if tasks reference requirements
    if [ -f "$tasks_file" ] && [ -f "$requirements_file" ]; then
        if grep -q "Requirements:\|US-" "$tasks_file"; then
            has_refs=true
        fi
    fi
    
    echo "$has_refs"
}

# Check document structure
check_structure() {
    local spec_dir="$1"
    local requirements_file="$spec_dir/requirements.md"
    local design_file="$spec_dir/design.md"
    local tasks_file="$spec_dir/tasks.md"
    
    local structure_score=0
    
    # Check requirements structure
    if [ -f "$requirements_file" ]; then
        if grep -q "## Introduction\|## Requirements" "$requirements_file"; then
            structure_score=$((structure_score + 1))
        fi
    fi
    
    # Check design structure
    if [ -f "$design_file" ]; then
        if grep -q "## Overview\|## Architecture\|## Components" "$design_file"; then
            structure_score=$((structure_score + 1))
        fi
    fi
    
    # Check tasks structure
    if [ -f "$tasks_file" ]; then
        if grep -q "## Tasks\|## Development Status" "$tasks_file"; then
            structure_score=$((structure_score + 1))
        fi
    fi
    
    # Return true if at least 2 out of 3 have good structure
    if [ $structure_score -ge 2 ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Calculate health score
calculate_health_score() {
    local issues="$1"
    local warnings="$2"
    local ears_compliance="$3"
    local cross_refs="$4"
    local structure="$5"
    
    local score=100
    
    # Deduct for issues and warnings
    score=$((score - (issues * 10)))
    score=$((score - (warnings * 2)))
    
    # Deduct for compliance failures
    if [ "$ears_compliance" = "false" ]; then
        score=$((score - 15))
    fi
    
    if [ "$cross_refs" = "false" ]; then
        score=$((score - 10))
    fi
    
    if [ "$structure" = "false" ]; then
        score=$((score - 10))
    fi
    
    # Ensure score doesn't go below 0
    if [ $score -lt 0 ]; then
        score=0
    fi
    
    echo "$score"
}

# Perform comprehensive health check
perform_health_check() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    
    if [ ! -d "$spec_dir" ]; then
        echo "Error: Specification directory not found: $spec_dir"
        exit 1
    fi
    
    # Initialize counters
    local issues=0
    local warnings=0
    local recommendations=()
    
    # Check file existence
    local requirements_file="$spec_dir/requirements.md"
    local design_file="$spec_dir/design.md"
    local tasks_file="$spec_dir/tasks.md"
    
    if [ ! -f "$requirements_file" ]; then
        issues=$((issues + 1))
        recommendations+=("Create requirements.md file")
    fi
    
    if [ ! -f "$design_file" ]; then
        warnings=$((warnings + 1))
        recommendations+=("Create design.md file")
    fi
    
    if [ ! -f "$tasks_file" ]; then
        warnings=$((warnings + 1))
        recommendations+=("Create tasks.md file")
    fi
    
    # Check compliance
    local ears_compliance=$(check_ears_compliance "$spec_dir")
    local cross_refs=$(check_cross_references "$spec_dir")
    local structure=$(check_structure "$spec_dir")
    
    if [ "$ears_compliance" = "false" ]; then
        issues=$((issues + 1))
        recommendations+=("Fix EARS format in requirements")
    fi
    
    if [ "$cross_refs" = "false" ]; then
        warnings=$((warnings + 1))
        recommendations+=("Add cross-references between documents")
    fi
    
    if [ "$structure" = "false" ]; then
        warnings=$((warnings + 1))
        recommendations+=("Improve document structure")
    fi
    
    # Calculate health score
    local health_score=$(calculate_health_score "$issues" "$warnings" "$ears_compliance" "$cross_refs" "$structure")
    
    # Build compliance text
    local compliance_parts=()
    if [ "$ears_compliance" = "true" ]; then
        compliance_parts+=("EARS: ✓")
    else
        compliance_parts+=("EARS: ✗")
    fi
    
    if [ "$cross_refs" = "true" ]; then
        compliance_parts+=("Cross-refs: ✓")
    else
        compliance_parts+=("Cross-refs: ✗")
    fi
    
    if [ "$structure" = "true" ]; then
        compliance_parts+=("Structure: ✓")
    else
        compliance_parts+=("Structure: ✗")
    fi
    
    local compliance_text=$(IFS=', '; echo "${compliance_parts[*]}")
    
    # Update health metrics
    "$SCRIPT_DIR/health-update.sh" "$feature_name" \
        --score "$health_score" \
        --issues "$issues" \
        --warnings "$warnings" \
        --compliance "$compliance_text" >/dev/null
    
    # Output results
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$spec_dir/.metadata/health-status.json"
    else
        echo "Health Check Results for: $feature_name"
        echo "Health Score: $health_score/100"
        echo "Issues: $issues"
        echo "Warnings: $warnings"
        echo "Compliance: $compliance_text"
        
        if [ ${#recommendations[@]} -gt 0 ]; then
            echo "Recommendations:"
            printf '%s\n' "${recommendations[@]}" | sed 's/^/  - /'
        fi
        
        if [ "$VERBOSE" = true ]; then
            echo ""
            echo "Detailed Analysis:"
            echo "  EARS Format: $ears_compliance"
            echo "  Cross References: $cross_refs"
            echo "  Document Structure: $structure"
        fi
    fi
}

# Main execution
if [ -z "$FEATURE_NAME" ]; then
    echo "Error: Feature name required"
    show_help
    exit 1
fi

perform_health_check "$FEATURE_NAME"