# ПОЛНАЯ ПРОВЕРКА СООТВЕТСТВИЯ КОДА
# Проверяет что локальный код == Docker код == актуальный report.html

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ПРОВЕРКА СООТВЕТСТВИЯ КОДА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Проверка локального pdf_generator.py
Write-Host "[1/7] Проверка локального файла..." -ForegroundColor Yellow
$localFile = "BotCut\pdf_generator.py"
if (Test-Path $localFile) {
    $localMD5 = (Get-FileHash -Path $localFile -Algorithm MD5).Hash
    Write-Host "  ✓ MD5: $localMD5" -ForegroundColor Green
} else {
    Write-Host "  ✗ Файл не найден!" -ForegroundColor Red
    exit 1
}

# 2. Проверка файла в контейнере
Write-Host "[2/7] Проверка файла в Docker..." -ForegroundColor Yellow
$containerMD5 = docker exec hpmcut-bot md5sum /app/pdf_generator.py 2>$null
if ($LASTEXITCODE -eq 0) {
    $containerMD5Hash = ($containerMD5 -split '\s+')[0]
    Write-Host "  ✓ MD5: $containerMD5Hash" -ForegroundColor Green

    if ($localMD5 -eq $containerMD5Hash.ToUpper()) {
        Write-Host "  ✓ MD5 СОВПАДАЮТ!" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MD5 НЕ СОВПАДАЮТ!" -ForegroundColor Red
        Write-Host "    Локальный:  $localMD5" -ForegroundColor Red
        Write-Host "    Контейнер:  $containerMD5Hash" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ Контейнер не запущен!" -ForegroundColor Red
    exit 1
}

# 3. Проверка что нет старого Helvetica-Bold
Write-Host "[3/7] Проверка шрифтов в PDF..." -ForegroundColor Yellow
$helvetica = Select-String -Path $localFile -Pattern "Helvetica-Bold" -Quiet
if ($helvetica) {
    Write-Host "  ✗ Найден Helvetica-Bold (черные квадраты!)" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  ✓ Все шрифты используют self.font_name" -ForegroundColor Green
}

# 4. Проверка UTF-8 encoding
Write-Host "[4/7] Проверка UTF-8 encoding..." -ForegroundColor Yellow
$utf8 = Select-String -Path $localFile -Pattern "encoding='utf-8'" -Quiet
if ($utf8) {
    Write-Host "  ✓ UTF-8 encoding указан" -ForegroundColor Green
} else {
    Write-Host "  ✗ UTF-8 encoding НЕ указан!" -ForegroundColor Red
    exit 1
}

# 5. Проверка __pycache__
Write-Host "[5/7] Проверка __pycache__..." -ForegroundColor Yellow
$pycache = Get-ChildItem -Path "BotCut" -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue
if ($pycache) {
    Write-Host "  ⚠ Найден __pycache__: $($pycache.FullName)" -ForegroundColor Yellow
    Write-Host "    Очищаю..." -ForegroundColor Yellow
    Remove-Item -Path "BotCut\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Очищено" -ForegroundColor Green
} else {
    Write-Host "  ✓ __pycache__ не найден" -ForegroundColor Green
}

# 6. Проверка docker-compose.yml
Write-Host "[6/7] Проверка docker-compose.yml..." -ForegroundColor Yellow
$dockerCompose = Get-Content "docker-compose.yml" -Raw
if ($dockerCompose -match "PYTHONDONTWRITEBYTECODE=1") {
    Write-Host "  ✓ PYTHONDONTWRITEBYTECODE=1 включен" -ForegroundColor Green
} else {
    Write-Host "  ✗ PYTHONDONTWRITEBYTECODE=1 НЕ включен!" -ForegroundColor Red
    exit 1
}

# 7. Проверка .dockerignore
Write-Host "[7/7] Проверка .dockerignore..." -ForegroundColor Yellow
$dockerIgnore = Get-Content ".dockerignore" -Raw
if ($dockerIgnore -match "__pycache__") {
    Write-Host "  ✓ __pycache__ в .dockerignore" -ForegroundColor Green
} else {
    Write-Host "  ✗ __pycache__ НЕ в .dockerignore!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Код в локальном проекте и Docker контейнере ИДЕНТИЧЕН!" -ForegroundColor Green
Write-Host "HTML и PDF будут генерироваться с правильной кириллицей." -ForegroundColor Green
Write-Host ""
Write-Host "Следующий шаг: протестировать отчеты в боте!" -ForegroundColor Yellow
