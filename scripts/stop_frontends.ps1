param([int]$Port=8790)
$projectRoot=(Split-Path -Parent $PSScriptRoot)
try { $session=Invoke-RestMethod "http://127.0.0.1:$Port/api/session" -TimeoutSec 3 }
catch { Write-Host '后台已经停止。'; exit 0 }
if ($session.application -ne 'wavefront-frontends') { throw '该端口不属于波前工具，不会停止。' }
if ($session.jobs | Where-Object { $_.status -in 'running','queued' }) { throw '有任务在运行，请先在前端停止任务。' }
# Session PID identifies this service, avoiding unrelated Python processes.
if (-not $session.pid) { throw '旧版后台不提供 PID。请关闭旧启动窗口；勿批量结束 Python 进程。' }
if ($session.application_root -ne $projectRoot) { throw '后台属于另一份目录，请使用那份目录的停止脚本。' }
Stop-Process -Id $session.pid -ErrorAction Stop
Write-Host '波前工具后台已停止；结果仍保留。'
