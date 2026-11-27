:; d=$(cd "$(dirname "$0")" && pwd) && n=$(basename "$0" .cmd) && case $(uname -s) in Linux|Darwin) rm -f "$d/ws-windows-setup.cmd" 2>/dev/null || : ;; esac && t=$d/_steering/.yask/_toolstore/ws/$n && { [ -f "$t" ] || { echo "$n: $t was not found" >&2; exit 127; }; } && exec env WS_ROOT="$d" sh "$t" "$@"; exit 127 #
@echo off
rem Launcher for this workspace: one file for sh (Linux, macOS, WSL, Git Bash) and for cmd.exe or PowerShell.
rem Nothing is installed and nothing goes on the PATH. It always works on the workspace it sits in.
rem   sh:          ./ws COMMAND         (or: sh ws COMMAND, which needs no execute bit)
rem   Windows:     run ws-windows-setup.cmd once, then .\ws COMMAND in PowerShell or ws.cmd COMMAND in cmd.exe
rem On Linux and macOS the sh half removes ws-windows-setup.cmd on first run; Git Bash and MSYS leave it for Windows.
rem The file name picks the tool: a copy named yask (or yask.cmd after setup) runs yask, the same tool under its second name.
rem Line 1 is what sh runs (cmd reads it as a label); the rest is cmd. Keep CRLF line endings and the # that ends line 1: sh reads the CR as a comment.
rem Keep rem lines free of the characters cmd treats as operators. Fallback if this file misbehaves: _steering\.yask\_toolstore\ws\ws.cmd (cmd) or sh _steering/.yask/_toolstore/ws/ws (sh).
setlocal
set "WS_ROOT=%~dp0"
if not exist "%~dp0_steering\.yask\_toolstore\ws\%~n0.cmd" goto missing
"%~dp0_steering\.yask\_toolstore\ws\%~n0.cmd" %*
exit /b %errorlevel%
:missing
echo %~n0: _steering\.yask\_toolstore\ws\%~n0.cmd was not found 1>&2
exit /b 127
