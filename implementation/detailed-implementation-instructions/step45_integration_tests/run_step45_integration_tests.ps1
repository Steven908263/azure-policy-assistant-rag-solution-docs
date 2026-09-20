param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

Write-Host "I-28 Step 45 Cosmos integration-test runner"
Write-Host "Project: $PWD"
Write-Host ""
Write-Host "These tests use the REAL development Cosmos memories container."
Write-Host "Temporary records are uniquely named and cleaned up after each test."
Write-Host ""

$env:RUN_COSMOS_INTEGRATION_TESTS = "true"

if ($VerboseOutput) {
    python -m pytest -c pytest-integration.ini tests/integration -m integration -v -s
}
else {
    python -m pytest -c pytest-integration.ini tests/integration -m integration -v
}

if ($LASTEXITCODE -ne 0) {
    throw "Step 45 integration tests failed."
}

Write-Host ""
Write-Host "Step 45 integration tests PASSED."
