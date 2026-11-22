
-- Test : cohérence entre salle, séance et place
BEGIN;

-- Créer deux salles
INSERT INTO salles (nom, capacite)
VALUES
('Salle Cohérence 1', 50),
('Salle Cohérence 2', 50);

-- Créer une place A12 dans la salle 2
INSERT INTO places (salle_id, rangee, numero)
SELECT id, 'A', 12
FROM salles
WHERE nom = 'Salle Cohérence 2';

-- Créer un film
INSERT INTO films (titre, duree_minutes)
VALUES ('Film Test Cohérence', 90);

-- Programmer le film dans la salle 1
INSERT INTO seances
(film_id, salle_id, date_debut, date_fin, prix)
SELECT f.id, s.id,
       '2026-12-04 14:00:00+01',
       '2026-12-04 15:30:00+01',
       8.00
FROM films f
CROSS JOIN salles s
WHERE f.titre = 'Film Test Cohérence'
  AND s.nom = 'Salle Cohérence 1';

-- Créer un spectateur
INSERT INTO utilisateurs
(nom, prenom, email, mot_de_passe_hash)
VALUES
('Test', 'Charlie', 'charlie-coherence@example.com', 'hash-test');

-- Créer sa réservation
INSERT INTO reservations
(utilisateur_id, seance_id, statut, montant_total)
SELECT u.id, se.id, 'confirmee', 8.00
FROM utilisateurs u
CROSS JOIN seances se
JOIN films f ON f.id = se.film_id
WHERE u.email = 'charlie-coherence@example.com'
  AND f.titre = 'Film Test Cohérence';

-- Tenter d'attribuer une place de la salle 2
-- à une séance programmée dans la salle 1.
-- Cette insertion doit être refusée.
INSERT INTO reservation_places
(reservation_id, seance_id, salle_id, place_id)
SELECT
    r.id,
    r.seance_id,
    se.salle_id,
    p.id
FROM reservations r
JOIN utilisateurs u ON u.id = r.utilisateur_id
JOIN seances se ON se.id = r.seance_id
CROSS JOIN places p
JOIN salles s ON s.id = p.salle_id
WHERE u.email = 'charlie-coherence@example.com'
  AND s.nom = 'Salle Cohérence 2'
  AND p.rangee = 'A'
  AND p.numero = 12;

ROLLBACK;
