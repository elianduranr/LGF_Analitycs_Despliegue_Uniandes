$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

$env:PYTHONPATH = "src;."

$Python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$HostName = if ($env:LGF_DASH_HOST) { $env:LGF_DASH_HOST } else { "127.0.0.1" }
$VentasPort = if ($env:LGF_DASH_PORT) { $env:LGF_DASH_PORT } else { "8052" }
$ForecastPort = if ($env:LGF_FORECAST_DASH_PORT) { $env:LGF_FORECAST_DASH_PORT } else { "8053" }
$IntegratedPort = if ($env:LGF_INTEGRATED_DASH_PORT) { $env:LGF_INTEGRATED_DASH_PORT } else { "8050" }

function Test-Port {
    param([string]$Port)
    $connection = Get-NetTCPConnection -LocalPort ([int]$Port) -ErrorAction SilentlyContinue
    return $null -ne $connection
}

if (-not (Test-Port $VentasPort)) {
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\run_dash_ventas.ps1" `
        -WorkingDirectory $RootDir `
        -WindowStyle Hidden | Out-Null
}

if (-not (Test-Port $ForecastPort)) {
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\run_dash_forecast.ps1" `
        -WorkingDirectory $RootDir `
        -WindowStyle Hidden | Out-Null
}

Write-Host "Tablero integrado: http://$HostName`:$IntegratedPort"
Write-Host "Ventas generales: http://$HostName`:$VentasPort"
Write-Host "Forecast SOLIDO: http://$HostName`:$ForecastPort"
Write-Host "Espera unos segundos si ventas generales esta cargando el acumulado completo."

& $Python app\dashboard_integrado.py `
    --ventas-url "http://$HostName`:$VentasPort" `
    --forecast-url "http://$HostName`:$ForecastPort" `
    --host $HostName `
    --port $IntegratedPort
