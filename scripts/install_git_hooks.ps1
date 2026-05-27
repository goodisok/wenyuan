# Install prepare-commit-msg hook to strip Cursor co-author trailers.
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$root\.git")) {
    Write-Error "Not a git repository: $root"
    exit 1
}
$hookDir = Join-Path $root ".git\hooks"
New-Item -ItemType Directory -Force -Path $hookDir | Out-Null
$hook = @"
#!/bin/sh
python "`$(git rev-parse --show-toplevel)/scripts/git/strip_cursor_coauthor.py" "`$1"
"@
Set-Content -Path (Join-Path $hookDir "prepare-commit-msg") -Value $hook -NoNewline -Encoding utf8
Write-Host "Installed prepare-commit-msg hook."
