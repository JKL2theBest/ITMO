@echo off

if "%1"=="" (
    echo.
    echo Ошибка: Команда не указана.
    echo Пожалуйста, используйте: setup, on, off, status, watch
    echo.
    echo   Первый запуск: start.bat setup
    echo.
    goto :end
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0protector.ps1" -Mode %1

:end
pause