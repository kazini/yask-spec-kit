#!/bin/bash

# Health Metrics Management Script
# Manages specification health scores and compliance tracking

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Default values
FEATURE_NAME=""
SCORE=""
ISSUES=""
WARNINGS=""
COMPLIANCE=""
JSON_OUTPUT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --score)
            SCORE="$2"
            shift 2
            ;;
        --issues)
            ISSUES="$2"
            shift 2
            ;;
        --warnings)
            WARNINGS="$2"
            shift 2
            ;;
        --compliance)
            COMPLIANCE="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
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
Health Metrics Management

USAGE:
    health-update.sh <feature-name> [options]

OPTIONS:
    --score <number>         Set health score (0-100)
    --issues <number>        Set number of critical issues
    --warnings <number>      Set number of warnings
    --compliance <text>      Set compliance status text
    --json                   Output in JSON format

EXAMPLES:
    health-update.sh user-auth --score 95 --issues 0 --warnings 2
    health-update.sh user-auth --compliance "EARS: ✓, Cross-refs: ✓, Structure: ✓"
    health-update.sh user-auth --json
EOF
}

# Initialize health file if it doesn't exist
init_health_file() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local meta_dir="$spec_dir/.metadata"
    local health_file="$meta_dir/health-status.json"
    
    mkdir -p "$meta_dir"
    
    if [ ! -f "$health_file" ]; then
        cat > "$health_file" << 'EOF'
{
  "score": 100,
  "issues": 0,
  "warnings": 0,
  "compliance": {
    "ears_format": false,
    "cross_references": false,
    "structure": false,
    "requirements_coverage": false
  },
  "compliance_text": "pending",
  "last_check": "",
  "recommendations": []
}
EOF
    fi
}

# Update health metrics
update_health() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local meta_dir="$spec_dir/.metadata"
    local health_file="$meta_dir/health-status.json"
    
    # Initialize if needed
    init_health_file "$feature_name"
    
    # Read current health data
    local current_health=$(cat "$health_file")
    
    # Update fields if provided
    if [ -n "$SCORE" ]; then
        current_health=$(echo "$current_health" | jq --arg score "$SCORE" '.score = ($score | tonumber)')
    fi
    
    if [ -n "$ISSUES" ]; then
        current_health=$(echo "$current_health" | jq --arg issues "$ISSUES" '.issues = ($issues | tonumber)')
    fi
    
    if [ -n "$WARNINGS" ]; then
        current_health=$(echo "$current_health" | jq --arg warnings "$WARNINGS" '.warnings = ($warnings | tonumber)')
    fi
    
    if [ -n "$COMPLIANCE" ]; then
        current_health=$(echo "$current_health" | jq --arg compliance "$COMPLIANCE" '.compliance_text = $compliance')
        
        # Update individual compliance flags based on text
        if [[ "$COMPLIANCE" == *"EARS: ✓"* ]]; then
            current_health=$(echo "$current_health" | jq '.compliance.ears_format = true')
        fi
        if [[ "$COMPLIANCE" == *"Cross-refs: ✓"* ]]; then
            current_health=$(echo "$current_health" | jq '.compliance.cross_references = true')
        fi
        if [[ "$COMPLIANCE" == *"Structure: ✓"* ]]; then
            current_health=$(echo "$current_health" | jq '.compliance.structure = true')
        fi
        if [[ "$COMPLIANCE" == *"Coverage: ✓"* ]]; then
            current_health=$(echo "$current_health" | jq '.compliance.requirements_coverage = true')
        fi
    fi
    
    # Always update timestamp
    current_health=$(echo "$current_health" | jq --arg updated "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '.last_check = $updated')
    
    # Generate recommendations based on health data
    local recommendations=()
    local score=$(echo "$current_health" | jq -r '.score')
    local issues=$(echo "$current_health" | jq -r '.issues')
    local warnings=$(echo "$current_health" | jq -r '.warnings')
    
    if [ "$issues" -gt 0 ]; then
        recommendations+=("Address $issues critical issue(s) before proceeding")
    fi
    
    if [ "$warnings" -gt 0 ]; then
        recommendations+=("Review $warnings warning(s) for potential improvements")
    fi
    
    if [ "$score" -lt 80 ]; then
        recommendations+=("Health score below 80 - run validation and fix issues")
    fi
    
    # Update recommendations
    local rec_json=$(printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s .)
    current_health=$(echo "$current_health" | jq --argjson recs "$rec_json" '.recommendations = $recs')
    
    # Write updated health data
    echo "$current_health" > "$health_file"
    
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$health_file"
    else
        echo "✓ Updated health metrics for specification: $feature_name"
        echo "Health Score: $(echo "$current_health" | jq -r '.score')"
        echo "Issues: $(echo "$current_health" | jq -r '.issues')"
        echo "Warnings: $(echo "$current_health" | jq -r '.warnings')"
    fi
}

# Get health status
get_health() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local health_file="$spec_dir/.metadata/health-status.json"
    
    if [ ! -f "$health_file" ]; then
        init_health_file "$feature_name"
    fi
    
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$health_file"
    else
        echo "Health Status for: $feature_name"
        echo "Score: $(jq -r '.score' "$health_file")"
        echo "Issues: $(jq -r '.issues' "$health_file")"
        echo "Warnings: $(jq -r '.warnings' "$health_file")"
        echo "Compliance: $(jq -r '.compliance_text' "$health_file")"
        echo "Last Check: $(jq -r '.last_check' "$health_file")"
        
        local recs=$(jq -r '.recommendations[]' "$health_file" 2>/dev/null)
        if [ -n "$recs" ]; then
            echo "Recommendations:"
            echo "$recs" | sed 's/^/  - /'
        fi
    fi
}

# Main execution
if [ -z "$FEATURE_NAME" ]; then
    echo "Error: Feature name required"
    show_help
    exit 1
fi

if [ -n "$SCORE" ] || [ -n "$ISSUES" ] || [ -n "$WARNINGS" ] || [ -n "$COMPLIANCE" ]; then
    # Update health metrics
    update_health "$FEATURE_NAME"
else
    # Just get health status
    get_health "$FEATURE_NAME"
fi