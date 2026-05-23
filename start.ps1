# Script de Inicio Rápido - Sistema MAS-CIS
# Este script verifica la configuración e inicia el sistema

Write-Host "🚀 Iniciando Sistema MAS-CIS..." -ForegroundColor Cyan
Write-Host ""

# Verificar archivo .env
Write-Host "1️⃣ Verificando configuración..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "   ❌ Archivo .env no encontrado" -ForegroundColor Red
    Write-Host "   💡 Ejecuta primero: .\install.ps1" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "   ✅ Archivo .env encontrado" -ForegroundColor Green
}

# Verificar SQL Server
Write-Host ""
Write-Host "2️⃣ Verificando SQL Server..." -ForegroundColor Yellow
$sqlService = Get-Service -Name MSSQLSERVER -ErrorAction SilentlyContinue
if ($sqlService -and $sqlService.Status -eq "Running") {
    Write-Host "   ✅ SQL Server está corriendo" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  SQL Server no está corriendo" -ForegroundColor Yellow
    $response = Read-Host "   ¿Deseas intentar iniciarlo? (S/N)"
    if ($response -eq "S" -or $response -eq "s") {
        Start-Service -Name MSSQLSERVER
        Write-Host "   ✅ SQL Server iniciado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Continuando sin SQL Server (algunas funciones no estarán disponibles)" -ForegroundColor Yellow
    }
}

# Verificar base de datos inicializada
Write-Host ""
Write-Host "3️⃣ Verificando base de datos..." -ForegroundColor Yellow
Write-Host "   💡 Si es la primera vez, ejecuta: python src/database/init_db.py" -ForegroundColor Cyan

# Iniciar el sistema
Write-Host ""
Write-Host "4️⃣ Iniciando servidor..." -ForegroundColor Yellow
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🌐 El sistema estará disponible en:" -ForegroundColor Green
Write-Host "   • API:        http://localhost:8000" -ForegroundColor White
Write-Host "   • Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • Dashboard:  http://localhost:8000/static/index.html" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""

# Ejecutar el sistema
python main.py
