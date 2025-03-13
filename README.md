Titre : Projet d'Ingénierie des Données : Pipeline de Données de Vote en Temps Réel

Description :

Ce projet simule un système de vote en temps réel et met en œuvre un pipeline de données complet, de la génération de données à la visualisation des résultats. Il met en évidence les compétences et les outils essentiels pour un ingénieur de données moderne.

Fonctionnalités Clés :

Génération de Données Simulées :
Un générateur de données simule des votes, produisant des flux de données réalistes.
Pipeline de Données en Temps Réel :
Les données de vote sont transmises via Apache Kafka, un système de messagerie distribué.
Apache Spark Streaming est utilisé pour traiter les données en temps réel, effectuer des agrégations et des calculs.
Stockage de Données :
Les résultats agrégés sont stockés dans une base de données PostgreSQL, permettant une analyse et une visualisation ultérieures.
Visualisation des Données :
Les données sont visualisées à l'aide de Grafana, créant des tableaux de bord interactifs pour suivre les résultats des votes en temps réel.
Infrastructure Conteneurisée :
L'ensemble du pipeline est conteneurisé avec Docker et orchestré avec Docker Compose, assurant une portabilité et une reproductibilité maximales.
Aspects d'Ingénierie des Données Mis en Avant :

Architecture de Pipeline de Données :
Conception et mise en œuvre d'un pipeline de données robuste et évolutif.
Traitement de Flux de Données :
Utilisation de Spark Streaming pour le traitement de données en temps réel.
Intégration de Données :
Intégration de diverses technologies (Kafka, Spark, PostgreSQL, Grafana) pour créer un système cohérent.
Automatisation et Orchestration :
Utilisation de Docker et Docker Compose pour automatiser le déploiement et l'orchestration du pipeline.
Surveillance et Visualisation :
Mise en place de tableaux de bord Grafana pour surveiller et visualiser les données en temps réel.
Technologies Utilisées :

Apache Kafka
Apache Spark Streaming
PostgreSQL
Grafana
Docker
Docker Compose
Python
Instructions d'Exécution :

Cloner le dépôt.
Installer Docker et Docker Compose.
Exécuter docker compose up -d.
Accéder à Grafana via http://localhost:3000.
