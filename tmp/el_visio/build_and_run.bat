@echo off
call "D:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d "%~dp0"
cl verb.c test_ir.c /Fe:test_ir.exe
if errorlevel 1 (
    echo Compilation failed
    exit /b 1
)
echo Build OK
test_ir.exe