param(
    [string]$Query,
    [string]$FilePath,
    [string]$JdbcUrl = "jdbc:hive2://localhost:10000/lakehouse;auth=noSasl;transportMode=binary;socketTimeout=30",
    [string]$DriverJar = "drivers/hive-jdbc-2.3.9-standalone.jar",
    [int]$LoginTimeoutSeconds = 20,
    [int]$QueryTimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$driverJarPath = Join-Path $repoRoot $DriverJar
if (-not (Test-Path $driverJarPath)) {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "download_hive_jdbc.ps1")
}

if (-not (Test-Path $driverJarPath)) {
    throw "Khong tim thay JDBC driver tai $driverJarPath"
}

if ([string]::IsNullOrWhiteSpace($Query) -and [string]::IsNullOrWhiteSpace($FilePath)) {
    throw "Can cung cap -Query hoac -FilePath"
}

$tempDir = Join-Path $env:TEMP "HiveJdbcRunner"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

$sqlFilePath = if (-not [string]::IsNullOrWhiteSpace($FilePath)) {
    Resolve-Path $FilePath | Select-Object -ExpandProperty Path
} else {
    $generatedSqlPath = Join-Path $tempDir "query.sql"
    Set-Content -LiteralPath $generatedSqlPath -Value $Query -Encoding Ascii
    $generatedSqlPath
}

$javaFilePath = Join-Path $tempDir "HiveJdbcQueryRunner.java"
$className = "HiveJdbcQueryRunner"

@'
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class HiveJdbcQueryRunner {
    private static List<String> splitStatements(String sqlText) {
        List<String> statements = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        for (String line : sqlText.split("\\R")) {
            String trimmed = line.trim();
            if (trimmed.startsWith("--")) {
                continue;
            }
            current.append(line).append('\n');
            if (trimmed.endsWith(";")) {
                String statement = current.toString().trim();
                if (statement.endsWith(";")) {
                    statement = statement.substring(0, statement.length() - 1).trim();
                }
                if (!statement.isEmpty()) {
                    statements.add(statement);
                }
                current.setLength(0);
            }
        }
        String tail = current.toString().trim();
        if (!tail.isEmpty()) {
            statements.add(tail);
        }
        return statements;
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 4) {
            throw new IllegalArgumentException("Expected args: <jdbcUrl> <sqlFilePath> <loginTimeoutSeconds> <queryTimeoutSeconds>");
        }

        String jdbcUrl = args[0];
        String sqlFilePath = args[1];
        int loginTimeoutSeconds = Integer.parseInt(args[2]);
        int queryTimeoutSeconds = Integer.parseInt(args[3]);

        Class.forName("org.apache.hive.jdbc.HiveDriver");
        DriverManager.setLoginTimeout(loginTimeoutSeconds);

        String sqlText = Files.readString(Paths.get(sqlFilePath), StandardCharsets.UTF_8);
        List<String> statements = splitStatements(sqlText);

        try (Connection connection = DriverManager.getConnection(jdbcUrl, "", "");
             Statement statement = connection.createStatement()) {
            statement.setQueryTimeout(queryTimeoutSeconds);

            for (String sql : statements) {
                System.out.println("SQL> " + sql.replaceAll("\\s+", " ").trim());
                boolean hasResultSet = statement.execute(sql);
                if (!hasResultSet) {
                    System.out.println("UPDATED_ROWS=" + statement.getUpdateCount());
                    continue;
                }

                try (ResultSet rs = statement.getResultSet()) {
                    ResultSetMetaData metaData = rs.getMetaData();
                    int columnCount = metaData.getColumnCount();
                    int rowCount = 0;
                    while (rs.next()) {
                        rowCount += 1;
                        StringBuilder row = new StringBuilder();
                        for (int i = 1; i <= columnCount; i++) {
                            if (i > 1) {
                                row.append(" | ");
                            }
                            row.append(metaData.getColumnLabel(i)).append("=").append(rs.getString(i));
                        }
                        System.out.println(row.toString());
                    }
                    System.out.println("ROW_COUNT=" + rowCount);
                }
            }
        }
    }
}
'@ | Set-Content -LiteralPath $javaFilePath -Encoding Ascii

$javacArgs = @("-cp", $driverJarPath, "-d", $tempDir, $javaFilePath)
& javac @javacArgs
if ($LASTEXITCODE -ne 0) {
    throw "javac compile that bai"
}

$javaArgs = @(
    "-cp",
    "$driverJarPath;$tempDir",
    $className,
    $JdbcUrl,
    $sqlFilePath,
    $LoginTimeoutSeconds,
    $QueryTimeoutSeconds
)

& java @javaArgs
if ($LASTEXITCODE -ne 0) {
    throw "Thuc thi JDBC query that bai"
}
