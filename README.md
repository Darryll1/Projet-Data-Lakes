#  Projet Data Lake
 
Ce projet propose une **infrastructure complète de gestion de données** centrée sur la scalabilité, la diversité des formats et l’accessibilité sécurisée via API. Il intègre à la fois des bases relationnelles et NoSQL, un Data Lake basé sur MinIO, et une interface utilisateur conviviale développée avec Streamlit.
 
---
 
##  Objectifs
 
- Intégrer **plusieurs systèmes de gestion de bases de données** (relationnelles et NoSQL)
- Exposer les données via une **API RESTful sécurisée** (FastAPI + JWT)
- Centraliser les données dans un **Data Lake** (MinIO)
- Permettre une **interaction utilisateur** via une interface Streamlit
- Conteneuriser l’ensemble de l’architecture avec Docker & Docker Compose
 
--
 
##  Architecture du Projet
 
| Composant      | Technologie utilisée |
| -------------- | --------------------- |
| Base relationnelle | PostgreSQL |
| NoSQL – Documents | MongoDB |
| NoSQL – Graphes   | Neo4j |
| NoSQL – Colonnes  | Apache Cassandra |
| API sécurisée     | FastAPI + JWT |
| Stockage Data Lake | MinIO (compatible S3) |
| Interface utilisateur | Streamlit |
| Orchestration | Docker + Docker Compose |
 
---
 
## Structure du projet
| Dossier/Fichier                  | Rôle                                                                                   |
| -------------------------------- | -------------------------------------------------------------------------------------- |
| `api_v1_crud_full.py`            | API FastAPI centralisée (CRUD + JWT) pour communiquer avec toutes les bases de données |
| `interface/Interface3.py`        | Interface utilisateur développée avec Streamlit                                        |
| `create_4_databases_complete.py` | Script d'initialisation des tables et structures dans les 4 bases                      |
| `export_to_datalake.py`          | Script d’export des données depuis les bases vers le Data Lake (MinIO)                 |
| `docker-compose.yml`             | Orchestration de tous les services (BDD, API, interface, etc.) via Docker Compose      |
| `Dockerfile`                     | Image Docker pour l'application FastAPI                                                |
| `interface/Dockerfile`           | Image Docker dédiée à l'interface Streamlit                                            |
| `*.json`, `*.csv`                | Jeux de données d’exemple pour injection dans MongoDB, Neo4j, Cassandra ou PostgreSQL  |
| `requirements.txt`               | Liste des dépendances Python requises pour exécuter l’API ou les scripts               |
| `README.md`                      | Document de présentation du projet (ce fichier)                                        |

## Technologies utilisées
FastAPI pour l’API REST
PyJWT, PassLib pour la sécurité
psycopg2, PyMongo, neo4j-driver, cassandra-driver pour les connexions BDD
boto3 pour interagir avec MinIO
Streamlit pour l’interface graphique
## Lancer le projet 
1. Cloner le dépôt et se placer dans le dossier du projet
2. Lancer tous les services avec Docker Compose
docker compose up --build -d
Ce fichier docker-compose.yml va démarrer :
PostgreSQL
MongoDB
Neo4j
Cassandra
MinIO
L’API FastAPI
 Une fois les services démarrés, l’API FastAPI est accessible à l’adresse :
http://localhost:8000/docs
Lancer l’interface Streamlit
L’interface Streamlit n’est pas démarrée automatiquement par Docker. Tu dois exécuter la commande suivante dans le conteneur  :
 python interface/Interface.py
 L’interface s’ouvrira à l’adresse suivante :
http://localhost:8501
Le datalake se trouve sur http://localhost:9001
