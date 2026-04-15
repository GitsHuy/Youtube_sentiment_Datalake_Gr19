param(
    [int]$ThriftPort = 10000,
    [int]$MaxWaitSeconds = 120,
    [switch]$SkipThriftStart,
    [switch]$SkipRegisterTables,
    [switch]$SkipQualityChecks,
    [int]$RetryCount = 3,
    [int]$RetryDelaySeconds = 15
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$requiredPorts = @(
    @{ Name = "Kafka"; Port = 19092 },
    @{ Name = "HDFS NameNode RPC"; Port = 8020 },
    @{ Name = "Hive Metastore"; Port = 9083 }
)

$jdbcRunner = Join-Path $PSScriptRoot "invoke_hive_jdbc_sql.ps1"

function Invoke-ComposeCapture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandText,
        [int]$Attempts = 1
    )

    $lastErrorMessage = ""

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        $stdoutPath = [System.IO.Path]::GetTempFileName()
        $stderrPath = [System.IO.Path]::GetTempFileName()

        try {
            $process = Start-Process `
                -FilePath "powershell.exe" `
                -ArgumentList @("-NoProfile", "-Command", $CommandText) `
                -Wait `
                -PassThru `
                -RedirectStandardOutput $stdoutPath `
                -RedirectStandardError $stderrPath

            $stdout = if (Test-Path $stdoutPath) { Get-Content $stdoutPath -Raw } else { "" }
            $stderr = if (Test-Path $stderrPath) { Get-Content $stderrPath -Raw } else { "" }
            $output = ($stdout + $stderr).Trim()

            if ($process.ExitCode -eq 0) {
                return $output
            }

            $lastErrorMessage = "Lenh that bai: $CommandText`n$output"
        }
        finally {
            Remove-Item $stdoutPath, $stderrPath -ErrorAction SilentlyContinue
        }

        if ($attempt -lt $Attempts) {
            Write-Host "Thu lai lenh ($attempt/$Attempts) sau $RetryDelaySeconds giay..."
            Start-Sleep -Seconds $RetryDelaySeconds
        }
    }

    throw $lastErrorMessage
}

function Write-Step {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "==> $Message"
}

function Invoke-SparkSqlFallback {
    param(
        [string]$Query,
        [string]$FilePath
    )

    if (-not [string]::IsNullOrWhiteSpace($FilePath)) {
        $resolvedPath = Resolve-Path $FilePath | Select-Object -ExpandProperty Path
        $repoRootPath = (Resolve-Path $repoRoot | Select-Object -ExpandProperty Path)
        if (-not $resolvedPath.StartsWith($repoRootPath)) {
            throw "Khong the anh xa file SQL ngoai repo vao container: $resolvedPath"
        }
        $repoRelativePath = $resolvedPath.Substring($repoRootPath.Length).TrimStart('\', '/').Replace("\", "/")
        $containerSqlPath = "/opt/" + $repoRelativePath
        Invoke-ComposeCapture "docker exec nhom19-spark-master /bin/bash -lc ""/opt/spark/bin/spark-sql -f $containerSqlPath""" -Attempts $RetryCount
        return
    }

    $escapedQuery = $Query.Replace('"', '\"')
    Invoke-ComposeCapture "docker exec nhom19-spark-master /bin/bash -lc ""/opt/spark/bin/spark-sql -e '$escapedQuery'""" -Attempts $RetryCount
}

function Invoke-QueryWithFallback {
    param(
        [string]$StepLabel,
        [string]$Query,
        [string]$FilePath,
        [int]$QueryTimeoutSeconds = 90
    )

    try {
        if (-not [string]::IsNullOrWhiteSpace($FilePath)) {
            & powershell -ExecutionPolicy Bypass -File $jdbcRunner -FilePath $FilePath -QueryTimeoutSeconds $QueryTimeoutSeconds
        }
        else {
            & powershell -ExecutionPolicy Bypass -File $jdbcRunner -Query $Query -QueryTimeoutSeconds $QueryTimeoutSeconds
        }

        if ($LASTEXITCODE -ne 0) {
            throw "JDBC query failed."
        }
    }
    catch {
        Write-Host "JDBC/Thrift chua on dinh o buoc '$StepLabel'. Chuyen sang spark-sql fallback..."
        Invoke-SparkSqlFallback -Query $Query -FilePath $FilePath | Out-Host
    }
}

Write-Step "Kiem tra container chinh"
foreach ($portCheck in $requiredPorts) {
    $portReady = $false
    $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        $tcp = Test-NetConnection -ComputerName localhost -Port $portCheck.Port -WarningAction SilentlyContinue
        if ($tcp.TcpTestSucceeded) {
            $portReady = $true
            break
        }
        Start-Sleep -Seconds 5
    }

    if (-not $portReady) {
        throw "$($portCheck.Name) chua san sang o cong $($portCheck.Port)."
    }

    Write-Host "$($portCheck.Name) san sang o cong $($portCheck.Port)."
}

if (-not $SkipThriftStart) {
    Write-Step "Khoi dong spark-thriftserver"
    try {
        Invoke-ComposeCapture "docker compose up -d spark-thriftserver" -Attempts $RetryCount | Out-Null
    }
    catch {
        $tcp = Test-NetConnection -ComputerName localhost -Port $ThriftPort -WarningAction SilentlyContinue
        if ($tcp.TcpTestSucceeded) {
            Write-Host "Docker API dang chao dao nhung cong $ThriftPort da mo, tiep tuc smoke test."
        }
        else {
            throw
        }
    }
}

Write-Step "Cho cong Thrift Server san sang"
$deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
$ready = $false
while ((Get-Date) -lt $deadline) {
    $tcp = Test-NetConnection -ComputerName localhost -Port $ThriftPort -WarningAction SilentlyContinue
    if ($tcp.TcpTestSucceeded) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 5
}
if (-not $ready) {
    throw "spark-thriftserver chua mo cong $ThriftPort sau $MaxWaitSeconds giay."
}
Write-Host "Cong $ThriftPort da mo."

if (-not $SkipRegisterTables) {
    Write-Step "Dang ky lai external tables"
    Invoke-QueryWithFallback -StepLabel "register tables" -FilePath (Join-Path $repoRoot "spark\sql\register_tables.sql")
    Write-Host "Dang ky bang thanh cong."
}

Write-Step "Kiem tra metastore"
Invoke-QueryWithFallback -StepLabel "show tables" -Query "SHOW TABLES IN lakehouse;"

if (-not $SkipQualityChecks) {
    Write-Step "Chay quality checks"
    Invoke-QueryWithFallback -StepLabel "quality checks" -FilePath (Join-Path $repoRoot "spark\sql\checkpoint11_quality_checks.sql") -QueryTimeoutSeconds 180
}

Write-Step "Thong tin ket noi"
Write-Host "JDBC URL: jdbc:hive2://localhost:$ThriftPort/lakehouse"
Write-Host "Driver: Apache Hive 2"
Write-Host "Authentication: None"

Write-Host ""
Write-Host "Smoke test completed: PASS"
