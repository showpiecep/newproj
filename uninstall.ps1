$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "newproj uninstaller: uv is required: https://docs.astral.sh/uv/"
}

uv tool uninstall newproj
if ($LASTEXITCODE -ne 0) {
    throw "newproj uninstaller: uv tool uninstall failed with exit code $LASTEXITCODE"
}
