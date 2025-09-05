@echo off
rem Файл-запускатор для protector.ps1

set "MODE=%1"
if not defined MODE goto :help

if /I "%MODE%"=="setup"  goto :run
if /I "%MODE%"=="on"     goto :run
if /I "%MODE%"=="off"    goto :run
if /I "%MODE%"=="status" goto :run
if /I "%MODE%"=="watch"  goto :run

goto :help

:run
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0protector.ps1" -Mode %1
goto :end

:help
echo.
echo Ошибка: Неверная или отсутствующая команда '%1'.
echo Пожалуйста, используйте одну из следующих команд:
echo.
echo   start.bat setup    - для первоначальной настройки
echo   start.bat on       - для включения защиты для существующих файлов
echo   start.bat off      - для отключения защиты
echo   start.bat status   - для проверки текущего статуса
echo   start.bat watch    - для запуска режима слежения за новыми файлами
echo.
goto :end

:end
pause