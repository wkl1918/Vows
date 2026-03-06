@echo off
chcp 65001 >nul
title VoxFlow 视频配音 (新傻瓜拖拽版)

set FILE=%~1
if "%FILE%"=="" (
    echo.
    echo [错误] 请拖拽文件到这个bat图标上来!
    echo [可选] 命令行模式可传第二个参数作为目标语言，例如: 一键处理视频.bat "D:\demo.mp4" en
    pause
    exit /b
)

set TARGET_LANG=%~2
if "%TARGET_LANG%"=="" (
    echo.
    echo 请选择目标语言代码（支持 50 种，直接回车=zh）：
    echo zh中文 en英文 ja日文 ko韩文 es西班牙语 fr法语 de德语 ru俄语 it意大利语 pt葡萄牙语
    echo ar阿拉伯语 hi印地语 th泰语 vi越南语 tr土耳其语 nl荷兰语 pl波兰语 id印尼语 ms马来语 fa波斯语
    echo uk乌克兰语 cs捷克语 sk斯洛伐克语 hu匈牙利语 ro罗马尼亚语 bg保加利亚语 hr克罗地亚语 sl斯洛文尼亚语 sr塞尔维亚语
    echo da丹麦语 sv瑞典语 no挪威语 fi芬兰语 et爱沙尼亚语 lv拉脱维亚语 lt立陶宛语 el希腊语 he希伯来语
    echo bn孟加拉语 ta泰米尔语 te泰卢固语 mr马拉地语 gu古吉拉特语 kn卡纳达语 ml马拉雅拉姆语 ur乌尔都语
    echo sw斯瓦希里语 af南非语 fil菲律宾语 ca加泰罗尼亚语
    set /p INPUT_LANG=请输入语言代码: 
    if "%INPUT_LANG%"=="" (
        set TARGET_LANG=zh
    ) else (
        set TARGET_LANG=%INPUT_LANG%
    )
)
if "%TARGET_LANG%"=="" set TARGET_LANG=zh

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
echo 引擎已就绪，正在准备制作... (目标语言: %TARGET_LANG%)
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
python run_task.py "%FILE%" "%TARGET_LANG%"

echo 全部流程结束！
pause
