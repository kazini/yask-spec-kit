#!/bin/bash
# Install spec-driven development for Gemini CLI

set -e  # Exit on any error

GEMINI_COMMANDS_DIR="$HOME/.gemini/commands"
SPEC_DIR="$GEMINI_COMMANDS_DIR/spec"

echo "Installing Spec-Driven Development for Gemini CLI..."

# --- OS Detection and Bash Executable Path ---
BASH_EXECUTABLE="bash" # Default for Linux/macOS
IS_WINDOWS=false

# Check for Windows environment (more robust than just OSTYPE for Git Bash)
if [[ "$(uname -s)" =~ MINGW|CYGWIN|MSYS ]]; then
    IS_WINDOWS=true
elif [[ "$(uname -s)" =~ ^Linux$ && -n "$WSL_DISTRO_NAME" ]]; then
    # This is WSL, but we still want to use Git Bash if available for the prompt
    # If install-gemini.sh is run from WSL, it should still try to find Git Bash.
    IS_WINDOWS=true # Treat WSL as Windows for the purpose of finding Git Bash
fi

if $IS_WINDOWS; then
    echo "Detected Windows environment."
    if command -v git &> /dev/null; then
        # Get the absolute Unix-style path to git.exe from command -v git
        GIT_EXE_PATH_UNIX=$(command -v git)
        
        # Convert this Unix-style path to an absolute Windows path using cygpath -w
        if command -v cygpath &> /dev/null; then
            GIT_EXE_PATH_WINDOWS=$(cygpath -w "$GIT_EXE_PATH_UNIX")
        else
            echo "WARNING: 'cygpath' not found. Cannot convert Git executable path to Windows style. Falling back to default 'bash'."
            # BASH_EXECUTABLE remains "bash" (default fallback)
        fi

        if [ -n "$GIT_EXE_PATH_WINDOWS" ]; then # Only proceed if GIT_EXE_PATH_WINDOWS was successfully determined
            # Normalize path to use forward slashes for easier string manipulation in bash
            GIT_EXE_PATH_WINDOWS_SLASHES=$(echo "$GIT_EXE_PATH_WINDOWS" | sed 's/\\/\//g')

            GIT_ROOT_DIR_WINDOWS=""
            # Determine the actual Git installation root (e.g., C:/Program Files/Git)
            # Start with the directory containing git.exe
            CURRENT_DIR=$(dirname "$GIT_EXE_PATH_WINDOWS_SLASHES")
            
            # Traverse up the directory tree until we find a directory that looks like the Git root
            while [[ "$CURRENT_DIR" != "/" && "$CURRENT_DIR" != "" ]]; do
                if [[ -d "$CURRENT_DIR/bin" && -d "$CURRENT_DIR/usr" && -d "$CURRENT_DIR/mingw64" ]]; then
                    GIT_ROOT_DIR_WINDOWS="$CURRENT_DIR"
                    break
                fi
                CURRENT_DIR=$(dirname "$CURRENT_DIR")
            done

            if [ -z "$GIT_ROOT_DIR_WINDOWS" ]; then
                echo "WARNING: Could not determine Git installation root by traversing up from $GIT_EXE_PATH_WINDOWS. Falling back to default 'bash'."
                # BASH_EXECUTABLE remains "bash" (default fallback)
            else
                TEMP_BASH_EXECUTABLE=""

                # Prioritize common locations for bash.exe
                if [ -f "$GIT_ROOT_DIR_WINDOWS/bin/bash.exe" ]; then
                    TEMP_BASH_EXECUTABLE="$GIT_ROOT_DIR_WINDOWS/bin/bash.exe"
                elif [ -f "$GIT_ROOT_DIR_WINDOWS/usr/bin/bash.exe" ]; then
                    TEMP_BASH_EXECUTABLE="$GIT_ROOT_DIR_WINDOWS/usr/bin/bash.exe"
                elif [ -f "$GIT_ROOT_DIR_WINDOWS/mingw64/bin/bash.exe" ]; then
                    TEMP_BASH_EXECUTABLE="$GIT_ROOT_DIR_WINDOWS/mingw64/bin/bash.exe"
                fi

                if [ -f "$TEMP_BASH_EXECUTABLE" ]; then
                    # Convert to Windows-style path using cygpath -w (already checked for cygpath earlier)
                    WINDOWS_BASH_PATH=$(cygpath -w "$TEMP_BASH_EXECUTABLE")
                    if [ -f "$WINDOWS_BASH_PATH" ]; then
                        BASH_EXECUTABLE="$WINDOWS_BASH_PATH"
                        echo "Found Git Bash executable at: $BASH_EXECUTABLE (Windows path)"
                    else
                        echo "WARNING: Git Bash's bash.exe not found at inferred Windows path: $WINDOWS_BASH_PATH. Falling back to default 'bash'."
                        # BASH_EXECUTABLE remains "bash" (default fallback)
                    fi
                else
                    echo "WARNING: Could not find bash.exe in common Git installation paths relative to $GIT_ROOT_DIR_WINDOWS. Falling back to default 'bash'."
                    # BASH_EXECUTABLE remains "bash" (default fallback)
                fi
            fi
        else
            echo "WARNING: Could not determine Git installation root from git.exe path: $GIT_EXE_PATH_WINDOWS. Falling back to default 'bash'."
            # BASH_EXECUTABLE remains "bash" (default fallback)
        fi
    else
        echo "WARNING: Git command not found in PATH. Falling back to default 'bash'."
        # BASH_EXECUTABLE remains "bash" (default fallback)
    fi
else
    echo "Detected Linux/macOS environment."
    # BASH_EXECUTABLE remains "bash" (default)
fi

echo "Using bash executable: $BASH_EXECUTABLE"





echo "Creating global spec command directory: $SPEC_DIR"
mkdir -p "$SPEC_DIR" || { echo "ERROR: Failed to create directory $SPEC_DIR"; exit 1; }
echo "Directory $SPEC_DIR created successfully."

# Copy system files (from .yask directory)
echo "Copying .yask directory to $SPEC_DIR/"
cp -r ./.yask "$SPEC_DIR/" || { echo "ERROR: Failed to copy ./.yask to $SPEC_DIR/"; exit 1; }
echo "Copying spec-dev-agent.md to $SPEC_DIR/"
cp ./spec-dev-agent.md "$SPEC_DIR/" || { echo "ERROR: Failed to copy ./spec-dev-agent.md to $SPEC_DIR/"; exit 1; }
echo "System files copied successfully to $SPEC_DIR/."

cat > "$GEMINI_COMMANDS_DIR/spec.toml" << EOF
prompt = '1: check for folder .yask in project folder to see if installed, check output of command to beware errors instead of no found \ if YES, guide the user in detail to develop using spec-driven being informative / if NO, find main Git folder using (where git) then run this command using quotes for paths and tell user to restart gemini when done: <GIT>\bin\bash.exe  <user>\.gemini\commands\spec\spec-dev-setup.sh'
description = "Initializes specification-driven development in the current workspace."
EOF
if [ $? -ne 0 ]; then echo "ERROR: Failed to create $GEMINI_COMMANDS_DIR/spec.toml"; exit 1; fi
echo "spec.toml created successfully in $GEMINI_COMMANDS_DIR."

# Create setup script
echo "Creating spec-dev-setup.sh in $SPEC_DIR/"
cat > "$SPEC_DIR/spec-dev-setup.sh" << 'SPEC_SETUP_EOF'
#!/bin/bash
# Spec-driven development setup for current workspace

set -e

WORKSPACE_GEMINI_DIR="./.gemini"
SPEC_SYS_DIR="$WORKSPACE_GEMINI_DIR"
COMMANDS_SPEC_DIR="$HOME/.gemini/commands/spec" # This relies on HOME being set correctly by Gemini CLI

echo "Setting up spec-driven development in current workspace..."

# 1. Copy .yask system files to .gemini
echo "Copying .yask system files to $SPEC_SYS_DIR..."
mkdir -p "$SPEC_SYS_DIR"
cp -r "$COMMANDS_SPEC_DIR/.yask" "$SPEC_SYS_DIR/"

# 2. Install agent prompt in workspace
# Check for conflict before copying agent prompt file
if [ -e "./.yask" ]; then # Use -e to check for existence of file or directory
    echo "ERROR: A file or directory named './.yask' already exists in the workspace root."
    echo "Please rename or remove it before running the /spec command to avoid conflicts."
    exit 1
fi

echo "Installing spec-dev prompt as .spec..."
cp "$COMMANDS_SPEC_DIR/spec-dev-agent.md" "./.spec"

# 3. Configure Gemini workspace settings (.gemini/settings.json)
mkdir -p "$WORKSPACE_GEMINI_DIR"

# Backup existing settings if they exist
if [ -f "$WORKSPACE_GEMINI_DIR/settings.json" ]; then
    echo "Backing up existing settings.json to settings_old.json..."
    mv "$WORKSPACE_GEMINI_DIR/settings.json" "$WORKSPACE_GEMINI_DIR/settings_old.json"
fi

echo "Creating Gemini workspace settings in $WORKSPACE_GEMINI_DIR/settings.json..."
cat > "$WORKSPACE_GEMINI_DIR/settings.json" << 'SETTINGS_EOF'
{
  "contextFileName": ".spec",
  "includeDirectories": [".gemini/.yask"],
  "fileFiltering": {
    "respectGitIgnore": false
  }
}
SETTINGS_EOF

echo "✅ Spec-driven development setup complete!"
echo "📁 System files: $SPEC_SYS_DIR/.yask/"
echo "🤖 Agent prompt: ./.spec (loaded automatically)"
echo "⚙️  Workspace settings: $WORKSPACE_GEMINI_DIR/settings.json"
echo ""
echo "You can now use spec-driven development in this workspace."
SPEC_SETUP_EOF

# Make setup script executable
chmod +x "$SPEC_DIR/spec-dev-setup.sh"

# --- Generate Admin Launcher for Windows ---


# Verify the files were created successfully
echo "Verifying installation..."
if [ -f "$SPEC_DIR/spec-dev-agent.md" ] && [ -d "$SPEC_DIR/.yask" ] && [ -f "$SPEC_DIR/spec-dev-setup.sh" ]; then
    echo "✅ Files successfully copied and created."
    
    echo ""
    echo "✅ Gemini CLI integration installed successfully!"
    echo ""
    echo "Usage:"
    echo "  Manual setup: Copy files to project and rename prompt to .gemini"
    echo "  Automated setup: Run '/spec' command in any project directory"
    echo ""
    echo "The '/spec' command will:"
    echo "  - Copy system files to workspace .gemini"
    echo "  - Install agent prompt as .spec"
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
        rm -rf ./.yask
        rm -f ./install-gemini.sh
        
        echo "✅ Original files cleaned up."
    else
        echo "Original files preserved."
    fi
else
    echo "❌ Installation verification failed. Files may not have been copied correctly."
    exit 1
fi

# The extraneous closing brace '}' has been removed from the end of the file.