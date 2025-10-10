#!/bin/bash
# Install spec-driven development for Gemini CLI

set -e  # Exit on any error

GEMINI_COMMANDS_DIR="$HOME/.gemini/commands"
SPEC_DIR="$GEMINI_COMMANDS_DIR/spec"

echo "Installing Spec-Driven Development for Gemini CLI..."

# Create spec command directory
mkdir -p "$SPEC_DIR"

# Copy system files (from .spec-dev directory)
cp -r ./.spec-dev "$SPEC_DIR/"
cp ./spec-dev-agent.md "$SPEC_DIR/"

# Create spec.toml command file
cat > "$GEMINI_COMMANDS_DIR/spec.toml" << 'EOF'
prompt = "!{bash spec-dev-setup.sh}"
EOF

# Create setup script
cat > "$SPEC_DIR/spec-dev-setup.sh" << 'EOF'
#!/bin/bash
# Spec-driven development setup for current workspace

set -e

WORKSPACE_GEMINI_DIR="./.gemini"
SPEC_SYS_DIR="$WORKSPACE_GEMINI_DIR/.spec-sys"
COMMANDS_SPEC_DIR="$HOME/.gemini/commands/spec"

echo "Setting up spec-driven development in current workspace..."

# Check if .spec-dev already exists in current folder
if [ ! -d "./.spec-dev" ]; then
    echo "Copying .spec-dev system files..."
    mkdir -p "$SPEC_SYS_DIR"
    cp -r "$COMMANDS_SPEC_DIR/.spec-dev" "$SPEC_SYS_DIR/"
else
    echo ".spec-dev already exists in current folder, skipping system copy."
fi

# Copy prompt file as .spec-dev (no extension)
echo "Installing spec-dev prompt..."
cp "$COMMANDS_SPEC_DIR/spec-dev-agent.md" "./.spec-dev"

# Handle workspace .gemini directory
mkdir -p "$WORKSPACE_GEMINI_DIR"

# Backup existing settings if they exist
if [ -f "$WORKSPACE_GEMINI_DIR/settings.json" ]; then
    echo "Backing up existing settings.json..."
    mv "$WORKSPACE_GEMINI_DIR/settings.json" "$WORKSPACE_GEMINI_DIR/settings_old.json"
fi

# Create new settings.json
echo "Creating Gemini workspace settings..."
cat > "$WORKSPACE_GEMINI_DIR/settings.json" << 'SETTINGS_EOF'
{
  "contextFileName": ".spec-dev",
  "includeDirectories": [".gemini/.spec-sys/"],
  "fileFiltering": {
    "respectGitIgnore": false
  }
}
SETTINGS_EOF

echo "✅ Spec-driven development setup complete!"
echo "📁 System files: .gemini/.spec-sys/.spec-dev/"
echo "🤖 Agent prompt: .spec-dev (loaded automatically)"
echo "⚙️  Workspace settings: .gemini/settings.json"
echo ""
echo "You can now use spec-driven development in this workspace."
EOF

# Make setup script executable
chmod +x "$SPEC_DIR/spec-dev-setup.sh"

# Verify the files were created successfully
echo "Verifying installation..."
if [ -f "$SPEC_DIR/spec-dev-agent.md" ] && [ -d "$SPEC_DIR/.spec-dev" ] && [ -f "$SPEC_DIR/spec-dev-setup.sh" ]; then
    echo "✅ Files successfully copied and created."
    
    echo ""
    echo "✅ Gemini CLI integration installed successfully!"
    echo ""
    echo "Usage:"
    echo "  Manual setup: Copy files to project and rename prompt to .gemini"
    echo "  Automated setup: Run '/spec' command in any project directory"
    echo ""
    echo "The '/spec' command will:"
    echo "  - Copy system files to workspace .gemini/.spec-sys/"
    echo "  - Install agent prompt as .spec-dev"
    echo "  - Configure Gemini workspace settings"
    echo ""
    echo "⚠️  IMPORTANT: After installation, reload Gemini context:"
    echo "   Run '/memory refresh' or restart Gemini to activate the new command."
    echo ""
    
    # Confirm deletion with user
    read -p "Delete original installer and source files? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning up original files..."
        
        # Delete original files
        rm -f ./spec-dev-agent.md
        rm -rf ./.spec-dev
        rm -f ./install-gemini.sh
        
        echo "✅ Original files cleaned up."
    else
        echo "Original files preserved."
    fi
else
    echo "❌ Installation verification failed. Files may not have been copied correctly."
    exit 1
fi