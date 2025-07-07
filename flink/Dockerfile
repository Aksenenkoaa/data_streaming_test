FROM apache/flink:1.20.0

# Install Python and pip
USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev wget && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install PyFlink and dependencies
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Download the correct JAR files for Flink 1.20.0
# Kafka connector 3.3.0 (compatible with Flink 1.20.x)
RUN wget -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.19/flink-sql-connector-kafka-3.3.0-1.19.jar

# JDBC connector 3.3.0 (compatible with Flink 1.20.x)  
RUN wget -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.3.0-1.20/flink-connector-jdbc-3.3.0-1.20.jar

# PostgreSQL JDBC driver
RUN wget -P /opt/flink/lib https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar

USER flink 