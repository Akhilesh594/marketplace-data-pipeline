param([string]$PythonCommand = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Executable (exit $LASTEXITCODE)" }
}
Invoke-Checked $PythonCommand @('-c', 'import sys; assert sys.version_info[:2] == (3,11), "Use Python 3.11"')
$environments = @(
    @{ Name = '.venv'; Requirements = 'requirements-dbt.txt' },
    @{ Name = '.venv-dagster'; Requirements = 'orchestration/requirements.txt' },
    @{ Name = '.venv-feast'; Requirements = 'requirements-feast.txt' }
)
foreach ($environment in $environments) {
    Invoke-Checked $PythonCommand @('-m', 'venv', $environment.Name)
    $environmentPython = Join-Path $projectRoot ($environment.Name + '/Scripts/python.exe')
    Invoke-Checked $environmentPython @('-m', 'pip', 'install', '-r', $environment.Requirements)
    Invoke-Checked $environmentPython @('-m', 'pip', 'check')
}
Write-Output 'Environments installed. Configure credentials and external services using docs/SETUP.md.'
