@echo off
REM Скрипт для пересборки HPMCut контейнеров с новыми изменениями (Windows)

echo ==================================
echo  Пересборка HPMCut контейнеров
echo ==================================
echo.

REM Остановить и удалить старые контейнеры
echo [1/5] Остановка старых контейнеров...
docker-compose down

REM Удалить старые образы
echo.
echo [2/5] Удаление старых образов...
docker rmi hpmcut-web:latest hpmcut-bot:latest 2>nul
if %ERRORLEVEL% NEQ 0 echo Старые образы не найдены

REM Пересобрать образы
echo.
echo [3/5] Сборка новых образов (это может занять несколько минут)...
docker-compose build --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Не удалось собрать образы!
    pause
    exit /b 1
)

REM Запустить контейнеры
echo.
echo [4/5] Запуск контейнеров...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Не удалось запустить контейнеры!
    pause
    exit /b 1
)

REM Показать статус
echo.
echo [5/5] Статус контейнеров:
docker-compose ps

echo.
echo ==================================
echo  Готово!
echo ==================================
echo.
echo Для просмотра логов: docker-compose logs -f
echo Для остановки: docker-compose down
echo.

REM Спросить, показать ли логи
set /p showlogs="Показать логи? (y/n): "
if /i "%showlogs%"=="y" (
    echo.
    echo Логи (Ctrl+C для выхода):
    docker-compose logs -f --tail=50
)

pause
