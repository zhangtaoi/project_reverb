@echo off
rem ==================================================
rem  Reverb render launcher - edit the lines below, then double-click.
rem  Usage: double-click, or run "run.bat" from a terminal.
rem ==================================================
setlocal

rem ---- Edit these (or just set them in params.yaml) ----
set SRC=data\One More Light.wav
set DST=output\output.wav
set MODEL=reverb
set MIX=0.5
set LOUDN=None
set PRESET=hall
rem -----------------------------------------------------
rem  SRC    input audio (relative to project root)
rem  DST    output file (relative to project root)
rem  MODEL  algorithm: reverb (tank, paper-faithful) or comb (compact)
rem  MIX    dry/wet 0-1; None = use params.yaml
rem  LOUDN  output loudness in dBFS; None = no loudness match
rem  PRESET preset name: plate, room, hall; None = algorithm defaults

cd /d "%~dp0"

if "%MODEL%"=="comb" (
    set MODULE=dattorro_comb.demo
) else (
    set MODULE=dattorro_reverb.demo
)

if not exist "%MODULE:.demo=%\demo.py" (
    echo [ERROR] %MODULE:.demo=%\demo.py not found. Run this from the project root.
    pause
    exit /b 1
)

set ARGS=
if not "%MIX%"=="None"   set ARGS=%ARGS% --mix=%MIX%
if not "%LOUDN%"=="None" set ARGS=%ARGS% --loudn_out=%LOUDN%
if "%MODEL%"=="reverb" (
    if not "%PRESET%"=="None" set ARGS=%ARGS% --preset=%PRESET%
)

echo Input : %SRC%
echo Output: %DST%
echo Model : %MODEL%
if "%MODEL%"=="reverb" echo Preset: %PRESET%
echo Args  :%ARGS%
echo.
python -m %MODULE% "%SRC%" "%DST%" %ARGS%
if errorlevel 1 (
    echo.
    echo [FAILED] Render error. Check the input path above and params.yaml.
    pause
    exit /b 1
)

echo.
echo Done - output: %DST%
pause