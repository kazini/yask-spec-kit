#!/bin/bash

# Common functions and utilities for spec-driven development scripts
# These functions provide reusable functionality across all automation scripts

# Get the project root directory
get_project_root() {
    # Try to find git root first
    if git rev-parse --show-toplevel 2>/dev/null; then
        return 0
    fi
    
    # Fallback to finding .specification directory
    local current_dir="$(pwd)"
    while [ "$current_dir" != "/" ]; do
        if [ -d "$current_dir/.specification" ]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    
    # If no .specification found, use current directory
    pwd
}

# Get specification directory path
get_spec_dir() {
    local project_root="$1"
    echo "$project_root/.specification"
}

# Get all standard paths for a specification
# Usage: eval $(get_spec_paths "feature-name")
# Sets: PROJECT_ROOT, SPEC_DIR, FEATURE_DIR, REQUIREMENTS, DESIGN, TASKS
get_spec_paths() {
    local feature_name="$1"
    
    if [ -z "$feature_name" ]; then
        echo "Error: Feature name is required" >&2
        return 1
    fi
    
    local project_root=$(get_project_root)
    local spec_dir=$(get_spec_dir "$project_root")
    local feature_dir="$spec_dir/specs/$feature_name"
    
    echo "PROJECT_ROOT='$project_root'"
    echo "SPEC_DIR='$spec_dir'"
    echo "FEATURE_DIR='$feature_dir'"
    echo "REQUIREMENTS='$feature_dir/requirements.md'"
    echo "DESIGN='$feature_dir/design.md'"
    echo "TASKS='$feature_dir/tasks.md'"
}

# Check if a file exists and report status
check_file() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        echo "  ✓ $description"
        return 0
    else
        echo "  ✗ $description"
        return 1
    fi
}

# Check if a directory exists and has content
check_dir() {
    local dir="$1"
    local description="$2"
    
    if [ -d "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null)" ]; then
        echo "  ✓ $description"
        return 0
    else
        echo "  ✗ $description"
        return 1
    fi
}

# Sanitize a feature name for use in file paths
sanitize_feature_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Check if specification structure is initialized
check_spec_structure() {
    local project_root=$(get_project_root)
    local spec_dir=$(get_spec_dir "$project_root")
    
    if [ ! -d "$spec_dir" ]; then
        echo "Error: Specification structure not initialized"
        echo "Run: ./scripts/spec.sh init"
        return 1
    fi
    
    return 0
}

# Get the phase of a specification (requirements, design, tasks, complete)
get_spec_phase() {
    local feature_name="$1"
    eval $(get_spec_paths "$feature_name")
    
    if [ -f "$TASKS" ]; then
        echo "complete"
    elif [ -f "$DESIGN" ]; then
        echo "design"
    elif [ -f "$REQUIREMENTS" ]; then
        echo "requirements"
    else
        echo "empty"
    fi
}

# List all available specifications
list_specifications() {
    local project_root=$(get_project_root)
    local spec_dir=$(get_spec_dir "$project_root")
    
    if [ ! -d "$spec_dir/specs" ]; then
        return 1
    fi
    
    for spec_path in "$spec_dir/specs"/*; do
        if [ -d "$spec_path" ]; then
            basename "$spec_path"
        fi
    done
}

# Validate EARS format in requirements
validate_ears_format() {
    local requirements_file="$1"
    
    if [ ! -f "$requirements_file" ]; then
        return 1
    fi
    
    # Check for basic EARS patterns
    if grep -q "WHEN.*THEN.*SHALL" "$requirements_file" || grep -q "IF.*THEN.*SHALL" "$requirements_file"; then
        return 0
    else
        return 1
    fi
}

# Create a backup of a file
backup_file() {
    local file="$1"
    
    if [ -f "$file" ]; then
        cp "$file" "$file.backup.$(date +%Y%m%d_%H%M%S)"
        echo "  ✓ Backup created for $(basename "$file")"
    fi
}

# Log an action with timestamp
log_action() {
    local action="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $action"
}

# Check if we're in a valid project directory
validate_project_context() {
    local project_root=$(get_project_root)
    
    # Basic validation - could be enhanced based on project needs
    if [ ! -w "$project_root" ]; then
        echo "Error: No write permission in project directory"
        return 1
    fi
    
    return 0
}

# Extract feature name from current context (if available)
detect_current_feature() {
    # This could be enhanced to detect from git branch, current directory, etc.
    local current_dir=$(basename "$(pwd)")
    
    # If we're in a spec directory, extract the feature name
    if [[ "$current_dir" =~ ^[0-9]+-.*$ ]]; then
        echo "$current_dir"
        return 0
    fi
    
    return 1
}

# Print a formatted header
print_header() {
    local title="$1"
    local width=60
    local padding=$(( (width - ${#title}) / 2 ))
    
    echo ""
    printf "%*s" $width | tr ' ' '='
    echo ""
    printf "%*s%s%*s\n" $padding "" "$title" $padding ""
    printf "%*s" $width | tr ' ' '='
    echo ""
}

# Print a formatted section
print_section() {
    local title="$1"
    echo ""
    echo "── $title ──"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get file modification time for comparison
get_file_mtime() {
    local file="$1"
    
    if [ -f "$file" ]; then
        if command_exists stat; then
            # Linux/GNU stat
            stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null
        else
            # Fallback using ls
            ls -l "$file" | awk '{print $6 " " $7 " " $8}'
        fi
    fi
}