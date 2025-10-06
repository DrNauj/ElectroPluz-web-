# Script de arranque para ElectroPlus
# Inicia todos los microservicios y el gateway

$ErrorActionPreference = "Stop"

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