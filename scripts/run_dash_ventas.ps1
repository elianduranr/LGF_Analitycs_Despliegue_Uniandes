$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

$env:PYTHONPATH = "src;."

$DefaultDataPath = "C:\Proyectos_gaitana\Proyecto_despliegue\bases de datos historicas\historic_sales_acum.csv"
$DataPath = if ($env:LGF_DATA_PATH) { $env:LGF_DATA_PATH } else { $DefaultDataPath }
$HostName = if ($env:LGF_DASH_HOST) { $env:LGF_DASH_HOST } else { "127.0.0.1" }
$Port = if ($env:LGF_DASH_PORT) { $env:LGF_DASH_PORT } else { "8052" }
$Python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

if (-not (Test-Path $DataPath)) {
    Write-Host "No encontre el acumulado en: $DataPath"
    Write-Host "Define LGF_DATA_PATH con la ruta a historic_sales_acum.csv y vuelve a correr."
    exit 1
}

& $Python app\dash_ventas.py --data-path $DataPath --host $HostName --port $Port
