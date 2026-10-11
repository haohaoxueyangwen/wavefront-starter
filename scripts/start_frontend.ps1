param([ValidateSet('speckle','grating','hartmann','wavefront')][string]$App='speckle')
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeFile = Join-Path $projectRoot '.local_runtime.json'
if (Test-Path -LiteralPath $runtimeFile) {
    $runtimeConfig = Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
    $runtimePython = $runtimeConfig.python
} elseif (Test-Path -LiteralPath (Join-Path $projectRoot '.venv\Scripts\python.exe')) {
    $runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
} else {
    $runtimePython = (Get-Command python -ErrorAction Stop).Source
}
& $runtimePython -B (Join-Path $projectRoot 'launch_frontend.py') --app $App
if ($LASTEXITCODE -ne 0) { throw 'Frontend launch failed.' }
