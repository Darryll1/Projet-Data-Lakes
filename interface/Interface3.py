import streamlit as st
st.set_page_config(page_title="Interface API SmartCity", layout="wide")

import requests
from datetime import datetime
import uuid

# === CONFIGURATION ===
BASE_URL = "http://app:8000" 
USERNAME = "admin"
PASSWORD = "admin"

# === AUTHENTIFICATION ===
# @st.cache_data
# def get_auth_token():
#     try:
#         resp = requests.post(f"{BASE_URL}/v1/token", data={"username": USERNAME, "password": PASSWORD})
#         token = resp.json()["access_token"]
#         return {"Authorization": f"Bearer {token}"}
#     except Exception as e:
#         st.error(f"❌ Erreur d'authentification : {e}")
#         return {}
@st.cache_data
def get_auth_token():
    try:
        resp = requests.post(f"{BASE_URL}/v1/token", data={"username": USERNAME, "password": PASSWORD}, timeout=5)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        else:
            st.error("❌ Token non reçu de l'API.")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion à l'API : {e}")
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
import psycopg2
import pandas as pd
import json
import boto3
from datetime import datetime
from sqlalchemy import create_engine


print("📤 Export vers Data Lake (MinIO)...")

# === Connexion MinIO ===
s3 = boto3.client(
    's3',
    endpoint_url="http://minio:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="admin123",
    region_name="us-east-1"
)
bucket_name = "datalake"
try:
    s3.create_bucket(Bucket=bucket_name)
except:
    pass

# === EXPORT FONCTIONS ===
def export_PostgreSQL():
    try:
        engine = create_engine("postgresql+psycopg2://postgres:password@postgres:5432/smartcity")
        df_pg = pd.read_sql("SELECT * FROM mesures", engine)
        export_dir = "/tmp/exports"
        os.makedirs(export_dir, exist_ok=True)
        csv_pg = os.path.join(export_dir, "postgres_mesures.csv")
        df_pg.to_csv(csv_pg, index=False)
        s3.upload_file(csv_pg, bucket_name, f"structured/postgres_mesures_{datetime.now().isoformat()}.csv")
        print("✅ PostgreSQL exporté vers MinIO")
    except Exception as e:
        print(f"❌ Erreur PostgreSQL export : {e}")

def export_MongoDB():
    try:
        mongo = MongoClient("mongodb://mongo:27017/")
        docs = list(mongo.smartcity_documents.mesures.find({}, {"_id": 0}))

        # Convertir les dates en chaînes ISO
        def serialize_doc(doc):
            return {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in doc.items()
            }

        cleaned_docs = [serialize_doc(doc) for doc in docs]

        export_dir = "/tmp/exports"
        os.makedirs(export_dir, exist_ok=True)
        json_path = os.path.join(export_dir, "mongo_mesures.json")

        with open(json_path, "w") as f:
            json.dump(cleaned_docs, f)

        s3.upload_file(json_path, bucket_name, f"semi_structured/MongoDB/mongo_mesures_{datetime.now().isoformat()}.json")
        print("✅ MongoDB exporté")

    except Exception as e:
        print(f"❌ Erreur MongoDB export : {e}")


def export_Cassandra():
    try:
        cluster = Cluster(["cassandra"], port=9042)
        cass = cluster.connect("smartcity_columns")
        rows = cass.execute("SELECT * FROM mesures")
        cass_data = [{k: str(v) if isinstance(v, uuid.UUID) else v.isoformat() if isinstance(v, datetime) else v for k, v in row._asdict().items()} for row in rows]
        export_dir = "/tmp/exports"
        os.makedirs(export_dir, exist_ok=True)
        json_path = os.path.join(export_dir, "cassandra_mesures.json")
        with open(json_path, "w") as f:
            json.dump(cass_data, f, indent=2)
        s3.upload_file(json_path, bucket_name, f"semi_structured/Cassandra/cassandra_mesures_{datetime.now().isoformat()}.json")
        print("✅ Cassandra exporté")
    except Exception as e:
        print(f"❌ Erreur Cassandra export : {e}")

def export_Neo4j():
    try:
        driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            result = session.run("MATCH (c:Capteur)-[:A_PRODUIT]->(m:Mesure) RETURN c.id AS capteur_id, m.valeur, m.unite, m.date_heure")
            neo_data = [record.data() for record in result]
        export_dir = "/tmp/exports"
        os.makedirs(export_dir, exist_ok=True)
        json_path = os.path.join(export_dir, "neo4j_mesures.json")
        with open(json_path, "w") as f:
            json.dump(neo_data, f)
        s3.upload_file(json_path, bucket_name, f"semi_structured/Neo4j/neo4j_mesures_{datetime.now().isoformat()}.json")
        print("✅ Neo4j exporté")
    except Exception as e:
        print(f"❌ Erreur Neo4j export : {e}")

# === INTERFACE PRINCIPALE ===
st.title("🌐 Interface API SmartCity")
 
export_PostgreSQL()
export_MongoDB()
export_Cassandra()
export_Neo4j()  

operation = st.selectbox("🛠️ Choisissez une opération :", ["", "create", "get", "put", "delete", "ajouter fichier"])

# === UPLOAD DE FICHIERS ===
if operation == "ajouter fichier": 
    fichiers = st.file_uploader("📎 Importez vos fichiers :", type=["csv", "json", "txt"], accept_multiple_files=True)
    if fichiers:
        st.success(f"{len(fichiers)} fichier(s) importé(s)")

        uploads_dir = "./uploads"
        os.makedirs(uploads_dir, exist_ok=True)  # 🔧 Crée le dossier local si besoin

        for fichier in fichiers:
            st.write(f"📄 {fichier.name}")
            try:
                # 🔁 Génère un nom de fichier unique pour MinIO (dans un dossier 'unstructured')
                object_name = f"unstructured/{datetime.now().isoformat()}_{fichier.name}"

                # 📂 Chemin local temporaire
                local_path = os.path.join(uploads_dir, fichier.name)

                # 💾 Sauvegarde sur disque
                with open(local_path, "wb") as file:
                    file.write(fichier.getbuffer())

                # ⬆️ Envoi vers MinIO dans le bucket 'datalake' sous 'unstructured/'
                s3.upload_file(local_path, bucket_name, object_name)

                # 🧹 Nettoyage du fichier local
                os.remove(local_path)

                st.success(f"✅ Fichier '{fichier.name}' exporté vers MinIO dans 'unstructured/'.")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'upload de {fichier.name} : {e}")

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
