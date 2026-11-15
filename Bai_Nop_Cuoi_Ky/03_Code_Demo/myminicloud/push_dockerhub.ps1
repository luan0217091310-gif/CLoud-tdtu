param(
    [Parameter(Mandatory=$true, HelpMessage="Nhập username Docker Hub của bạn (VD: phunghuuluan)")]
    [string]$DockerHubUser
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$env:DOCKERHUB_USER = $DockerHubUser

# Lưu DOCKERHUB_USER vào .env để docker-compose.yml tự động nhận
python setup_demo.py --student-id 524H0167
$envContent = Get-Content .env | Where-Object { $_ -notmatch '^DOCKERHUB_USER=' }
$envContent + "DOCKERHUB_USER=$DockerHubUser" | Set-Content -Encoding UTF8 .env

Write-Host "1. Đang build 3 custom images (web, web2, app)..." -ForegroundColor Cyan
docker compose build web-frontend-server web-frontend-server2 application-backend-server

Write-Host "2. Đăng nhập Docker Hub với tài khoản: $DockerHubUser" -ForegroundColor Cyan
docker login -u $DockerHubUser

$repos = @("myminicloud-web", "myminicloud-web2", "myminicloud-app")
foreach ($repo in $repos) {
    $image = "${DockerHubUser}/${repo}:demo"
    Write-Host "3. Đang push $image lên Docker Hub..." -ForegroundColor Green
    docker push $image
    Write-Host "   -> Link: https://hub.docker.com/r/$DockerHubUser/$repo" -ForegroundColor Yellow
}

Write-Host "`nHoàn tất push cả 3 images lên Docker Hub và cập nhật .env!" -ForegroundColor Green

