@echo off
call "D:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d "D:\deepAsh\project_reverb\tmp\el_visio"
"D:\deepAsh\project_reverb\tmp\el_visio\demo_reverb.exe" "D:\deepAsh\project_reverb\One More Light-44.1k.wav" "D:\deepAsh\project_reverb\output\el_visio_tank_44k.wav" 0.5
pause