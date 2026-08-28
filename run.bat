@echo off
rem ==================================================
rem  Reverb render launcher - edit the 3 lines below, then double-click.
rem  Usage: double-click, or run "run.bat" from a terminal.
rem ==================================================
setlocal

rem ---- Edit these ----
set SRC=One More Light.wav
set DST=output.wav
set MIX=0.5
set LOUDN=None
rem ---------------------
rem  SRC   input audio (project root; may be a full path)
rem  DST   output file (written to project root)
rem  MIX   dry/wet 0-1; set to None to use the mix in params.md
rem  LOUDN output loudness in dBFS; None = no loudness match

cd /d "%~dp0"

if not exist "dattorro_reverb\demo.py" (
    echo [ERROR] dattorro_reverb\demo.py not found. Run this from the project root.
    pause
    exit /b 1
)

set ARGS=
if not "%MIX%"=="None"   set ARGS=%ARGS% --mix=%MIX%
if not "%LOUDN%"=="None" set ARGS=%ARGS% --loudn_out=%LOUDN%

echo Input : %SRC%
echo Output: %DST%
echo Args  :%ARGS%
echo.
python -m dattorro_reverb.demo "%SRC%" "%DST%" %ARGS%
if errorlevel 1 (
    echo.
    echo [FAILED] Render error. Check the input path above and params.md.
    pause
    exit /b 1
)

echo.
echo Done - output: %DST%
pause