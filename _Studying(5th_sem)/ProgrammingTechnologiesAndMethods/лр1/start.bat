@echo off
rem Файл-запускатор для protector.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0protector.ps1" -Mode %1
pause