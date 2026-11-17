
-- Test 1 : prévention de la double réservation
-- Les données fictives seront annulées.

BEGIN;

INSERT INTO utilisateurs
(nom, prenom, email, mot_de_passe_hash)
VALUES
('Test', 'Alice', 'alice-test@example.com', 'hash-fictif'),
('Test', 'Bob', 'bob-test@example.com', 'hash-fictif');

INSERT INTO films (titre, duree_minutes)
VALUES ('Film Test Réservation', 120);

INSERT INTO salles (nom, capacite)
VALUES ('Salle Test Réservation', 100);

INSERT INTO places (salle_id, rangee, numero)
SELECT id, 'A', 12
FROM salles
WHERE nom = 'Salle Test Réservation';

INSERT INTO seances
(film_id, salle_id, date_debut, date_fin, prix)
SELECT
    f.id,
    s.id,
    '2026-12-02 20:00:00+01',
    '2026-12-02 22:00:00+01',
    10.00
FROM films f
CROSS JOIN salles s
WHERE f.titre = 'Film Test Réservation'
AND s.nom = 'Salle Test Réservation';

INSERT INTO reservations
(utilisateur_id, seance_id, statut, montant_total)
SELECT u.id, se.id, 'confirmee', 10.00
FROM utilisateurs u
CROSS JOIN seances se
JOIN films f ON f.id = se.film_id
WHERE u.email = 'alice-test@example.com'
AND f.titre = 'Film Test Réservation';

INSERT INTO reservation_places
(reservation_id, seance_id, salle_id, place_id)
SELECT r.id, r.seance_id, se.salle_id, p.id
FROM reservations r
JOIN utilisateurs u ON u.id = r.utilisateur_id
JOIN seances se ON se.id = r.seance_id
JOIN places p ON p.salle_id = se.salle_id
WHERE u.email = 'alice-test@example.com'
AND p.rangee = 'A'
AND p.numero = 12;

-- Deuxième réservation pour le même siège

INSERT INTO reservations
(utilisateur_id, seance_id, statut, montant_total)
SELECT u.id, se.id, 'confirmee', 10.00
FROM utilisateurs u
CROSS JOIN seances se
JOIN films f ON f.id = se.film_id
WHERE u.email = 'bob-test@example.com'
AND f.titre = 'Film Test Réservation';

-- Cette insertion doit échouer :
-- A12 est déjà réservée par Alice.

INSERT INTO reservation_places
(reservation_id, seance_id, salle_id, place_id)
SELECT r.id, r.seance_id, se.salle_id, p.id
FROM reservations r
JOIN utilisateurs u ON u.id = r.utilisateur_id
JOIN seances se ON se.id = r.seance_id
JOIN places p ON p.salle_id = se.salle_id
WHERE u.email = 'bob-test@example.com'
AND p.rangee = 'A'
AND p.numero = 12;

ROLLBACK;
