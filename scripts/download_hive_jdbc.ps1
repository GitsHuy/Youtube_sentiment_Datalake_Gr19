param(
    [string]$Version = "2.3.9",
    [string]$OutputDir = "drivers"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $repoRoot $OutputDir
$jarName = "hive-jdbc-$Version-standalone.jar"
$jarPath = Join-Path $targetDir $jarName
$url = "https://repo.maven.apache.org/maven2/org/apache/hive/hive-jdbc/$Version/$jarName"

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

if ((Test-Path $jarPath) -and ((Get-Item $jarPath).Length -lt 1MB)) {
    Remove-Item $jarPath -Force
}

if (-not (Test-Path $jarPath)) {
    Write-Host "Downloading $jarName ..."
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $jarPath
} else {
    Write-Host "$jarName already exists."
}

Write-Host "Saved to: $jarPath"
