import streamlit as st
st.set_page_config(page_title="Interface API SmartCity", layout="wide")

import requests
from datetime import datetime
import uuid

# === CONFIGURATION ===
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"

# === AUTHENTIFICATION ===
@st.cache
def get_auth_token():
    try:
        resp = requests.post(f"{BASE_URL}/v1/token", data={"username": USERNAME, "password": PASSWORD})
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        st.error(f"❌ Erreur d'authentification : {e}")
        return {}

headers = get_auth_token()

# === OUTILS ===
def clean_string(text):
    try:
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        return text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")

def clean_data(data):
    return {k: clean_string(v) if isinstance(v, str) else v for k, v in data.items()}

# === SIDEBAR : Aperçus des bases ===
st.sidebar.title("📊 Aperçu des Données")

env_preview = st.sidebar.selectbox("🔍 Voir les données de :", ["", "PostgreSQL", "MongoDB", "Cassandra", "Neo4j"])

if env_preview == "PostgreSQL":
    try:
        response = requests.get(f"{BASE_URL}/v1/pg/mesures/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                st.sidebar.dataframe(data)
            elif isinstance(data, list):
                st.sidebar.info("✅ Aucune donnée à afficher.")
            elif isinstance(data, dict) and "error" in data:
                st.sidebar.error(f"❌ Erreur API : {data['error']}")
            else:
                st.sidebar.warning("⚠️ Format inattendu.")
                st.sidebar.json(data)
        else:
            st.sidebar.error(f"❌ Erreur API PostgreSQL : {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur PostgreSQL : {e}")

elif env_preview == "MongoDB":
    try:
        response = requests.get(f"{BASE_URL}/v1/mongo/mesures/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                st.sidebar.dataframe(data)
            elif isinstance(data, list):
                st.sidebar.info("✅ Aucune donnée à afficher.")
            elif isinstance(data, dict) and "error" in data:
                st.sidebar.error(f"❌ Erreur API : {data['error']}")
            else:
                st.sidebar.warning("⚠️ Format inattendu.")
                st.sidebar.json(data)
        else:
            st.sidebar.error(f"❌ Erreur API MongoDB : {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur MongoDB : {e}")

elif env_preview == "Cassandra":
    try:
        response = requests.get(f"{BASE_URL}/v1/cassandra/mesures/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                st.sidebar.dataframe(data)
            elif isinstance(data, list):
                st.sidebar.info("✅ Aucune donnée à afficher.")
            elif isinstance(data, dict) and "error" in data:
                st.sidebar.error(f"❌ Erreur API : {data['error']}")
            else:
                st.sidebar.warning("⚠️ Format inattendu.")
                st.sidebar.json(data)
        else:
            st.sidebar.error(f"❌ Erreur API Cassandra : {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur Cassandra : {e}")

elif env_preview == "Neo4j":
    try:
        response = requests.get(f"{BASE_URL}/v1/neo4j/mesures/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                st.sidebar.dataframe(data)
            elif isinstance(data, list):
                st.sidebar.info("✅ Aucune donnée à afficher.")
            elif isinstance(data, dict) and "error" in data:
                st.sidebar.error(f"❌ Erreur API : {data['error']}")
            else:
                st.sidebar.warning("⚠️ Format inattendu.")
                st.sidebar.json(data)
        else:
            st.sidebar.error(f"❌ Erreur API Neo4j : {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur Neo4j : {e}")

# === Export to Datalake ===
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
def export_PostgreSQL():
    conn = psycopg2.connect(host="localhost", dbname="smartcity", user="postgres", password="password", port=5432)
    df_pg = pd.read_sql("SELECT * FROM mesures", conn)
    csv_pg = "/tmp/postgres_mesures.csv"
    df_pg.to_csv(csv_pg, index=False)
    s3.upload_file(csv_pg, bucket_name, f"structured/postgres_mesures_{datetime.now().isoformat()}.csv")
    print("✅ PostgreSQL exporté")

# === MongoDB (semi-structured) ===
def export_MongoDB():
    mongo = MongoClient("mongodb://localhost:27017/")
    docs = list(mongo.smartcity_documents.mesures.find({}, {"_id": 0}))
    with open("/tmp/mongo_mesures.json", "w") as f:
        json.dump(docs, f)
    s3.upload_file("/tmp/mongo_mesures.json", bucket_name, f"semi_structured/mongo_mesures_{datetime.now().isoformat()}.json")
    print("✅ MongoDB exporté")

# === Cassandra (semi-structured) ===
def export_Cassandra():
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
def export_Neo4j():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        result = session.run("MATCH (c:Capteur)-[:A_PRODUIT]->(m:Mesure) RETURN c.id AS capteur_id, m.valeur, m.unite, m.date_heure")
        neo_data = [record.data() for record in result]

    with open("/tmp/neo4j_mesures.json", "w") as f:
        json.dump(neo_data, f)
    s3.upload_file("/tmp/neo4j_mesures.json", bucket_name, f"semi_structured/neo4j_mesures_{datetime.now().isoformat()}.json")
    print("✅ Neo4j exporté")
    
# === FICHIERS UTILISATEURS (unstructured) ===
def fichiers_utilisateurs():
    # === FICHIERS UTILISATEUR (non-structurés) ===
    upload_dir = "./uploads"  # Dossier local où les fichiers sont déposés
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                object_name = f"unstructured/{datetime.now().isoformat()}_{filename}"
                try:
                    s3.upload_file(file_path, bucket_name, object_name)
                    print(f" Fichier utilisateur exporté : {object_name}")
                except Exception as e:
                    print(f" Erreur lors de l'upload de {filename} : {e}")
    else:
        print("⚠️ Dossier './uploads' introuvable. Aucun fichier non structuré exporté.")
# === INTERFACE PRINCIPALE ===
st.title("🌐 Interface API SmartCity")

operation = st.selectbox("🛠️ Choisissez une opération :", ["", "create", "get", "put", "delete", "ajouter fichier"])

# === UPLOAD DE FICHIERS ===
# === AJOUTER FICHIER (Streamlit) ===

if operation == "ajouter fichier":

    fichiers = st.file_uploader("📎 Importez vos fichiers :", type=["csv", "json", "txt"], accept_multiple_files=True)
    if fichiers:
        upload_dir = "./uploads"
        os.makedirs(upload_dir, exist_ok=True)
        for fichier in fichiers:
            file_path = os.path.join(upload_dir, fichier.name)
            with open(file_path, "wb") as f:
                f.write(fichier.read())
        st.success(f"{len(fichiers)} fichier(s) sauvegardé(s) localement pour export.")
        fichiers_utilisateurs()
 

# === OPERATIONS CRUD ===
elif operation in ["create", "get", "put", "delete"]:
    env = st.selectbox("🌍 Environnement :", ["", "PostgreSQL", "MongoDB", "Cassandra", "Neo4j"])
    env_map = {
        "PostgreSQL": "pg",
        "MongoDB": "mongo",
        "Cassandra": "cassandra",
        "Neo4j": "neo4j"
    }

    if env:
        api_path = f"{BASE_URL}/v1/{env_map[env]}/mesures/"
        st.subheader(f"🧰 Opération '{operation}' sur {env}")

        capteur_id = st.number_input("🔢 Capteur ID", min_value=1, step=1)

        if operation in ["create", "put"]:
            valeur = st.number_input("🌡️ Valeur", format="%.4f")
            unite = st.text_input("📏 Unité")
            date = st.date_input("📅 Date")
            heure = st.time_input("⏰ Heure")
            date_heure = datetime.combine(date, heure)
            mesure = {
                "capteur_id": capteur_id,
                "valeur": valeur,
                "unite": unite,
                "date_heure": date_heure.isoformat()
            }

        # === CREATE ===
        if operation == "create" and st.button("📥 Créer la mesure"):
            res = requests.post(api_path, json=clean_data(mesure), headers=headers)
            if res.status_code == 200:
                st.success("✅ Mesure créée avec succès.")
                st.json(res.json())
                if env == "PostgreSQL": 
                    export_PostgreSQL()
                elif env == "MongoDB":
                    export_MongoDB()
                elif env == "Cassandra":
                    export_Cassandra()
                elif env == "Neo4j": 
                    export_Neo4j()    
            else:
                st.error(f"❌ Erreur de création ({res.status_code})")
                st.text(res.text)

        # === GET ===
        elif operation == "get" and st.button("📤 Récupérer les mesures"):
            params = {"capteur_id": capteur_id} if env in ["PostgreSQL", "MongoDB", "Cassandra", "Neo4j"] else {}
            res = requests.get(api_path, headers=headers, params=params)
            if res.status_code == 200:
                st.success("✅ Données récupérées avec succès.")
                st.json(res.json())
            else:
                st.error(f"❌ Erreur de récupération ({res.status_code})")
                st.text(res.text)

        # === PUT ===
        elif operation == "put":
            identifiant = st.text_input("✏️ Identifiant (UUID ou entier)")
            if st.button("🔄 Mettre à jour la mesure"):
                put_path = api_path + identifiant
                res = requests.put(put_path, json=clean_data(mesure), headers=headers)
                if res.status_code == 200:
                    st.success("✅ Mise à jour effectuée avec succès.")
                    st.json(res.json())
                    if env == "PostgreSQL": 
                        export_PostgreSQL()
                    elif env == "MongoDB":
                        export_MongoDB()
                    elif env == "Cassandra":
                        export_Cassandra()
                    elif env == "Neo4j": 
                        export_Neo4j()  
                else:
                    st.error(f"❌ Erreur lors de la mise à jour ({res.status_code})")
                    st.text(res.text)

        # === DELETE ===
        elif operation == "delete":
            identifiant = (
                st.text_input("🗑️ Identifiant (UUID)") if env == "Cassandra"
                else st.number_input("🗑️ Identifiant (id)", min_value=1, step=1)
            )
            if st.button("🧹 Supprimer la mesure"):
                delete_path = api_path + str(identifiant)
                res = requests.delete(delete_path, headers=headers)
                if res.status_code == 200:
                    st.success("✅ Mesure supprimée avec succès.")
                    st.json(res.json())
                    if env == "PostgreSQL": 
                        export_PostgreSQL()
                    elif env == "MongoDB":
                        export_MongoDB()
                    elif env == "Cassandra":
                        export_Cassandra()
                    elif env == "Neo4j": 
                        export_Neo4j()  
                else:
                    st.error(f"❌ Erreur lors de la suppression ({res.status_code})")
                    st.text(res.text)
