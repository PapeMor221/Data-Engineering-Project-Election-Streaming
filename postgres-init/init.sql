CREATE DATABASE ElectionDB;
\c ElectionDB;

CREATE TABLE vote_counts (
    candidat_nom VARCHAR(255),
    candidat_prenom VARCHAR(255),
    count INTEGER,
    UNIQUE (candidat_nom, candidat_prenom)
);