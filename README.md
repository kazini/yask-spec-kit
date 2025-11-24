## YASK, a Kiro-inspired Spec-Dev System

**Yet Another Spec-Kit.** Go figures! I based this spec-kit mainly using Kiro's rules and guidelines and complimented with documentation from a few others, like user-created and GitHub's own spec-kit. I wasn't satisfied with any of them. This format *should* be compatible with Kiro.

**Differences to Kiro**: This is Kiro's methodology made explicit and platform-independent. Same principles, same workflow, same results, but documented for use with any AI system or IDE. Potentially scales better across teams, tools, and complex projects using explicit documentation patterns. See `report.md` for an AI-generated evaluation.

Reports on performance and suggestions for improvements are welcomed! Best of luck with your projects.

__________
*(Windows) Requires: Git for Windows, for Bash*

Transform feature ideas into structured specifications through AI-guided Requirements → Design → Tasks → Implementation workflow.

### **1. Gemini CLI Setup**
####   **Manual Installation:**
- Copy into your project workspace, change the agent prompt to `gemini.md` and delete the installers.
####   **Automated Installation (For frequent use):**
- Extract the files somewhere, and run `./install-gemini.sh`
- Use `/spec` in Gemini to initialize spec-dev in your current workspace. Restart Gemini.`

### **2. Cursor IDE Setup**
####   **Manual Installation:**
- Extract the files to your project directory and run `./install-cursor.sh`
- Cursor will automatically load the spec-dev agent rules and system files

*If your agent is having troubles with the scripts, windows is likely using WSL's bash instead of Git's. Run 'fix_bash.bat' as admin to add Bash to your path.*

### **3. System Structure & Documentation**
The core components of this system are:
*   `spec-dev-agent.md`: The instructions for the AI agent.
*   `.yask/`: Contains all supporting system configurations, tools, and detailed documentation.
*   `blueprint/`: This is where you'll store your project's development specifications.

All in-depth documentation, covering core principles, methodology, interaction patterns, prompting strategies, and implementation support (templates, scripts), is organized within the `.yask/` directory.

*Special thanks to [@jasonkneen](https://github.com/jasonkneen) for their Kiro documentation set as a point of reference for the creation of this instruction set.*
__________

### To Do:
```md
> Need to test both 2.21 and 2.21_cf side by side.

* Must make installer(s) also remove the install-cursor file.
- Must fix cursor implementation automation, currently as a 'mode' or modified custom instruction for Plan mode, only tried as a custom mode.

* Adding Validation and Testing guidelines

-! remove dependency on spec.sh script.

-! refine cross-documentation workflow, check that when updating design, it checks if it needs to update requirements, make more open to also changing ALL docs

? Centralized prompt, must check performance, as preemptive evaluation indicates degradation of context comprehension. More testing required.


* Future:
	- look into maybe incorporating some more best practices and principles from the kiro guide docs.
	? Work on integrations.
```
