
@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist logs mkdir logs

:START
echo.>> logs\bot.log
echo [%date% %time%] Запуск бота >> logs\bot.log

python -u main.py >> logs\bot.log 2>&1

set EXITCODE=%errorlevel%
echo [%date% %time%] Бот остановился. Код: %EXITCODE% >> logs\bot.log
echo Перезапуск через 10 секунд...
timeout /t 10 /nobreak >nul

goto START
