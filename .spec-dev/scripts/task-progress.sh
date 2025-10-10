#!/bin/bash

# Task Progress Management Script
# Manages task completion status and progress tracking

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Default values
FEATURE_NAME=""
TASK_ID=""
STATUS=""
JSON_OUTPUT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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
            elif [ -z "$TASK_ID" ]; then
                TASK_ID="$1"
            elif [ -z "$STATUS" ]; then
                STATUS="$1"
            fi
            shift
            ;;
    esac
done

show_help() {
    cat << 'EOF'
Task Progress Management

USAGE:
    task-progress.sh <feature-name> <task-id> <status> [options]

STATUS VALUES:
    pending       Task not started
    in-progress   Task currently being worked on
    completed     Task finished and verified

OPTIONS:
    --json        Output in JSON format

EXAMPLES:
    task-progress.sh user-auth T-001 in-progress
    task-progress.sh user-auth T-001 completed
    task-progress.sh user-auth --json
EOF
}

# Initialize progress file if it doesn't exist
init_progress_file() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local meta_dir="$spec_dir/.metadata"
    local progress_file="$meta_dir/progress.json"
    
    mkdir -p "$meta_dir"
    
    if [ ! -f "$progress_file" ]; then
        cat > "$progress_file" << 'EOF'
{
  "total_tasks": 0,
  "completed_tasks": 0,
  "in_progress_tasks": 0,
  "pending_tasks": 0,
  "completion_percentage": 0,
  "tasks": {},
  "last_updated": ""
}
EOF
    fi
}

# Update task status
update_task_status() {
    local feature_name="$1"
    local task_id="$2"
    local status="$3"
    local spec_dir=".specification/specs/$feature_name"
    local meta_dir="$spec_dir/.metadata"
    local progress_file="$meta_dir/progress.json"
    local tasks_file="$spec_dir/tasks.md"
    
    # Initialize if needed
    init_progress_file "$feature_name"
    
    # Update tasks.md file with new status
    if [ -f "$tasks_file" ]; then
        case "$status" in
            pending)
                sed -i "s/- \[.\] \*\*$task_id\*\*/- [ ] **$task_id**/" "$tasks_file" 2>/dev/null || true
                ;;
            in-progress)
                sed -i "s/- \[.\] \*\*$task_id\*\*/- [🚧] **$task_id**/" "$tasks_file" 2>/dev/null || true
                ;;
            completed)
                sed -i "s/- \[.\] \*\*$task_id\*\*/- [x] **$task_id**/" "$tasks_file" 2>/dev/null || true
                ;;
        esac
    fi
    
    # Update progress JSON
    local current_progress=$(cat "$progress_file")
    
    # Update task status in JSON
    current_progress=$(echo "$current_progress" | jq --arg task_id "$task_id" --arg status "$status" '.tasks[$task_id] = $status')
    
    # Recalculate totals
    local total_tasks=$(echo "$current_progress" | jq '.tasks | length')
    local completed_tasks=$(echo "$current_progress" | jq '[.tasks[] | select(. == "completed")] | length')
    local in_progress_tasks=$(echo "$current_progress" | jq '[.tasks[] | select(. == "in-progress")] | length')
    local pending_tasks=$(echo "$current_progress" | jq '[.tasks[] | select(. == "pending")] | length')
    
    # Calculate completion percentage
    local completion_percentage=0
    if [ "$total_tasks" -gt 0 ]; then
        completion_percentage=$(echo "scale=1; $completed_tasks * 100 / $total_tasks" | bc -l 2>/dev/null || echo "0")
    fi
    
    # Update progress data
    current_progress=$(echo "$current_progress" | jq \
        --arg total "$total_tasks" \
        --arg completed "$completed_tasks" \
        --arg in_progress "$in_progress_tasks" \
        --arg pending "$pending_tasks" \
        --arg percentage "$completion_percentage" \
        --arg updated "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '.total_tasks = ($total | tonumber) |
         .completed_tasks = ($completed | tonumber) |
         .in_progress_tasks = ($in_progress | tonumber) |
         .pending_tasks = ($pending | tonumber) |
         .completion_percentage = ($percentage | tonumber) |
         .last_updated = $updated')
    
    # Write updated progress
    echo "$current_progress" > "$progress_file"
    
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$progress_file"
    else
        echo "✓ Updated task $task_id to $status"
        echo "Progress: $completed_tasks/$total_tasks tasks completed (${completion_percentage}%)"
    fi
}

# Get progress status
get_progress() {
    local feature_name="$1"
    local spec_dir=".specification/specs/$feature_name"
    local progress_file="$spec_dir/.metadata/progress.json"
    
    if [ ! -f "$progress_file" ]; then
        init_progress_file "$feature_name"
    fi
    
    if [ "$JSON_OUTPUT" = true ]; then
        cat "$progress_file"
    else
        echo "Task Progress for: $feature_name"
        echo "Total Tasks: $(jq -r '.total_tasks' "$progress_file")"
        echo "Completed: $(jq -r '.completed_tasks' "$progress_file")"
        echo "In Progress: $(jq -r '.in_progress_tasks' "$progress_file")"
        echo "Pending: $(jq -r '.pending_tasks' "$progress_file")"
        echo "Completion: $(jq -r '.completion_percentage' "$progress_file")%"
    fi
}

# Main execution
if [ -z "$FEATURE_NAME" ]; then
    echo "Error: Feature name required"
    show_help
    exit 1
fi

if [ -z "$TASK_ID" ]; then
    # Just get progress
    get_progress "$FEATURE_NAME"
elif [ -z "$STATUS" ]; then
    echo "Error: Task status required"
    show_help
    exit 1
else
    # Update task status
    case "$STATUS" in
        pending|in-progress|completed)
            update_task_status "$FEATURE_NAME" "$TASK_ID" "$STATUS"
            ;;
        *)
            echo "Error: Invalid status. Use pending, in-progress, or completed."
            exit 1
            ;;
    esac
fi