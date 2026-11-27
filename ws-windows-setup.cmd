@echo off
rem Windows setup for the polyglot launchers in this folder: give them their .cmd names.
rem Run once after copying the template on Windows. Safe to run again.
rem Works from any folder: only files next to this script are touched.
rem Removes itself after a run that renamed at least one launcher.
setlocal
set "changed="
pushd "%~dp0" || exit /b 1
call :one ws || goto fail
call :one yask || goto fail
popd
if not defined changed goto nothing
echo ws-windows-setup: done; removing this script
(goto) 2>nul & del "%~f0"
:nothing
echo ws-windows-setup: done; nothing to rename
exit /b 0
:fail
popd
exit /b 1
:one
if exist "%~1.cmd" (
  echo ws-windows-setup: %~1.cmd is already set up
  exit /b 0
)
if not exist "%~1" (
  echo ws-windows-setup: %~1 was not found, skipped
  exit /b 0
)
move /Y "%~1" "%~1.cmd" >nul
if errorlevel 1 (
  echo ws-windows-setup: could not rename %~1 1>&2
  exit /b 1
)
echo ws-windows-setup: renamed %~1 to %~1.cmd
set "changed=1"
exit /b 0
