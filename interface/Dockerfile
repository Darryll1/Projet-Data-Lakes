FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev

# Copier le script
COPY . /app

# Installer dépendances Python
RUN pip install streamlit pandas psycopg2-binary minio boto3 pymongo cassandra-driver neo4j sqlalchemy

# Démarrer Streamlit
CMD ["streamlit", "run", "Interface3.py", "--server.port=8501", "--server.address=0.0.0.0"]
