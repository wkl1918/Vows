@echo off
chcp 65001 >nul
title VoxFlow 视频配音含硬字幕 (新傻瓜拖拽版)

set FILE=%~1
if "%FILE%"=="" (
    echo.
    echo [错误] 请拖拽文件到这个bat图标上来!
    pause
    exit /b
)

echo 正在检查引擎是否运行...
netstat -ano | findstr "LISTENING" | findstr ":8000" >nul
if %errorlevel% equ 0 goto ready

echo 没检测到正在运行的引擎，现在自动帮你启动...
echo (请保持弹出的新窗口一直开着)
:: 用独立辅助脚本启动，避免嵌套引号解析问题
start "VoxFlow Backend" cmd /k "%~dp0_start_backend.bat"

set /a c=0
:loop
timeout /t 3 >nul
netstat -ano | findstr "LISTENING" | findstr ":8000" >nul
if %errorlevel% equ 0 goto ready
set /a c+=1
if %c% lss 30 goto loop

echo 启动似乎花了太长时间，或报错了，请看另一个黑窗口
pause
exit /b

:ready
echo 引擎已就绪，正在准备制作...
pushd "%~dp0"
set "ACTIVATE_BAT="
if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" set "ACTIVATE_BAT=%USERPROFILE%\anaconda3\Scripts\activate.bat"
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" set "ACTIVATE_BAT=%USERPROFILE%\miniconda3\Scripts\activate.bat"
if exist "%ProgramData%\anaconda3\Scripts\activate.bat" set "ACTIVATE_BAT=%ProgramData%\anaconda3\Scripts\activate.bat"
if defined ACTIVATE_BAT (
    call "%ACTIVATE_BAT%" VoxFlow
) else (
    call conda activate VoxFlow
)
python run_task_with_subtitles.py "%FILE%"

echo 全部流程结束！
pause
