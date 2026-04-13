param(
    [int]$Port = 10000,
    [int]$MaxWaitSeconds = 120
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Starting spark-thriftserver..."
docker compose up -d spark-thriftserver | Out-Null

$deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
$ready = $false

while ((Get-Date) -lt $deadline) {
    $tcp = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    if ($tcp.TcpTestSucceeded) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 5
}

if (-not $ready) {
    throw "spark-thriftserver chua mo cong $Port sau $MaxWaitSeconds giay."
}

Write-Host "Registering external tables..."
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql" | Out-Null

Write-Host "Checking metastore tables..."
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW TABLES IN lakehouse'" | Out-Null

Write-Host ""
Write-Host "TCP check:"
Test-NetConnection -ComputerName localhost -Port $Port

Write-Host ""
Write-Host "JDBC endpoint ready:"
Write-Host "  jdbc:hive2://localhost:$Port/lakehouse"

Write-Host ""
Write-Host "Recommended DBeaver settings:"
Write-Host "  Driver: Apache Hive 2"
Write-Host "  Host: localhost"
Write-Host "  Port: $Port"
Write-Host "  Database: lakehouse"
Write-Host "  Authentication: None"
Write-Host ""
Write-Host "Smoke test completed: port is open and metastore tables are visible from Spark SQL."
