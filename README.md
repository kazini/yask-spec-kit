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
- Add VS-based profile for Roo and Kilo.

-! remove dependency on spec.sh script. Almost fully achieved.
? ...should we remove installer dependency altogether and bundle different zip releases for specific agent wrappers?

-! refine cross-documentation workflow, check that when updating design, it checks if it needs to update requirements, make more open to also changing ALL docs

? Centralized prompt, must check performance, as preemptive evaluation indicates degradation of context comprehension. More testing required.
	* Initial testing suggests 'collage' centralized prompt produces worse results in models with sub-par instruction adherence, results degrade versus central+3 instruction method.
	* Initial versions of 'jigsaw' centralized prompt are created, but must be further refined, validating results and focusing on format and wording inducing results and adherence.
		> This seems to suggest that actually having 4 different files with redundancies, even if loaded at a secondary point, improve functionality.
		> This seems... odd, as it all ends up in the same context, so 'collage' centralized prompt should perform identically.


* Future:
	* Adding Validation and Testing guidelines and procedures
	* Testing efficacy and then adding procedures for Pseudocode-based code parsing and creation
	
	- look into maybe incorporating some more best practices and principles from the kiro guide docs.
	? Work on integrations. Methods to recognize and use specific MCP tools such as Tree-Sitter and code health and parsing/validation tools would be meaningful, but drift the project away from its current flexiblity.
	
	* Evaluate what adding a script could meaningfully contribute with, as to keep the prompt flexible and agnostic. *Could help with auto-updating it and with code validation.*
	
```
