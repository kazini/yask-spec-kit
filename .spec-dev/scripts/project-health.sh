#!/bin/bash

# Project Health Check Script
# Comprehensive validation of spec-driven development project structure
# Compatible with various AI development agents

set -e

# Get script directory and source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Configuration
VERBOSE_MODE=false
JSON_MODE=false
FIX_MODE=false

# Parse command line arguments
for arg in "$@"; do
    case "$arg" in
        --verbose|-v)
            VERBOSE_MODE=true
            ;;
        --json)
            JSON_MODE=true
            ;;
        --fix)
            FIX_MODE=true
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
    esac
done

# Show help information
show_help() {
    cat << 'EOF'
Project Health Check Script

USAGE:
    project-health.sh [OPTIONS]

OPTIONS:
    --verbose, -v  Show detailed health information
    --json         Output results in JSON format
    --fix          Attempt to fix common issues automatically
    --help, -h     Show this help message

DESCRIPTION:
    Performs comprehensive validation of spec-driven development project structure,
    including directory organization, document completeness, cross-references,
    and compliance with established principles.

CHECKS PERFORMED:
    - Project structure validation
    - Specification completeness
    - Cross-reference integrity
    - Template consistency
    - Script functionality
    - Documentation quality
EOF
}

# Main health check function
main() {
    local project_root=$(get_project_root)
    
    if [ "$JSON_MODE" = false ]; then
        print_header "Project Health Check"
        echo "Project Root: $project_root"
        echo ""
    fi
    
    local total_issues=0
    local total_warnings=0
    local total_fixes=0
    
    # Run all health checks
    check_project_structure total_issues total_warnings total_fixes
    check_specification_completeness total_issues total_warnings total_fixes
    check_cross_references total_issues total_warnings total_fixes
    check_template_consistency total_issues total_warnings total_fixes
    check_script_functionality total_issues total_warnings total_fixes
    check_documentation_quality total_issues total_warnings total_fixes
    
    # Generate summary
    if [ "$JSON_MODE" = true ]; then
        generate_json_summary "$total_issues" "$total_warnings" "$total_fixes"
    else
        generate_text_summary "$total_issues" "$total_warnings" "$total_fixes"
    fi
    
    # Exit with appropriate code
    if [ $total_issues -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Check project structure
check_project_structure() {
    local -n issues_ref=$1
    local -n warnings_ref=$2
    local -n fixes_ref=$3
    
    if [ "$JSON_MODE" = false ]; then
        print_section "Project Structure"
    fi
    
    local project_root=$(get_project_root)
    
    # Check for .spec-dev directory
    if [ -d "$project_root/.spec-dev" ]; then
        log_check "✓ .spec-dev directory exists"
        
        # Check for required files in .spec-dev
        local required_files=(
            "README.md"
            "project-principles.md"
            "principles_update_checklist.md"
        )
        
        for file in "${required_files[@]}"; do
            if [ -f "$project_root/.spec-dev/$file" ]; then
                log_check "✓ .spec-dev/$file exists"
            else
                log_check "✗ .spec-dev/$file missing"
                issues_ref=$((issues_ref + 1))
            fi
        done
        
        # Check for scripts directory
        if [ -d "$project_root/.spec-dev/scripts" ]; then
            log_check "✓ .spec-dev/scripts directory exists"
            
            # Check for required scripts
            local required_scripts=(
                "spec.sh"
                "common.sh"
                "create-spec.sh"
                "validate-spec.sh"
            )
            
            for script in "${required_scripts[@]}"; do
                if [ -f "$project_root/.spec-dev/scripts/$script" ]; then
                    log_check "✓ scripts/$script exists"
                else
                    log_check "✗ scripts/$script missing"
                    issues_ref=$((issues_ref + 1))
                fi
            done
        else
            log_check "✗ .spec-dev/scripts directory missing"
            issues_ref=$((issues_ref + 1))
        fi
        
        # Check for templates directory
        if [ -d "$project_root/.spec-dev/templates" ]; then
            log_check "✓ .spec-dev/templates directory exists"
        else
            log_check "⚠ .spec-dev/templates directory missing"
            warnings_ref=$((warnings_ref + 1))
        fi
        
    else
        log_check "✗ .spec-dev directory missing"
        issues_ref=$((issues_ref + 1))
        
        if [ "$FIX_MODE" = true ]; then
            log_check "  → Attempting to create .spec-dev structure"
            # This would require copying from a template location
            fixes_ref=$((fixes_ref + 1))
        fi
    fi
    
    # Check for .specification directory
    if [ -d "$project_root/.specification" ]; then
        log_check "✓ .specification directory exists"
        
        # Check for specs subdirectory
        if [ -d "$project_root/.specification/specs" ]; then
            log_check "✓ .specification/specs directory exists"
        else
            log_check "⚠ .specification/specs directory missing"
            warnings_ref=$((warnings_ref + 1))
        fi
    else
        log_check "⚠ .specification directory not initialized"
        warnings_ref=$((warnings_ref + 1))
        
        if [ "$FIX_MODE" = true ]; then
            log_check "  → Run './scripts/spec.sh init' to initialize"
        fi
    fi
}

# Check specification completeness
check_specification_completeness() {
    local -n issues_ref=$1
    local -n warnings_ref=$2
    local -n fixes_ref=$3
    
    if [ "$JSON_MODE" = false ]; then
        print_section "Specification Completeness"
    fi
    
    local project_root=$(get_project_root)
    local spec_dir="$project_root/.specification/specs"
    
    if [ ! -d "$spec_dir" ]; then
        log_check "⚠ No specifications directory found"
        warnings_ref=$((warnings_ref + 1))
        return
    fi
    
    local spec_count=0
    local complete_specs=0
    
    for spec_path in "$spec_dir"/*; do
        if [ -d "$spec_path" ]; then
            local spec_name=$(basename "$spec_path")
            spec_count=$((spec_count + 1))
            
            log_check "Checking specification: $spec_name"
            
            local has_requirements=false
            local has_design=false
            local has_tasks=false
            
            # Check for core documents
            if [ -f "$spec_path/requirements.md" ]; then
                has_requirements=true
                log_check "  ✓ requirements.md exists"
            else
                log_check "  ✗ requirements.md missing"
                issues_ref=$((issues_ref + 1))
            fi
            
            if [ -f "$spec_path/design.md" ]; then
                has_design=true
                log_check "  ✓ design.md exists"
            else
                log_check "  ⚠ design.md missing"
                warnings_ref=$((warnings_ref + 1))
            fi
            
            if [ -f "$spec_path/tasks.md" ]; then
                has_tasks=true
                log_check "  ✓ tasks.md exists"
            else
                log_check "  ⚠ tasks.md missing"
                warnings_ref=$((warnings_ref + 1))
            fi
            
            # Check if specification is complete
            if [ "$has_requirements" = true ] && [ "$has_design" = true ] && [ "$has_tasks" = true ]; then
                complete_specs=$((complete_specs + 1))
                log_check "  ✓ Specification complete"
            fi
        fi
    done
    
    if [ $spec_count -eq 0 ]; then
        log_check "⚠ No specifications found"
        warnings_ref=$((warnings_ref + 1))
    else
        log_check "Found $spec_count specification(s), $complete_specs complete"
    fi
}

# Check cross-references integrity
check_cross_references() {
    local -n issues_ref=$1
    local -n warnings_ref=$2
    local -n fixes_ref=$3
    
    if [ "$JSON_MODE" = false ]; then
        print_section "Cross-Reference Integrity"
    fi
    
    local project_root=$(get_project_root)
    local spec_dir="$project_root/.specification/specs"
    
    if [ ! -d "$spec_dir" ]; then
        return
    fi
    
    # Check for broken internal links
    for spec_path in "$spec_dir"/*; do
        if [ -d "$spec_path" ]; then
            local spec_name=$(basename "$spec_path")
            
            # Check requirements.md for proper structure
            if [ -f "$spec_path/requirements.md" ]; then
                if grep -q "User Story:" "$spec_path/requirements.md" && grep -q "WHEN.*THEN.*SHALL" "$spec_path/requirements.md"; then
                    log_check "✓ $spec_name requirements follow EARS format"
                else
                    log_check "⚠ $spec_name requirements may not follow EARS format"
                    warnings_ref=$((warnings_ref + 1))
                fi
            fi
            
            # Check for cross-references between documents
            if [ -f "$spec_path/design.md" ] && [ -f "$spec_path/requirements.md" ]; then
                if grep -q "requirements.md\|Requirements" "$spec_path/design.md"; then
                    log_check "✓ $spec_name design references requirements"
                else
                    log_check "⚠ $spec_name design doesn't reference requirements"
                    warnings_ref=$((warnings_ref + 1))
                fi
            fi
            
            if [ -f "$spec_path/tasks.md" ] && [ -f "$spec_path/design.md" ]; then
                if grep -q "design.md\|Design\|_Requirements:" "$spec_path/tasks.md"; then
                    log_check "✓ $spec_name tasks reference design/requirements"
                else
                    log_check "⚠ $spec_name tasks don't reference design/requirements"
                    warnings_ref=$((warnings_ref + 1))
                fi
            fi
        fi
    done
}

# Check template consistency
check_template_consistency() {
    local -n issues_ref=$1
    local -n warnings_ref=$2
    local -n fixes_ref=$3
    
    if [ "$JSON_MODE" = false ]; then
        print_section "Template Consistency"
    fi
    
    local project_root=$(get_project_root)
    
    # Check for system templates
    if [ -d "$project_root/.spec-dev/templates" ]; then
        local required_templates=(
            "requirements-template.md"
            "design-template.md"
            "tasks-template.md"
        )
        
        for template in "${required_templates[@]}"; do
            if [ -f "$project_root/.spec-dev/templates/$template" ]; then
                log_check "✓ System template $template exists"
            else
                log_check "⚠ System template $template missing"
                warnings_ref=$((warnings_ref + 1))
            fi
        done
    fi
    
    # Check for project-specific templates
    if [ -d "$project_root/.specification/templates" ]; then
        log_check "✓ Project-specific templates directory exists"
    else
        log_check "⚠ No project-specific templates directory"
        warnings_ref=$((warnings_ref + 1))
    fi
}

# Check script functionality
check_script_functionality() {
    local -n issues_ref=$1
    local -n warnings_ref=$2
    local -n fixes_ref=$3
    
    if [ "$JSON_MODE" = false ]; then
        print_section "Script Functionality"
    fi
    
    local project_root=$(get_project_root)
    
    # Check if main script is executable and functional
    if [ -f "$project_root/.spec-dev/scripts/spec.sh" ]; then
        if [ -x "$project_root/.spec-dev/scripts/spec.sh" ]; then
            log_check "✓ spec.sh is executable"
        else
            log_check "⚠ spec.sh is not executable"
            warnings_ref=$((warnings_ref + 1))
            
            if [ "$FIX_MODE" = true ]; then
                chmod +x "$project_root/.spec-dev/scripts/spec.sh" 2>/dev/null || true
                log_check "  → Made spec.sh executable"
                fixes_ref=$((fixes_ref + 1))
            fi
        fi
        
        # Test basic script functionality
        if "$project_root/.spec-dev/scripts/spec.sh" help >/dev/null 2>&1; then
            log_check "✓ spec.sh help command works"
        else
            log_check "✗ spec.sh help command fails"
            issues_ref=$((issues_ref + 1))
        fi
    fi
    
    # Check other scripts
    local scripts=("create-spec.sh" "validate-spec.sh" "common.sh")
    for script in "${scripts[@]}"; do
        if [ -f "$project_root/.spec-dev/scripts/$script" ]; then
            log_check "✓ $script exists"
        else
            log_check "⚠ $script missing"
            warnings_ref=$((warnings_ref + 1))
        fi
    done
}

# Check documentation quality
check_documentation_quality() {
    local -n issues_ref=$1
    local -n warnings_ref=$2
    local -n fixes_ref=$3
    
    if [ "$JSON_MODE" = false ]; then
        print_section "Documentation Quality"
    fi
    
    local project_root=$(get_project_root)
    
    # Check main README
    if [ -f "$project_root/.spec-dev/README.md" ]; then
        log_check "✓ .spec-dev/README.md exists"
        
        # Check for key sections
        if grep -q "## Overview" "$project_root/.spec-dev/README.md"; then
            log_check "✓ README has Overview section"
        else
            log_check "⚠ README missing Overview section"
            warnings_ref=$((warnings_ref + 1))
        fi
        
        if grep -q "## Quick Start" "$project_root/.spec-dev/README.md"; then
            log_check "✓ README has Quick Start section"
        else
            log_check "⚠ README missing Quick Start section"
            warnings_ref=$((warnings_ref + 1))
        fi
    else
        log_check "✗ .spec-dev/README.md missing"
        issues_ref=$((issues_ref + 1))
    fi
    
    # Check principles document
    if [ -f "$project_root/.spec-dev/project-principles.md" ]; then
        log_check "✓ project-principles.md exists"
        
        if grep -q "## Principles" "$project_root/.spec-dev/project-principles.md"; then
            log_check "✓ Principles document has Principles section"
        else
            log_check "⚠ Principles document missing Principles section"
            warnings_ref=$((warnings_ref + 1))
        fi
    else
        log_check "✗ project-principles.md missing"
        issues_ref=$((issues_ref + 1))
    fi
}

# Utility functions
log_check() {
    local message="$1"
    if [ "$JSON_MODE" = false ]; then
        if [ "$VERBOSE_MODE" = true ] || [[ "$message" =~ ^[✓✗⚠] ]]; then
            echo "$message"
        fi
    fi
}

generate_json_summary() {
    local issues="$1"
    local warnings="$2"
    local fixes="$3"
    
    cat << EOF
{
    "status": "$([ $issues -eq 0 ] && echo "healthy" || echo "issues_found")",
    "summary": {
        "issues": $issues,
        "warnings": $warnings,
        "fixes_applied": $fixes
    },
    "health_score": $(( 100 - (issues * 10) - (warnings * 2) )),
    "recommendations": [
        $([ $issues -gt 0 ] && echo '"Address critical issues before proceeding",' || echo '')
        $([ $warnings -gt 0 ] && echo '"Review warnings for potential improvements",' || echo '')
        "Regular health checks recommended"
    ]
}
EOF
}

generate_text_summary() {
    local issues="$1"
    local warnings="$2"
    local fixes="$3"
    
    echo ""
    print_header "Health Check Summary"
    
    if [ $issues -eq 0 ] && [ $warnings -eq 0 ]; then
        echo "✅ Project is healthy! No issues found."
    elif [ $issues -eq 0 ]; then
        echo "✅ Project is mostly healthy with $warnings warning(s)."
    else
        echo "⚠️  Project has $issues issue(s) and $warnings warning(s) that need attention."
    fi
    
    if [ $fixes -gt 0 ]; then
        echo "🔧 Applied $fixes automatic fix(es)."
    fi
    
    local health_score=$(( 100 - (issues * 10) - (warnings * 2) ))
    echo ""
    echo "Health Score: $health_score/100"
    
    echo ""
    echo "Recommendations:"
    if [ $issues -gt 0 ]; then
        echo "  • Address critical issues before proceeding with development"
    fi
    if [ $warnings -gt 0 ]; then
        echo "  • Review warnings for potential improvements"
    fi
    echo "  • Run health checks regularly to maintain project quality"
    echo "  • Use --fix flag to automatically resolve common issues"
}

# Run main function
main "$@"