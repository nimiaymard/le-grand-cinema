
-- Projet : Le Grand Cinéma
-- Base de données : PostgreSQL
-- Table 1 : utilisateurs
-- Extension permettant certaines contraintes d'exclusion
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE utilisateurs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
     email VARCHAR(255) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'spectateur',
    date_creation TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_utilisateur_role
        CHECK (role IN ('spectateur', 'admin'))
);

-- Table 2 : films

CREATE TABLE films (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titre VARCHAR(200) NOT NULL,
    description TEXT,
    duree_minutes INTEGER NOT NULL,
    genre VARCHAR(100),
    date_sortie DATE,
    affiche_url VARCHAR(500),
    date_creation TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_film_duree
        CHECK (duree_minutes > 0)
);

-- Table 3 : salles

CREATE TABLE salles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    capacite INTEGER NOT NULL,
    est_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_salle_capacite
        CHECK (capacite > 0)
);

-- Table 4 : places

CREATE TABLE places (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salle_id BIGINT NOT NULL,
    rangee VARCHAR(5) NOT NULL,
    numero INTEGER NOT NULL,
    est_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_place_salle
        FOREIGN KEY (salle_id)
        REFERENCES salles(id),

    CONSTRAINT uq_place_salle
        UNIQUE (salle_id, rangee, numero),

    CONSTRAINT uq_place_id_salle
        UNIQUE (id, salle_id),

    CONSTRAINT chk_place_numero
        CHECK (numero > 0)
);
-- Table 5 : seances

CREATE TABLE seances (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    film_id BIGINT NOT NULL,
    salle_id BIGINT NOT NULL,
    date_debut TIMESTAMPTZ NOT NULL,
    date_fin TIMESTAMPTZ NOT NULL,
    prix NUMERIC(8,2) NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'programmee',

    CONSTRAINT fk_seance_film
        FOREIGN KEY (film_id)
        REFERENCES films(id),

    CONSTRAINT fk_seance_salle
        FOREIGN KEY (salle_id)
        REFERENCES salles(id),
  
    CONSTRAINT uq_seance_id_salle
        UNIQUE (id, salle_id),

    CONSTRAINT chk_seance_dates
        CHECK (date_fin > date_debut),

    CONSTRAINT chk_seance_prix
        CHECK (prix >= 0),

    CONSTRAINT chk_seance_statut
        CHECK (statut IN ('programmee', 'annulee', 'terminee'))
);

-- Empêcher les chevauchements de séances
-- dans une même salle.

ALTER TABLE seances
ADD CONSTRAINT excl_chevauchement_seances
EXCLUDE USING gist (
    salle_id WITH =,
    tstzrange(date_debut, date_fin, '[)') WITH &&
)
WHERE (statut = 'programmee');
-- Table 6 : reservations

CREATE TABLE reservations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id BIGINT NOT NULL,
    seance_id BIGINT NOT NULL,
    date_reservation TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    montant_total NUMERIC(10,2) NOT NULL DEFAULT 0,

    CONSTRAINT fk_reservation_utilisateur
        FOREIGN KEY (utilisateur_id)
        REFERENCES utilisateurs(id),

    CONSTRAINT fk_reservation_seance
        FOREIGN KEY (seance_id)
        REFERENCES seances(id),

    CONSTRAINT chk_reservation_statut
        CHECK (statut IN (
            'en_attente',
            'confirmee',
            'annulee'
        )),

    CONSTRAINT chk_reservation_montant
        CHECK (montant_total >= 0),

    CONSTRAINT uq_reservation_id_seance
        UNIQUE (id, seance_id)
);

-- Table 7 : reservation_places

CREATE TABLE reservation_places (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_id BIGINT NOT NULL,
    seance_id BIGINT NOT NULL,
    salle_id BIGINT NOT NULL,
    place_id BIGINT NOT NULL,
    date_liberation TIMESTAMPTZ DEFAULT NULL,

    CONSTRAINT fk_rp_reservation
        FOREIGN KEY (reservation_id, seance_id)
        REFERENCES reservations(id, seance_id),

    CONSTRAINT fk_rp_seance_salle
        FOREIGN KEY (seance_id, salle_id)
        REFERENCES seances(id, salle_id),

    CONSTRAINT fk_rp_place_salle
        FOREIGN KEY (place_id, salle_id)
        REFERENCES places(id, salle_id)

  
);

   
-- Une place ne peut être occupée qu'une fois par séance.
-- Les places libérées restent dans l'historique.

CREATE UNIQUE INDEX uq_place_active_par_seance
ON reservation_places (seance_id, place_id)
WHERE date_liberation IS NULL;
