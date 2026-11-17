
# Guide de contribution – Le Grand Cinéma

## 1. Organisation du projet

Le projet utilise Git et GitHub pour assurer le suivi
des modifications et faciliter le développement itératif.

## 2. Convention de nommage des branches

- main : branche stable destinée aux versions de production.
- develop : branche d'intégration des fonctionnalités.
- feature/nom-fonctionnalite : développement d'une fonctionnalité.
- fix/nom-correction : correction d'un bug.
- docs/nom-documentation : ajout ou modification de documentation.

Exemples :
- feature/gestion-films
- feature/reservation-place
- feature/billet-numerique
- fix/double-reservation
- docs/api-swagger

Les noms des branches sont écrits en minuscules,
sans espaces ni accents, avec des tirets pour séparer les mots.

## 3. Processus de développement

1. Se placer sur develop et récupérer les dernières modifications.
2. Créer une branche feature/ à partir de develop.
3. Développer la fonctionnalité.
4. Ajouter des tests et vérifier leur exécution.
5. Créer des commits explicites.
6. Publier la branche sur GitHub.
7. Ouvrir une Pull Request vers develop.
8. Vérifier le code et les tests avant la fusion.

La branche main reçoit uniquement les versions
stables validées depuis develop.

## 4. Convention des commits

Les messages suivent une convention simple :

- feat: ajout d'une fonctionnalité
- fix: correction d'un bug
- docs: modification de la documentation
- test: ajout ou modification des tests
- refactor: amélioration du code sans changement fonctionnel
- chore: maintenance du projet

Exemples :
- feat: ajout du catalogue des films
- feat: création du modèle Reservation
- fix: prévention des doubles réservations
- test: ajout des tests de réservation

## 5. Qualité et sécurité

- Ne jamais publier de mots de passe, tokens ou secrets.
- Utiliser des variables d'environnement pour la configuration.
- Respecter les conventions de style Python.
- Tester les fonctionnalités avant toute fusion.
- Vérifier les entrées utilisateurs et les droits d'accès.
- Documenter les changements importants.
