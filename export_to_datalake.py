# -*- coding: utf-8 -*-
import sys
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

import os
import boto3
import pandas as pd
import psycopg2
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase
from datetime import datetime
import json
import uuid

print("📤 Export vers Data Lake (MinIO)...")

# Connexion MinIO
s3 = boto3.client(
    's3',
    endpoint_url="http://localhost:9000",  # ou "http://minio:9000" dans Docker
    aws_access_key_id="admin",
    aws_secret_access_key="admin123",
    region_name="us-east-1"
)
bucket_name = "datalake"
try:
    s3.create_bucket(Bucket=bucket_name)
except:
    pass

# === PostgreSQL (structured) ===
conn = psycopg2.connect(host="localhost", dbname="smartcity", user="postgres", password="password", port=5432)
df_pg = pd.read_sql("SELECT * FROM mesures", conn)
csv_pg = "/tmp/postgres_mesures.csv"
df_pg.to_csv(csv_pg, index=False)
s3.upload_file(csv_pg, bucket_name, f"structured/postgres_mesures_{datetime.now().isoformat()}.csv")
print("✅ PostgreSQL exporté")

# === MongoDB (semi-structured) ===
mongo = MongoClient("mongodb://localhost:27017/")
docs = list(mongo.smartcity_documents.mesures.find({}, {"_id": 0}))
with open("/tmp/mongo_mesures.json", "w") as f:
    json.dump(docs, f)
s3.upload_file("/tmp/mongo_mesures.json", bucket_name, f"semi_structured/mongo_mesures_{datetime.now().isoformat()}.json")
print("✅ MongoDB exporté")

# === Cassandra (semi-structured) ===
cluster = Cluster(["127.0.0.1"], port=9042)
cass = cluster.connect("smartcity_columns")
rows = cass.execute("SELECT * FROM mesures")

def serialize_value(v):
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return v

cass_data = [{k: serialize_value(v) for k, v in row._asdict().items()} for row in rows]

with open("/tmp/cassandra_mesures.json", "w") as f:
    json.dump(cass_data, f, indent=2)

s3.upload_file("/tmp/cassandra_mesures.json", bucket_name, f"semi_structured/cassandra_mesures_{datetime.now().isoformat()}.json")
print("✅ Cassandra exporté")


# === Neo4j (semi-structured) ===
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
with driver.session() as session:
    result = session.run("MATCH (c:Capteur)-[:A_PRODUIT]->(m:Mesure) RETURN c.id AS capteur_id, m.valeur, m.unite, m.date_heure")
    neo_data = [record.data() for record in result]

with open("/tmp/neo4j_mesures.json", "w") as f:
    json.dump(neo_data, f)
s3.upload_file("/tmp/neo4j_mesures.json", bucket_name, f"semi_structured/neo4j_mesures_{datetime.now().isoformat()}.json")
print("✅ Neo4j exporté")
