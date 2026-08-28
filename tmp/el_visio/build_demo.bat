@echo off
call "D:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d "D:\deepAsh\project_reverb\tmp\el_visio"
cl verb.c demo_reverb.c /Fe:demo_reverb.exe
if errorlevel 1 (
    echo Compilation failed
    exit /b 1
)
echo Build OK
"D:\deepAsh\project_reverb\tmp\el_visio\demo_reverb.exe" "D:\deepAsh\project_reverb\One More Light.wav" "D:\deepAsh\project_reverb\output\el_visio_tank.wav" 0.5
pause