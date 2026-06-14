# Comprehensive installer for cognis-digital/labforge (Windows PowerShell).
# pipx -> uv -> pip (git+https) -> source. Not on PyPI; installs from GitHub.
$ErrorActionPreference = "Stop"
$Repo = "labforge"
$Url  = "git+https://github.com/cognis-digital/labforge.git"
$Git  = "https://github.com/cognis-digital/labforge.git"
function Say($m) { Write-Host "[$Repo] $m" -ForegroundColor Magenta }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
if (-not (Have python) -and -not (Have py)) { Say "Python 3.9+ required but not found."; exit 1 }
if (Have pipx) { Say "pipx install..."; pipx install $Url; if ($LASTEXITCODE -eq 0) { Say "Done. Run: labforge --help"; exit 0 } }
if (Have uv) { Say "uv install..."; uv tool install $Url; if ($LASTEXITCODE -eq 0) { Say "Done. Run: labforge --help"; exit 0 } }
if (Have pip) { Say "pip install..."; pip install --user $Url; if ($LASTEXITCODE -eq 0) { Say "Done. Run: labforge --help"; exit 0 } }
Say "Falling back to a source clone."
$Tmp = Join-Path $env:TEMP "$Repo-src"; git clone --depth 1 $Git $Tmp
Say "Cloned to $Tmp - run: cd $Tmp; python -m pip install ."
