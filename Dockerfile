
FROM python:3.10-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y gcc libpq-dev libffi-dev curl

# Installer drivers pour Cassandra, MongoDB, Neo4j
##RUN pip install psycopg2-binary pymongo cassandra-driver neo4j
RUN pip install psycopg2-binary pymongo cassandra-driver neo4j fastapi uvicorn python-jose python-multipart

# Copier le script principal
COPY create_4_databases_complete.py .
COPY api_v1_crud_full.py .
COPY export_to_datalake.py .
CMD ["sh", "-c", "python create_4_databases_complete.py && uvicorn api_v1_crud_full:app --host 0.0.0.0 --port 8000 && python export_to_datalake.py"]
##CMD ["uvicorn", "api_v1_crud_full:app", "--host", "0.0.0.0", "--port", "8000"]

