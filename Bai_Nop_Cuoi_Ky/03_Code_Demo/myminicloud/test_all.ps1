$ErrorActionPreference = "Stop"
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 (Join-Path $PSScriptRoot "test_all.py") @args
} else {
    & python (Join-Path $PSScriptRoot "test_all.py") @args
}
exit $LASTEXITCODE
