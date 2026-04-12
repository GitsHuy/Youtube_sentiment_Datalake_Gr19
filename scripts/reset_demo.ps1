param(
    [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"

Write-Host "Stopping project containers..."
docker compose down

if ($RemoveVolumes) {
    Write-Host "Removing project volumes..."
    docker compose down -v
}

Write-Host "Project reset completed."
