from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uuid

# === Import des BDD ===
import psycopg2
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase

# === App FastAPI avec préfixe de version ===
app = FastAPI(title="SmartCity API", version="1.0")

# =======================
# JWT CONFIGURATION
# =======================
SECRET_KEY = "smartcity_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token")

fake_users_db = {
    "admin": {
        "username": "admin",
        "password": "admin",
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password": "user",
        "role": "user"
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(username=payload.get("sub"), role=payload.get("role"))
    except JWTError:
        raise credentials_exception

@app.post("/v1/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Identifiants invalides")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}
import time
print("⏳ Attente de PostgreSQL (15 secondes)...")
time.sleep(15)
# =======================
# Connexions BDD
# =======================
pg_conn = psycopg2.connect(host="postgres", dbname="smartcity", user="postgres", password="password")
pg_cur = pg_conn.cursor()
mongo = MongoClient("mongodb://mongo:27017/").smartcity_documents
##cluster = Cluster(["cassandra"])
##cass = cluster.connect()
##cass.set_keyspace("smartcity_columns")
neo4j_driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))
from cassandra.cluster import Cluster, NoHostAvailable
import time
from cassandra.cluster import Cluster, NoHostAvailable
import time

print("⏳ Connexion à Cassandra...")

for i in range(10):
    try:
        cluster = Cluster(["cassandra"])
        cass = cluster.connect()
        cass.execute("""
            CREATE KEYSPACE IF NOT EXISTS smartcity_columns
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        cass.set_keyspace("smartcity_columns")
        # Assurer la présence de la table mesures
        cass.execute("""
            CREATE TABLE IF NOT EXISTS mesures (
                id UUID PRIMARY KEY,
                capteur_id int,
                valeur float,
                unite text,
                date_heure timestamp
            );
        """)

        print(" Cassandra connecté.")
        break
    except NoHostAvailable:
        print(f" Cassandra pas encore prêt (tentative {i+1}/10). Attente 5s...")
        time.sleep(5)
else:
    raise Exception(" Cassandra n'a pas répondu après 10 tentatives.")

# =======================
# Pydantic Model
# =======================
class Mesure(BaseModel):
    capteur_id: int
    valeur: float
    unite: str
    date_heure: datetime

@app.post("/v1/pg/mesures/")
def create_pg(m: Mesure, user: TokenData = Depends(get_current_user)):
    try:
        pg_cur.execute(
            "INSERT INTO mesures (capteur_id, valeur, unite, date_heure) VALUES (%s, %s, %s, %s)",
            (m.capteur_id, m.valeur, m.unite, m.date_heure)
        )
        pg_conn.commit()
        return {"msg": "Ajouté"}
    except Exception as e:
        pg_conn.rollback()
        return {"error": str(e)}

@app.get("/v1/pg/mesures/")
def read_pg(capteur_id: Optional[int] = None, user: TokenData = Depends(get_current_user)):
    try:
        if capteur_id is not None:
            pg_cur.execute("SELECT * FROM mesures WHERE capteur_id = %s", (capteur_id,))
        else:
            pg_cur.execute("SELECT * FROM mesures")
        rows = pg_cur.fetchall()
        return [dict(zip([desc[0] for desc in pg_cur.description], row)) for row in rows]
    except Exception as e:
        pg_conn.rollback()
        return {"error": str(e)}
        

# =======================
# MongoDB
# =======================
@app.post("/v1/mongo/mesures/")
def insert_mongo(m: Mesure, user: TokenData = Depends(get_current_user)):
    mongo.mesures.insert_one(m.dict())
    return {"msg": "ok"}

from typing import Optional

@app.get("/v1/mongo/mesures/")
def read_mongo(capteur_id: Optional[int] = None, user: TokenData = Depends(get_current_user)):
    query = {}
    if capteur_id is not None:
        query = {"capteur_id": capteur_id}
    return list(mongo.mesures.find(query, {"_id": 0}))


# =======================
# Cassandra
# =======================
@app.post("/v1/cassandra/mesures/")
def insert_cassandra(m: Mesure, user: TokenData = Depends(get_current_user)):
    cass.execute("INSERT INTO smartcity_columns.mesures (id, capteur_id, valeur, unite, date_heure) VALUES (%s, %s, %s, %s, %s)",
                 (uuid.uuid4(), m.capteur_id, m.valeur, m.unite, m.date_heure))
    return {"msg": "ok"}

from typing import Optional

from typing import Optional

@app.get("/v1/cassandra/mesures/")
def read_cassandra(capteur_id: Optional[int] = None, user: TokenData = Depends(get_current_user)):
    try:
        if capteur_id is not None:
            rows = cass.execute(
                "SELECT * FROM smartcity_columns.mesures WHERE capteur_id = %s", (capteur_id,)
            )
        else:
            rows = cass.execute("SELECT * FROM smartcity_columns.mesures")
        return [dict(row._asdict()) for row in rows]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}




# =======================
# Neo4j
# =======================
@app.post("/v1/neo4j/mesures/")
def insert_neo4j(m: Mesure, user: TokenData = Depends(get_current_user)):
    def run(tx):
        tx.run("""
            MERGE (c:Capteur {id: $capteur_id})
            CREATE (m:Mesure {valeur: $valeur, unite: $unite, date_heure: $date_heure})
            CREATE (c)-[:A_PRODUIT]->(m)
        """, capteur_id=m.capteur_id, valeur=m.valeur, unite=m.unite, date_heure=str(m.date_heure))
    with neo4j_driver.session() as session:
        session.write_transaction(run)
    return {"msg": "ok"}

from typing import Optional

@app.get("/v1/neo4j/mesures/")
def read_neo4j(capteur_id: Optional[int] = None, user: TokenData = Depends(get_current_user)):
    if capteur_id is not None:
        query = """
            MATCH (c:Capteur {id: $capteur_id})-[:A_PRODUIT]->(m:Mesure)
            RETURN c.id AS capteur_id, m.valeur, m.unite, m.date_heure
        """
        params = {"capteur_id": capteur_id}
    else:
        query = """
            MATCH (c:Capteur)-[:A_PRODUIT]->(m:Mesure)
            RETURN c.id AS capteur_id, m.valeur, m.unite, m.date_heure
        """
        params = {}

    with neo4j_driver.session() as session:
        result = session.run(query, **params)
        return [r.data() for r in result]




@app.get("/v1/pg/mesures/")
def read_pg(user: TokenData = Depends(get_current_user)):
    try:
        pg_cur.execute("SELECT * FROM mesures")
        rows = pg_cur.fetchall()
        return [dict(zip([desc[0] for desc in pg_cur.description], row)) for row in rows]
    except Exception as e:
        pg_conn.rollback()
        return {"error": str(e)}

@app.put("/v1/pg/mesures/{id}")
def update_pg(id: int, m: Mesure, user: TokenData = Depends(get_current_user)):
    try:
        pg_cur.execute(
            "UPDATE mesures SET capteur_id=%s, valeur=%s, unite=%s, date_heure=%s WHERE id=%s",
            (m.capteur_id, m.valeur, m.unite, m.date_heure, id)
        )
        pg_conn.commit()
        return {"msg": f"Mesure {id} mise à jour"}
    except Exception as e:
        pg_conn.rollback()
        return {"error": str(e)}

@app.delete("/v1/pg/mesures/{id}")
def delete_pg(id: int, user: TokenData = Depends(get_current_user)):
    try:
        pg_cur.execute("DELETE FROM mesures WHERE id=%s", (id,))
        pg_conn.commit()
        return {"msg": f"Mesure {id} supprimée"}
    except Exception as e:
        pg_conn.rollback()
        return {"error": str(e)}
# =======================
# MongoDB - UPDATE & DELETE
# =======================
@app.put("/v1/mongo/mesures/{capteur_id}")
def update_mongo(capteur_id: int, m: Mesure, user: TokenData = Depends(get_current_user)):
    mongo.mesures.update_one({"capteur_id": capteur_id}, {"$set": m.dict()})
    return {"msg": f"Mesure capteur {capteur_id} mise à jour"}

@app.delete("/v1/mongo/mesures/{capteur_id}")
def delete_mongo(capteur_id: int, user: TokenData = Depends(get_current_user)):
    mongo.mesures.delete_one({"capteur_id": capteur_id})
    return {"msg": f"Mesure capteur {capteur_id} supprimée"}

# =======================
# Cassandra - UPDATE & DELETE
# =======================
@app.put("/v1/cassandra/mesures/{id}")
def update_cassandra(id: str, m: Mesure, user: TokenData = Depends(get_current_user)):
    cass.execute("UPDATE smartcity_columns.mesures SET capteur_id=%s, valeur=%s, unite=%s, date_heure=%s WHERE id=%s",
                 (m.capteur_id, m.valeur, m.unite, m.date_heure, uuid.UUID(id)))
    return {"msg": f"Mesure {id} mise à jour"}

@app.delete("/v1/cassandra/mesures/{id}")
def delete_cassandra(id: str, user: TokenData = Depends(get_current_user)):
    cass.execute("DELETE FROM smartcity_columns.mesures WHERE id=%s", (uuid.UUID(id),))
    return {"msg": f"Mesure {id} supprimée"}

# =======================
# Neo4j - UPDATE & DELETE
# =======================
@app.put("/v1/neo4j/mesures/{capteur_id}")
def update_neo4j(capteur_id: int, m: Mesure, user: TokenData = Depends(get_current_user)):
    def run(tx):
        tx.run("""
            MATCH (c:Capteur {id: $capteur_id})-[:A_PRODUIT]->(m:Mesure)
            SET m.valeur = $valeur, m.unite = $unite, m.date_heure = $date_heure
        """, capteur_id=capteur_id, valeur=m.valeur, unite=m.unite, date_heure=str(m.date_heure))
    with neo4j_driver.session() as session:
        session.write_transaction(run)
    return {"msg": f"Mesure pour capteur {capteur_id} mise à jour"}

@app.delete("/v1/neo4j/mesures/{capteur_id}")
def delete_neo4j(capteur_id: int, user: TokenData = Depends(get_current_user)):
    def run(tx):
        tx.run("""
            MATCH (c:Capteur {id: $capteur_id})-[r:A_PRODUIT]->(m:Mesure)
            DELETE r, m
        """, capteur_id=capteur_id)
    with neo4j_driver.session() as session:
        session.write_transaction(run)
    return {"msg": f"Mesure pour capteur {capteur_id} supprimée"}
