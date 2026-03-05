@echo off
set "ACTIVATE_BAT="
if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" set "ACTIVATE_BAT=%USERPROFILE%\anaconda3\Scripts\activate.bat"
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" set "ACTIVATE_BAT=%USERPROFILE%\miniconda3\Scripts\activate.bat"
if exist "%ProgramData%\anaconda3\Scripts\activate.bat" set "ACTIVATE_BAT=%ProgramData%\anaconda3\Scripts\activate.bat"
if defined ACTIVATE_BAT (
    call "%ACTIVATE_BAT%" VoxFlow
) else (
    call conda activate VoxFlow
)
cd /d "%~dp0backend"
title VoxFlowBackend
echo 正在全速启动...
python app.py
