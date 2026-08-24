$ErrorActionPreference = "Stop"

$defaultSource = "https://github.com/showpiecep/newproj/releases/latest/download/newproj-templates.tar.gz"
$source = if ($env:NEWPROJ_SOURCE) { $env:NEWPROJ_SOURCE } else { $defaultSource }

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "newproj installer: uv is required: https://docs.astral.sh/uv/"
}

uv tool install --force $source
if ($LASTEXITCODE -ne 0) {
    throw "newproj installer: uv tool install failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "newproj installed successfully."
Write-Host "If the command is not in PATH yet, run: uv tool update-shell"
Write-Host "Then open a new terminal and run: newproj"
