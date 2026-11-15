$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Host "Đang đẩy cả 2 nhánh (main và hoan-thien-nop-bai) lên GitHub..." -ForegroundColor Cyan
Write-Host "(Nếu cửa sổ đăng nhập GitHub hiện lên, bạn bấm 'Sign in with your browser' để xác nhận nhé!)" -ForegroundColor Yellow

git branch -f main hoan-thien-nop-bai
git push origin hoan-thien-nop-bai main --force

Write-Host "`nĐã push thành công lên cả nhánh 'main' (nhánh chính) và 'hoan-thien-nop-bai'!" -ForegroundColor Green
Write-Host "Link kiểm tra: https://github.com/luan0217091310-gif/CLoud-tdtu" -ForegroundColor Green
