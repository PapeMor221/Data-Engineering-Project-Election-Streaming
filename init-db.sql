-- Création des tables pour stocker les données électorales
CREATE TABLE IF NOT EXISTS votes_raw (
    id SERIAL PRIMARY KEY,
    cni VARCHAR(20),
    nom VARCHAR(100),
    prenom VARCHAR(100),
    lieu_vote VARCHAR(100),
    sexe CHAR(1),
    age INTEGER,
    candidat_nom VARCHAR(100),
    candidat_prenom VARCHAR(100),
    candidat_bureau_vote VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS votes_par_candidat (
    id SERIAL PRIMARY KEY,
    candidat_nom VARCHAR(100),
    candidat_prenom VARCHAR(100),
    count BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS votes_par_lieu (
    id SERIAL PRIMARY KEY,
    lieu_vote VARCHAR(100),
    candidat_nom VARCHAR(100),
    count BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS votes_par_demo (
    id SERIAL PRIMARY KEY,
    sexe CHAR(1),
    tranche_age VARCHAR(10),
    candidat_nom VARCHAR(100),
    count BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);