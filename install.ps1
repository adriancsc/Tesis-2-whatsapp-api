# Script de Instalación Automática - Sistema MAS-CIS
# Este script instala todas las dependencias necesarias

Write-Host "🚀 Instalando Sistema MAS-CIS..." -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "1️⃣ Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python no encontrado. Por favor instala Python 3.10+" -ForegroundColor Red
    exit 1
}

# Instalar dependencias de Python
Write-Host ""
Write-Host "2️⃣ Instalando dependencias de Python..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Dependencias instaladas correctamente" -ForegroundColor Green
} else {
    Write-Host "   ❌ Error al instalar dependencias" -ForegroundColor Red
    exit 1
}

# Descargar modelo de spaCy
Write-Host ""
Write-Host "3️⃣ Descargando modelo de spaCy para español..." -ForegroundColor Yellow
python -m spacy download es_core_news_sm
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Modelo de spaCy descargado" -ForegroundColor Green
} else {
    Write-Host "   ❌ Error al descargar modelo de spaCy" -ForegroundColor Red
    exit 1
}

# Crear archivo .env si no existe
Write-Host ""
Write-Host "4️⃣ Configurando archivo .env..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "   ✅ Archivo .env creado desde .env.example" -ForegroundColor Green
    Write-Host "   ⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales de SQL Server" -ForegroundColor Magenta
} else {
    Write-Host "   ℹ️  Archivo .env ya existe, no se sobrescribirá" -ForegroundColor Cyan
}

# Verificar SQL Server
Write-Host ""
Write-Host "5️⃣ Verificando SQL Server..." -ForegroundColor Yellow
$sqlService = Get-Service -Name MSSQLSERVER -ErrorAction SilentlyContinue
if ($sqlService) {
    if ($sqlService.Status -eq "Running") {
        Write-Host "   ✅ SQL Server está corriendo" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  SQL Server está instalado pero no está corriendo" -ForegroundColor Yellow
        Write-Host "   💡 Intenta iniciarlo con: Start-Service -Name MSSQLSERVER" -ForegroundColor Cyan
    }
} else {
    Write-Host "   ⚠️  SQL Server no detectado o no está instalado" -ForegroundColor Yellow
    Write-Host "   💡 Asegúrate de tener SQL Server instalado y configurado" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Instalación completada!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
Write-Host "   1. Edita el archivo .env con tus credenciales de SQL Server"
Write-Host "   2. Ejecuta: python src/database/init_db.py"
Write-Host "   3. Ejecuta: python main.py"
Write-Host "   4. Abre: http://localhost:8000/docs"
Write-Host ""
Write-Host "📚 Para más información, consulta: guia_configuracion.md" -ForegroundColor Cyan
Write-Host ""
