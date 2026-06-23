# Gebruik een slanke Python 3.11 image op Debian-basis
FROM python:3.11-slim

# Installeer Java (OpenJDK 17 is klein en werkt prima met Tika)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Vertel Tika waar Java staat
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV TIKA_SERVER_JAR=/app/tika.jar

# Werkdirectory in de container
WORKDIR /app

# Kopieer requirements en installeer eerst (Docker layer cache profiteert hiervan)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de broncode + tika.jar
COPY . .

# Streamlit luistert standaard op poort 8501
EXPOSE 8501

# Zorg dat Streamlit ook buiten de container bereikbaar is
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Startcommando — pas 'app.py' aan als het entrypoint anders heet
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]