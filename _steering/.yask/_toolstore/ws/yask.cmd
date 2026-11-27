@echo off
rem yask shim: the same tool as ws. Uses WS_PYTHON, then python, py -3 or python3; assumes Python 3.8+.
setlocal
set WS_PROG=yask
if not defined WS_PYTHON goto try_python
"%WS_PYTHON%" "%~dp0..\ws\ws.py" %*
exit /b %errorlevel%
:try_python
python "%~dp0..\ws\ws.py" %*
if "%errorlevel%"=="9009" goto try_py
exit /b %errorlevel%
:try_py
py -3 "%~dp0..\ws\ws.py" %*
if "%errorlevel%"=="9009" goto try_py3
exit /b %errorlevel%
:try_py3
python3 "%~dp0..\ws\ws.py" %*
if "%errorlevel%"=="9009" goto missing
exit /b %errorlevel%
:missing
echo yask: Python 3 was not found on the PATH 1>&2
exit /b 127
