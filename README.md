# Projet Data Lakes – Intégration multi-bases et export vers Data Lake

## Description

Ce projet a pour objectif de développer une interface permettant de **centraliser des données issues de plusieurs bases de données hétérogènes** (PostgreSQL, MongoDB, Cassandra, Neo4j) et de les **exporter vers un Data Lake**. Il repose sur une architecture Dockerisée et une logique d’intégration orientée API.

---

## Architecture technique

Le projet est structuré autour des éléments suivants :

- **API Python (FastAPI)** : communication avec les bases via des endpoints REST
- **Interface utilisateur (Streamlit)** : chargement des mesures, affichage et export vers le Data Lake
- **Bases de données connectées** :
  - PostgreSQL
  - MongoDB
  - Cassandra
  - Neo4j
- **Export vers un système de fichiers Data Lake (MinIO ou équivalent)**
- **Docker + Docker Compose** : pour le déploiement multi-conteneurs

---

##  Structure des fichiers

| Dossier/Fichier | Rôle |
|------------------|------|
| `api_v1_crud_full.py` | API FastAPI pour communiquer avec les bases |
| `interface/Interface.py` | Interface utilisateur Streamlit |
| `create_4_databases_complete.py` | Script de création/initialisation des 4 bases |
| `export_to_datalake.py` | Script d’export des données vers le Data Lake |
| `docker-compose.yml` | Configuration des services Docker |
| `*.json / *.csv` | Jeux de données pour MongoDB, Neo4j, Cassandra, PostgreSQL |
| `Dockerfile` | Image Docker pour l’API |
| `interface/Dockerfile` | Image Docker pour Streamlit |

-
