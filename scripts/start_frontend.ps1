param([ValidateSet('speckle','grating','hartmann','wavefront')][string]$App='speckle',[int]$Port=8790,[switch]$NoBrowser)
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeFile = Join-Path $projectRoot '.local_runtime.json'
if (Test-Path -LiteralPath (Join-Path $projectRoot 'runtime\python\python.exe')) {
    $runtimePython = Join-Path $projectRoot 'runtime\python\python.exe'
} elseif (Test-Path -LiteralPath $runtimeFile) {
    $runtimeConfig = Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
    $runtimePython = $runtimeConfig.python
} elseif (Test-Path -LiteralPath (Join-Path $projectRoot '.venv\Scripts\python.exe')) {
    $runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
} else {
    throw '请下载 GitHub Release 中的 windows-x64.zip 完整包并解压；不要使用 GitHub 的 Source code ZIP。完整包已包含 Python 和 CPU/GPU 程序。'
}
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
$launchArgs=@('-B',(Join-Path $projectRoot 'launch_frontend.py'),'--app',$App,'--port',$Port)
if($NoBrowser){$launchArgs+='--no-browser'}
& $runtimePython @launchArgs
if ($LASTEXITCODE -ne 0) { throw 'Frontend launch failed.' }
