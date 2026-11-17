
-- Test d'annulation et de remise en vente
-- Toutes les modifications seront annulées à la fin.

BEGIN;

-- 1. Création de deux spectateurs fictifs
INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe_hash)
VALUES
('Test', 'Alice', 'alice-annulation@example.com', 'hash-test'),
('Test', 'Bob', 'bob-annulation@example.com', 'hash-test');

-- 2. Création du film
INSERT INTO films (titre, duree_minutes)
VALUES ('Film Test Annulation', 120);

-- 3. Création de la salle
INSERT INTO salles (nom, capacite)
VALUES ('Salle Test Annulation', 100);

-- 4. Création de la place A12
INSERT INTO places (salle_id, rangee, numero)
SELECT id, 'A', 12
FROM salles
WHERE nom = 'Salle Test Annulation';

-- 5. Programmation de la séance
INSERT INTO seances
(film_id, salle_id, date_debut, date_fin, prix)
SELECT f.id, s.id,
       '2026-12-03 20:00:00+01',
       '2026-12-03 22:00:00+01',
       10.00
FROM films f
CROSS JOIN salles s
WHERE f.titre = 'Film Test Annulation'
  AND s.nom = 'Salle Test Annulation';

-- 6. Alice effectue sa réservation
INSERT INTO reservations
(utilisateur_id, seance_id, statut, montant_total)
SELECT u.id, se.id, 'confirmee', 10.00
FROM utilisateurs u
CROSS JOIN seances se
JOIN films f ON f.id = se.film_id
WHERE u.email = 'alice-annulation@example.com'
  AND f.titre = 'Film Test Annulation';

-- 7. Attribution de la place A12 à Alice
INSERT INTO reservation_places
(reservation_id, seance_id, salle_id, place_id)
SELECT r.id, r.seance_id, se.salle_id, p.id
FROM reservations r
JOIN utilisateurs u ON u.id = r.utilisateur_id
JOIN seances se ON se.id = r.seance_id
JOIN places p ON p.salle_id = se.salle_id
WHERE u.email = 'alice-annulation@example.com'
  AND p.rangee = 'A'
  AND p.numero = 12;

-- 8. Annulation de la réservation d'Alice
UPDATE reservations
SET statut = 'annulee'
WHERE utilisateur_id = (
    SELECT id FROM utilisateurs
    WHERE email = 'alice-annulation@example.com'
);

-- 9. Libération de la place A12
UPDATE reservation_places
SET date_liberation = CURRENT_TIMESTAMP
WHERE reservation_id IN (
    SELECT r.id
    FROM reservations r
    JOIN utilisateurs u ON u.id = r.utilisateur_id
    WHERE u.email = 'alice-annulation@example.com'
);

-- 10. Bob réserve la même séance
INSERT INTO reservations
(utilisateur_id, seance_id, statut, montant_total)
SELECT u.id, se.id, 'confirmee', 10.00
FROM utilisateurs u
CROSS JOIN seances se
JOIN films f ON f.id = se.film_id
WHERE u.email = 'bob-annulation@example.com'
  AND f.titre = 'Film Test Annulation';

-- 11. Bob récupère la place A12
INSERT INTO reservation_places
(reservation_id, seance_id, salle_id, place_id)
SELECT r.id, r.seance_id, se.salle_id, p.id
FROM reservations r
JOIN utilisateurs u ON u.id = r.utilisateur_id
JOIN seances se ON se.id = r.seance_id
JOIN places p ON p.salle_id = se.salle_id
WHERE u.email = 'bob-annulation@example.com'
  AND p.rangee = 'A'
  AND p.numero = 12;

-- 12. Affichage des résultats
SELECT
    u.prenom,
    r.statut,
    p.rangee,
    p.numero,
    rp.date_liberation
FROM reservation_places rp
JOIN reservations r ON r.id = rp.reservation_id
JOIN utilisateurs u ON u.id = r.utilisateur_id
JOIN places p ON p.id = rp.place_id
WHERE u.email IN (
    'alice-annulation@example.com',
    'bob-annulation@example.com'
)
ORDER BY u.prenom;

-- 13. Suppression des données fictives
ROLLBACK;
