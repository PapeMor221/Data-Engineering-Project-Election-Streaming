-- Création de la base de données
CREATE DATABASE ElectionDB;
\c ElectionDB;

-- Table principale des votes par candidat
CREATE TABLE vote_counts (
    candidat_nom VARCHAR(255),
    candidat_prenom VARCHAR(255),
    total_votes INTEGER DEFAULT 0,
    UNIQUE (candidat_nom, candidat_prenom)
);

-- Table des votes par lieu de vote
CREATE TABLE votes_par_lieu (
    candidat_nom VARCHAR(255),
    candidat_prenom VARCHAR(255),
    lieu_vote VARCHAR(255),
    votes_par_lieu INTEGER DEFAULT 0,
    UNIQUE (candidat_nom, candidat_prenom, lieu_vote)
);

-- Table des votes par tranche d'âge
CREATE TABLE votes_par_age (
    candidat_nom VARCHAR(255),
    candidat_prenom VARCHAR(255),
    age_group VARCHAR(10),
    votes_par_age INTEGER DEFAULT 0,
    UNIQUE (candidat_nom, candidat_prenom, age_group)
);

-- Table des votes par sexe
CREATE TABLE votes_par_sexe (
    candidat_nom VARCHAR(255),
    candidat_prenom VARCHAR(255),
    sexe VARCHAR(10),
    votes_par_sexe INTEGER DEFAULT 0,
    UNIQUE (candidat_nom, candidat_prenom, sexe)
);