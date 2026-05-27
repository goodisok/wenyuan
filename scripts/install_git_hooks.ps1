# Install prepare-commit-msg hook to strip Cursor co-author trailers.
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$root\.git")) {
    Write-Error "Not a git repository: $root"
    exit 1
}
$hookDir = Join-Path $root ".git\hooks"
New-Item -ItemType Directory -Force -Path $hookDir | Out-Null
$hookPath = Join-Path $hookDir "prepare-commit-msg"
$hook = "#!/bin/sh`npython `"`$(git rev-parse --show-toplevel)/scripts/git/strip_cursor_coauthor.py`" `"`$1`"`n"
[System.IO.File]::WriteAllText($hookPath, $hook)
Write-Host "Installed prepare-commit-msg hook."
