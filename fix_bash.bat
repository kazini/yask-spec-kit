@echo off
setlocal

:: Check for administrative privileges
NET SESSION >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Requesting administrative privileges...
    GOTO :ADMIN_PROMPT
)

:: Define the Git Bash bin path
SET "GIT_BASH_BIN=C:\Program Files\Git\bin"

ECHO Modifying system PATH to prioritize Git Bash...

:: Get the current system PATH
FOR /F "tokens=*" %%A IN ('REG QUERY "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') DO (
    FOR /F "tokens=2*" %%B IN ("%%A") DO (
        SET "CURRENT_PATH=%%C"
    )
)

:: Remove existing Git Bash entries from the PATH to avoid duplicates and ensure correct order
:: This is a simplified removal and might not catch all variations.
SET "NEW_PATH=%CURRENT_PATH:C:\Program Files\Git\bin;=%%"
SET "NEW_PATH=%NEW_PATH:C:\Program Files\Git\cmd;=%%"
SET "NEW_PATH=%NEW_PATH:C:\Program Files\Git\usr\bin;=%%"
SET "NEW_PATH=%NEW_PATH:C:\Program Files\Git\usr\share\git-core;=%%"

:: Prepend the desired Git Bash bin path to the new PATH
SET "NEW_PATH=%GIT_BASH_BIN%;%NEW_PATH%"

:: Remove any trailing semicolons that might result from the removal process
IF "%NEW_PATH:~-1%"==";" SET "NEW_PATH=%NEW_PATH:~0,-1%"

:: Set the new system-wide PATH variable
:: setx is used for permanent system-wide changes.
:: /M specifies the machine-wide environment variable.
ECHO Setting new system PATH...
setx PATH "%NEW_PATH%" /M

ECHO.
ECHO System PATH updated successfully!
ECHO New PATH (first few entries):
ECHO %NEW_PATH% | FINDSTR /B /C:"%GIT_BASH_BIN%"
ECHO.
ECHO Please restart your terminal/IDE or reboot your system for changes to take full effect.
GOTO :EOF

:ADMIN_PROMPT
ECHO This script needs to be run as an administrator.
ECHO Right-click the .bat file and select "Run as administrator".
PAUSE
EXIT /B 1