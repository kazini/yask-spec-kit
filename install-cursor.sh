#!/bin/bash
# Install spec-driven development for Cursor IDE

set -e  # Exit on any error

CURSOR_RULES_DIR="./.cursor/rules"

echo "Installing Spec-Driven Development for Cursor IDE..."

# Check if .cursor/rules folder exists, create it if it doesn't
if [ ! -d "$CURSOR_RULES_DIR" ]; then
    echo "Creating .cursor/rules directory..."
    mkdir -p "$CURSOR_RULES_DIR"
else
    echo ".cursor/rules directory already exists."
fi

# Copy .spec-dev folder to .cursor/rules
echo "Copying .spec-dev system files..."
cp -r ./.spec-dev "$CURSOR_RULES_DIR/"

# Create the modified agent file with frontmatter
echo "Creating spec-dev-agent.mdc with Cursor frontmatter..."
cat > "$CURSOR_RULES_DIR/spec-dev-agent.mdc" << 'AGENT_EOF'
---
description: "Spec-Driven Development Agent"
alwaysApply: true
globs:
- ".spec-dev/**/*"
---

AGENT_EOF

# Append the original agent content
cat ./spec-dev-agent.md >> "$CURSOR_RULES_DIR/spec-dev-agent.mdc"

# Verify the files were created successfully
echo "Verifying installation..."
if [ -f "$CURSOR_RULES_DIR/spec-dev-agent.mdc" ] && [ -d "$CURSOR_RULES_DIR/.spec-dev" ]; then
    echo "✅ Files successfully copied and created."
    
    # Confirm deletion with user
    echo ""
    echo "Installation complete! Files have been copied to .cursor/rules/"
    echo "📁 System files: .cursor/rules/.spec-dev/"
    echo "🤖 Agent rules: .cursor/rules/spec-dev-agent.mdc"
    echo ""
    read -p "Delete original installer and source files? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning up original files..."
        
        # Delete original files
        rm -f ./spec-dev-agent.md
        rm -rf ./.spec-dev
        rm -f ./install-cursor.sh
        
        echo "✅ Original files cleaned up."
    else
        echo "Original files preserved."
    fi
else
    echo "❌ Installation verification failed. Files may not have been copied correctly."
    exit 1
fi

echo ""
echo "✅ Cursor IDE integration installed successfully!"
echo ""
echo "Usage:"
echo "  - Cursor will automatically load the spec-dev agent rules"
echo "  - Agent has access to all .spec-dev system files"
echo "  - Start using spec-driven development in your project"
echo ""
echo "The agent will:"
echo "  - Guide you through Requirements → Design → Tasks → Implementation"
echo "  - Auto-discover system files in .cursor/rules/.spec-dev/"
echo "  - Apply spec-driven development patterns automatically"