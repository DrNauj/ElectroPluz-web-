# Script de arranque para ElectroPlus
# Inicia todos los microservicios y el gateway

# Configurar codificación UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

$ErrorActionPreference = "Stop"

# Verificar requisitos previos
function Test-Requirements {
    try {
        $pythonVersion = python --version 2>&1
        if (-not $?) {
            Write-Host "ERROR: Python no está instalado o no está en el PATH" -ForegroundColor Red
            exit 1
        }
        Write-Host "Python detectado: $pythonVersion" -ForegroundColor Green
        
        $pipVersion = pip --version 2>&1
        if (-not $?) {
            Write-Host "ERROR: pip no está instalado" -ForegroundColor Red
            exit 1
        }
        Write-Host "pip detectado: $pipVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: No se pudieron verificar los requisitos" -ForegroundColor Red
        exit 1
    }
}

# Función para esperar que un servicio esté disponible
function Wait-ServiceReady {
    param(
        $serviceName,
        $url,
        $maxAttempts = 30,
        $waitSeconds = 2
    )
    Write-Host "Esperando que $serviceName esté listo..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "$url/health/" -Method GET -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Host "$serviceName está listo!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Host "Intento $i de $maxAttempts..." -ForegroundColor Yellow
            Start-Sleep -Seconds $waitSeconds
        }
    }
    
    Write-Host "ERROR: $serviceName no respondió después de $($maxAttempts * $waitSeconds) segundos" -ForegroundColor Red
    return $false
}

Write-Host "Verificando requisitos del sistema..." -ForegroundColor Cyan
Test-Requirements

# Función para limpiar procesos existentes en puertos
function Clear-UsedPorts {
    param(
        [int[]]$ports
    )
    Write-Host "Verificando y limpiando puertos en uso..." -ForegroundColor Yellow
    foreach ($port in $ports) {
        $processInfo = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
                      Select-Object -ExpandProperty OwningProcess
        if ($processInfo) {
            Write-Host "Puerto $port en uso. Terminando proceso..." -ForegroundColor Yellow
            Stop-Process -Id $processInfo -Force
            Start-Sleep -Seconds 1
        }
    }
}

Write-Host "Iniciando servicios de ElectroPlus..." -ForegroundColor Green

# Cargar variables de entorno desde .env
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
}

# Obtener puertos desde variables de entorno o usar valores por defecto
$GATEWAY_PORT = if ([Environment]::GetEnvironmentVariable("GATEWAY_PORT")) { 
    [Environment]::GetEnvironmentVariable("GATEWAY_PORT") 
} else { 
    8000 
}
$INVENTARIO_PORT = if ([Environment]::GetEnvironmentVariable("INVENTARIO_PORT")) { 
    [Environment]::GetEnvironmentVariable("INVENTARIO_PORT") 
} else { 
    8001 
}
$VENTAS_PORT = if ([Environment]::GetEnvironmentVariable("VENTAS_PORT")) { 
    [Environment]::GetEnvironmentVariable("VENTAS_PORT") 
} else { 
    8002 
}

# Función para verificar si un puerto está en uso
function Test-PortInUse {
    param($port)
    $portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    return $null -ne $portInUse
}

# Función para iniciar un servicio Django
function Start-DjangoService {
    param(
        $serviceName,
        $path,
        $port,
        $secretKeyVar
    )
    
    Write-Host "Iniciando $serviceName en puerto $port..." -ForegroundColor Cyan
    
    if (Test-PortInUse $port) {
        Write-Host "ERROR: Puerto $port ya está en uso!" -ForegroundColor Red
        return $false
    }
    
    Set-Location $path

    # Crear archivo .env específico para el servicio
    $envContent = @"
DEBUG=$(if ([Environment]::GetEnvironmentVariable("DEBUG")) { [Environment]::GetEnvironmentVariable("DEBUG") } else { "True" })
SECRET_KEY=$([Environment]::GetEnvironmentVariable($secretKeyVar))
ALLOWED_HOSTS=$(if ([Environment]::GetEnvironmentVariable("ALLOWED_HOSTS")) { [Environment]::GetEnvironmentVariable("ALLOWED_HOSTS") } else { "localhost,127.0.0.1" })

# Base de datos MySQL
MYSQL_HOST=$([Environment]::GetEnvironmentVariable("MYSQL_HOST"))
MYSQL_USER=$([Environment]::GetEnvironmentVariable("MYSQL_USER"))
MYSQL_PASSWORD=$([Environment]::GetEnvironmentVariable("MYSQL_PASSWORD"))
MYSQL_DATABASE=$([Environment]::GetEnvironmentVariable("MYSQL_DATABASE"))
MYSQL_PORT=$([Environment]::GetEnvironmentVariable("MYSQL_PORT"))

# API Keys y URLs de servicios
INVENTARIO_API_KEY=$([Environment]::GetEnvironmentVariable("INVENTARIO_API_KEY"))
VENTAS_API_KEY=$([Environment]::GetEnvironmentVariable("VENTAS_API_KEY"))
INVENTARIO_URL=$([Environment]::GetEnvironmentVariable("INVENTARIO_URL"))
VENTAS_URL=$([Environment]::GetEnvironmentVariable("VENTAS_URL"))
"@
    
    Set-Content -Path ".env" -Value $envContent -Force
    Write-Host "Archivo .env creado para $serviceName" -ForegroundColor Green
    
    # Activar entorno virtual si existe
    if (Test-Path "venv\Scripts\activate.ps1") {
        . .\venv\Scripts\activate.ps1
    }
    
    # Instalar dependencias
    python -m pip install -r requirements.txt
    
    # Aplicar migraciones
    python manage.py migrate
    
    # Iniciar servidor
    Start-Process python -ArgumentList "manage.py runserver 0.0.0.0:$port" -WindowStyle Hidden
    
    Write-Host "$serviceName iniciado en http://localhost:$port" -ForegroundColor Green
    return $true
}

# Directorio base
$BASE_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Limpiar puertos antes de iniciar
Clear-UsedPorts -ports @($GATEWAY_PORT, $INVENTARIO_PORT, $VENTAS_PORT)

# Verificar el estado del entorno virtual
$venvPath = Join-Path $BASE_DIR "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    . $venvPath\Scripts\activate.ps1
    python -m pip install --upgrade pip
} else {
    . $venvPath\Scripts\activate.ps1
}

# Iniciar M-Inventario
$inventarioPath = Join-Path $BASE_DIR "ElectroPlus-M-Inventario"
if (-not (Start-DjangoService -serviceName "M-Inventario" -path $inventarioPath -port $INVENTARIO_PORT -secretKeyVar "INVENTARIO_SECRET_KEY")) {
    exit 1
}

# Iniciar M-Ventas
$ventasPath = Join-Path $BASE_DIR "ElectroPlus-M-Ventas"
if (-not (Start-DjangoService -serviceName "M-Ventas" -path $ventasPath -port $VENTAS_PORT -secretKeyVar "VENTAS_SECRET_KEY")) {
    exit 1
}

# Iniciar Gateway
$gatewayPath = Join-Path $BASE_DIR "ElectroPlus-Gateway"
if (-not (Start-DjangoService -serviceName "Gateway" -path $gatewayPath -port $GATEWAY_PORT -secretKeyVar "GATEWAY_SECRET_KEY")) {
    exit 1
}

Write-Host "`nTodos los servicios están en ejecución:" -ForegroundColor Green
Write-Host "Gateway: http://localhost:$GATEWAY_PORT"
Write-Host "M-Inventario: http://localhost:$INVENTARIO_PORT"
Write-Host "M-Ventas: http://localhost:$VENTAS_PORT"

# Ejecutar pruebas de integración
Write-Host "`nEjecutando pruebas de integración..." -ForegroundColor Cyan
Set-Location $gatewayPath
# Esperamos unos segundos para asegurar que los servicios estén listos
Start-Sleep -Seconds 5
# Ejecutar las pruebas del directorio de integración específicamente
python manage.py test gateway_app.tests.integration.test_microservices --verbosity=2

# Verificar estado de los servicios
function Test-ServiceHealth {
    param($name, $url)
    try {
        $response = Invoke-WebRequest -Uri "$url/health/" -Method GET -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "${name} - Estado: OK" -ForegroundColor Green
        } else {
            Write-Host "${name} - Error (Status: $($response.StatusCode))" -ForegroundColor Red
        }
    } catch {
        Write-Host "${name} - Error de conexión" -ForegroundColor Red
    }
}

Write-Host "`nVerificando estado de los servicios:" -ForegroundColor Cyan
Test-ServiceHealth -name "Gateway" -url "http://localhost:$GATEWAY_PORT"
Test-ServiceHealth -name "M-Inventario" -url "http://localhost:$INVENTARIO_PORT"
Test-ServiceHealth -name "M-Ventas" -url "http://localhost:$VENTAS_PORT"

Write-Host "`nPresione Ctrl+C para detener todos los servicios" -ForegroundColor Yellow

# Mantener el script en ejecución
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Limpiar al salir
    Get-Process | Where-Object {$_.Name -eq 'python' -and $_.CommandLine -like '*runserver*'} | Stop-Process
    Write-Host "`nServicios detenidos." -ForegroundColor Green
}