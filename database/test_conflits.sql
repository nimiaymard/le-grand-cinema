
-- Test : prévention des chevauchements de séances
-- Toutes les données de test seront annulées.

BEGIN;

INSERT INTO films (titre, duree_minutes)
VALUES ('Film Test A', 120);

INSERT INTO salles (nom, capacite)
VALUES ('Salle Test', 100);

INSERT INTO seances (
    film_id,
    salle_id,
    date_debut,
    date_fin,
    prix
)
SELECT
    f.id,
    s.id,
    '2026-12-01 14:00:00+01',
    '2026-12-01 16:00:00+01',
    10.00
FROM films f
CROSS JOIN salles s
WHERE f.titre = 'Film Test A'
AND s.nom = 'Salle Test';

-- Cette seconde séance doit être refusée.
-- Elle chevauche la première dans la même salle.

INSERT INTO seances (
    film_id,
    salle_id,
    date_debut,
    date_fin,
    prix
)
SELECT
    f.id,
    s.id,
    '2026-12-01 15:00:00+01',
    '2026-12-01 17:00:00+01',
    10.00
FROM films f
CROSS JOIN salles s
WHERE f.titre = 'Film Test A'
AND s.nom = 'Salle Test';

ROLLBACK;
