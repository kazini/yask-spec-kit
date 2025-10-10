## YASK, a Kiro-inspired Spec-Dev System

**Yet Another Spec-Kit.** Go figures! I based this spec-kit mainly using Kiro's rules and guidelines and complimented with documentation from a few others, like user-created and GitHub's own spec-kit. I wasn't satisfied with any of them. This format *should* be compatible with Kiro.

Reports on performance and improvements are welcomed! Best of luck with your projects.

*A catchier and not-so-generic name is direly needed. -Kaz*
__________
*(Windows) Requires: Git for Windows, for Bash*

Transform feature ideas into structured specifications through AI-guided Requirements → Design → Tasks → Implementation workflow.

### **1. Gemini CLI Setup**
####   **Manual Installation:**
- Copy into your project workspace, change the agent prompt to `gemini.md` and delete the installers.
####   **Automated Installation (For frequent use):**
- Extract the files somewhere, and run `./install-gemini.sh`
- Use `/spec` in Gemini to initialize spec-dev in your current workspace. Reload with `/memory refresh`


### **2. Cursor IDE Setup**
####   **Manual Installation:**
- Extract the files to your project directory and run `./install-cursor.sh`
- Cursor will automatically load the spec-dev agent rules and system files

### **3. System Structure & Documentation**
The core components of this system are:
*   `spec-dev-agent.md`: The instructions for the AI agent.
*   `.spec-dev/`: Contains all supporting system configurations, tools, and detailed documentation.
*   `.specification/`: This is where you'll store your project's development specifications.

All in-depth documentation, covering core principles, methodology, interaction patterns, prompting strategies, and implementation support (templates, scripts, examples), is organized within the `.spec-dev/` directory. For a complete overview and navigation, please refer to `.spec-dev/overview.md`.
