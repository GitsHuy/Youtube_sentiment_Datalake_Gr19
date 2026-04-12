#!/bin/bash
set -euo pipefail

HIVE_SITE_TEMPLATE="/opt/hive/conf/hive-site.xml.template"
HIVE_SITE_FILE="/opt/hive/conf/hive-site.xml"
SQLSERVER_JDBC_JAR="/opt/hive/lib/mssql-jdbc-12.6.1.jre8.jar"

cp "${HIVE_SITE_TEMPLATE}" "${HIVE_SITE_FILE}"

sed -i "s|__SQLSERVER_HOST__|${SQLSERVER_HOST}|g" "${HIVE_SITE_FILE}"
sed -i "s|__SQLSERVER_PORT__|${SQLSERVER_PORT}|g" "${HIVE_SITE_FILE}"
sed -i "s|__SQLSERVER_DATABASE__|${SQLSERVER_DATABASE}|g" "${HIVE_SITE_FILE}"
sed -i "s|__SQLSERVER_USERNAME__|${SQLSERVER_USERNAME}|g" "${HIVE_SITE_FILE}"
sed -i "s|__SQLSERVER_PASSWORD__|${SQLSERVER_PASSWORD}|g" "${HIVE_SITE_FILE}"
sed -i "s|__METASTORE_THRIFT_PORT__|${METASTORE_THRIFT_PORT}|g" "${HIVE_SITE_FILE}"
sed -i "s|__METASTORE_WAREHOUSE_DIR__|${METASTORE_WAREHOUSE_DIR}|g" "${HIVE_SITE_FILE}"

export HIVE_AUX_JARS_PATH="${SQLSERVER_JDBC_JAR}"
export HADOOP_CLASSPATH="${SQLSERVER_JDBC_JAR}:${HADOOP_CLASSPATH:-}"

echo "Waiting for HDFS..."
until hdfs dfs -ls / >/dev/null 2>&1; do
  sleep 3
done

echo "Initializing Hive metastore schema if needed..."
if ! /opt/hive/bin/schematool -dbType mssql -info >/dev/null 2>&1; then
  /opt/hive/bin/schematool -dbType mssql -initSchema --verbose || true
fi

echo "Starting Hive Metastore on port ${METASTORE_THRIFT_PORT}..."
exec /opt/hive/bin/hive --service metastore -p "${METASTORE_THRIFT_PORT}"
