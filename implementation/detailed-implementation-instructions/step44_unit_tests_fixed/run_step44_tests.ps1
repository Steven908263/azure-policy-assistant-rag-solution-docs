param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"

Write-Host "I-28 Step 44 unit-test runner"
Write-Host "Project: $PWD"

if ($Install) {
    python -m pip install -r requirements-dev.txt
}

python -m pytest

if ($LASTEXITCODE -ne 0) {
    throw "Step 44 unit tests failed."
}

Write-Host "Step 44 unit tests PASSED."
