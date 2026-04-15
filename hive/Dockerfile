FROM apache/hive:3.1.3

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && curl -fsSL -o /opt/hive/lib/mssql-jdbc-12.6.1.jre8.jar https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.6.1.jre8/mssql-jdbc-12.6.1.jre8.jar \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY conf/hive-site.xml.template /opt/hive/conf/hive-site.xml.template
COPY scripts/start-metastore.sh /opt/hive/scripts/start-metastore.sh

RUN chmod +x /opt/hive/scripts/start-metastore.sh

ENTRYPOINT ["/opt/hive/scripts/start-metastore.sh"]
