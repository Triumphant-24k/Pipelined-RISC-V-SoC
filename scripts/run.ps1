param([ValidateSet('all','test','baseline','arch','check','compare','models')][string]$Target='all')
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxPath=(& wsl -d Ubuntu-22.04 -- wslpath -a $projectRoot).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the project path in WSL' }
if ($linuxPath.Contains("'")) { throw 'A single quote in the project path is unsupported by this wrapper' }
& wsl -d Ubuntu-22.04 -- bash -lc "cd '$linuxPath' && make $Target"
if ($LASTEXITCODE -ne 0) { throw "Regression target $Target failed" }
