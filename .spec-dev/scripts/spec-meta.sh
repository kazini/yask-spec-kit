#!/bin/bash

# Specification Metadata Management Script
# Manages core specification metadata separately from content files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Default values
FEATURE_NAME=""
ACTION=""
STATUS=""
PHASE=""
VERSION=""
AUTHOR=""
JSON_OUTPUT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        update|get|init)
            ACTION="$1"
            shift
            ;;
        --status)
            STATUS="$2"
            shift 2
            ;;
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --author)
            AUTHOR="$2"
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
Specification Metadata Management

USAGE:
    spec-meta.sh <action> <feature-name> [options]

ACTIONS:
    init <feature-name>           Initialize metadata for new specification
    update <feature-name>         Update specification metadata
    get <feature-name>           Get current metadata

OPTIONS:
    --status <status>            Set status (draft|approved|implemented)
    --phase <phase>              Set current phase (requirements|design|tasks|implementation)
    --version <version>          Set version number
    --author <author>            Set author name
    --json                       Output in JSON format

EXAMPLES:
    spec-meta.sh init user-auth --author "Dev Team"
    spec-meta.sh update user-auth --status approved --phase design
    spec-meta.sh get user-auth --json
EOF
}

# Initialize metadata for new specification
init_metadata() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local meta_dir="$spec_dir/.metadata"
    
    # Create metadata directory
    mkdir -p "$meta_dir"
    
    # Create spec metadata file
    cat > "$meta_dir/spec-metadata.json" << EOF
{
  "id": "spec-$feature_name",
  "name": "$feature_name",
  "status": "draft",
  "phase": "requirements",
  "version": "1.0.0",
  "author": "${AUTHOR:-"Unknown"}",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "dependencies": []
}
EOF

    if [ "$JSON_OUTPUT" = true ]; then
        cat "$meta_dir/spec-metadata.json"
    else
        echo "✓ Initialized metadata for specification: $feature_name"
    fi
}

# Update specification metadata
update_metadata() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local meta_dir="$spec_dir/.metadata"
    local meta_file="$meta_dir/spec-metadata.json"
    
    if [ ! -f "$meta_file" ]; then
        echo "Error: Metadata file not found. Run 'init' first."
        exit 1
    fi
    
    # Read current metadata
    local current_meta=$(cat "$meta_file")
    
    # Update fields if provided
    if [ -n "$STATUS" ]; then
        current_meta=$(echo "$current_meta" | jq --arg status "$STATUS" '.status = $status')
    fi
    
    if [ -n "$PHASE" ]; then
        current_meta=$(echo "$current_meta" | jq --arg phase "$PHASE" '.phase = $phase')
    fi
    
    if [ -n "$VERSION" ]; then
        current_meta=$(echo "$current_meta" | jq --arg version "$VERSION" '.version = $version')
    fi
    
    if [ -n "$AUTHOR" ]; then
        current_meta=$(echo "$current_meta" | jq --arg author "$AUTHOR" '.author = $author')
    fi
    
    # Always update timestamp
    current_meta=$(echo "$current_meta" | jq --arg updated "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '.updated = $updated')
    
    # Write updated metadata
    echo "$current_meta" > "$meta_file"
    
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$meta_file"
    else
        echo "✓ Updated metadata for specification: $feature_name"
    fi
}

# Get specification metadata
get_metadata() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local meta_file="$spec_dir/.metadata/spec-metadata.json"
    
    if [ ! -f "$meta_file" ]; then
        echo "Error: Metadata file not found for specification: $feature_name"
        exit 1
    fi
    
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$meta_file"
    else
        echo "Specification Metadata: $feature_name"
        echo "Status: $(jq -r '.status' "$meta_file")"
        echo "Phase: $(jq -r '.phase' "$meta_file")"
        echo "Version: $(jq -r '.version' "$meta_file")"
        echo "Author: $(jq -r '.author' "$meta_file")"
        echo "Updated: $(jq -r '.updated' "$meta_file")"
    fi
}

# Main execution
case "$ACTION" in
    init)
        if [ -z "$FEATURE_NAME" ]; then
            echo "Error: Feature name required for init"
            show_help
            exit 1
        fi
        init_metadata "$FEATURE_NAME"
        ;;
    update)
        if [ -z "$FEATURE_NAME" ]; then
            echo "Error: Feature name required for update"
            show_help
            exit 1
        fi
        update_metadata "$FEATURE_NAME"
        ;;
    get)
        if [ -z "$FEATURE_NAME" ]; then
            echo "Error: Feature name required for get"
            show_help
            exit 1
        fi
        get_metadata "$FEATURE_NAME"
        ;;
    *)
        echo "Error: Invalid action. Use init, update, or get."
        show_help
        exit 1
        ;;
esac