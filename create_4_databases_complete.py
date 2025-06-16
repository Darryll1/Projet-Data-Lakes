import time
print(" Attente que les bases de données démarrent...")
time.sleep(15)

# ===============================
# 1. BASE RELATIONNELLE : POSTGRESQL
# ===============================
import psycopg2

try:
    pg_conn = psycopg2.connect(
        host="postgres",
        dbname="smartcity",
        user="postgres",
        password="password"
    )
    pg_cur = pg_conn.cursor()

    # Transactions + contraintes + déclencheur
    pg_cur.execute("BEGIN;")
    pg_cur.execute("""
    CREATE TABLE IF NOT EXISTS mesures (
        id SERIAL PRIMARY KEY,
        capteur_id INT NOT NULL,
        valeur FLOAT CHECK (valeur >= 0),
        unite VARCHAR(10) NOT NULL,
        date_heure TIMESTAMP NOT NULL
    );
    """)

    pg_cur.execute("""
    CREATE OR REPLACE FUNCTION log_pollution()
    RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.valeur > 100 THEN
            RAISE NOTICE 'Pollution détectée : valeur = %', NEW.valeur;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    pg_cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'pollution_alert_trigger'
        ) THEN
            CREATE TRIGGER pollution_alert_trigger
            AFTER INSERT ON mesures
            FOR EACH ROW
            EXECUTE FUNCTION log_pollution();
        END IF;
    END;
    $$;
    """)

    pg_cur.execute("""
    INSERT INTO mesures (capteur_id, valeur, unite, date_heure)
    VALUES (%s, %s, %s, %s)
    """, (1, 110.5, 'Ug/m3', '2025-04-18 14:00:00'))

    pg_conn.commit()
    print("PostgreSQL : Donnée insérée avec intégrité + trigger activé.")
except Exception as e:
    pg_conn.rollback()
    print("PostgreSQL Error:", e)
finally:
    pg_cur.close()
    pg_conn.close()


# ===============================
# 2. MongoDB (orientée documents)
# ===============================
from pymongo import MongoClient
mongo_client = MongoClient("mongodb://mongo:27017/")
mongo_db = mongo_client.smartcity_documents

doc = {
    "capteur_id": 1,
    "valeur": 110.5,
    "unite": "Ug/m3",
    "date_heure": "2025-04-18T14:00:00"
}
mongo_db.mesures.insert_one(doc)
print("MongoDB : Document inséré.")

# ===============================
# 3. Cassandra (orientée colonnes)
# ===============================
# ===============================
# 3. Cassandra (orientée colonnes)
# ===============================
from cassandra.cluster import Cluster, NoHostAvailable
from datetime import datetime
import time
import uuid

print("Connexion à Cassandra...")

MAX_ATTEMPTS = 20
WAIT_SECONDS = 10

for i in range(MAX_ATTEMPTS):
    try:
        cluster = Cluster(["cassandra"])
        session = cluster.connect()
        print("Cassandra connecté.")
        break
    except NoHostAvailable:
        print(f"Cassandra pas encore prêt (tentative {i+1}/{MAX_ATTEMPTS}). Attente {WAIT_SECONDS}s...")
        time.sleep(WAIT_SECONDS)
else:
    raise Exception(f"Cassandra n’a pas répondu après {MAX_ATTEMPTS} tentatives.")

# Création keyspace + table
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS smartcity_columns
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
""")
session.set_keyspace("smartcity_columns")

session.execute("""
    CREATE TABLE IF NOT EXISTS mesures (
        id UUID PRIMARY KEY,
        capteur_id int,
        valeur float,
        unite text,
        date_heure timestamp
    );
""")

# Création de l'index secondaire sur capteur_id
session.execute("""
    CREATE INDEX IF NOT EXISTS mesures_capteur_id_idx ON mesures (capteur_id);
""")
print(" Cassandra : Index secondaire sur capteur_id créé.")

# Insertion de données
session.execute("""
    INSERT INTO mesures (id, capteur_id, valeur, unite, date_heure)
    VALUES (%s, %s, %s, %s, %s)
""", (uuid.uuid4(), 1, 110.5, "Ug/m3", datetime.utcnow()))

print("Cassandra : Donnée insérée.")

# ===============================
# 4. Neo4j (orientée graphes)
# ===============================
from neo4j import GraphDatabase, basic_auth
import time

print("Connexion à Neo4j...")

neo4j_driver = None

for i in range(10):
    try:
        neo4j_driver = GraphDatabase.driver("bolt://neo4j:7687", auth=basic_auth("neo4j", "password"))
        with neo4j_driver.session() as session:
            session.run("RETURN 1")  # simple test
        print("Neo4j connecté.")
        break
    except Exception as e:
        print(f"Neo4j pas encore prêt (tentative {i+1}/10). Attente 5s...")
        time.sleep(5)
else:
    raise Exception("Neo4j n’a pas répondu après 10 tentatives.")

def insert_mesure(tx, capteur_id, valeur, unite, date_heure):
    tx.run("""
        MERGE (c:Capteur {id: $capteur_id})
        CREATE (m:Mesure {valeur: $valeur, unite: $unite, date_heure: $date_heure})
        CREATE (c)-[:A_PRODUIT]->(m)
    """, capteur_id=capteur_id, valeur=valeur, unite=unite, date_heure=date_heure)

with neo4j_driver.session() as session:
    session.execute_write(insert_mesure, 1, 110.5, "Ug/m3", "2025-04-18T14:00:00")
    print("Neo4j : Donnée insérée avec relation.")
