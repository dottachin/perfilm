# PerFilm : analyse décisionnelle des performances des films

> Projet de Fin d'Études, Licence Sciences Mathématiques et Informatique (option SID)
> Faculté des Sciences Aïn Chock, Université Hassan II de Casablanca, 2020/2021
> **Réalisé par** Issam Echchadli. **Encadré par** Pr. Rim Koulali

*Conception et réalisation d'une application décisionnelle dédiée à l'analyse des performances des films.*

Ce dépôt est une **reconstruction du code** à partir du rapport de PFE (non versionné), le code d'origine ayant été perdu.
La reconstruction suit les choix, noms et étapes du rapport. Quelques défauts de l'original sont corrigés : voir [Écarts avec le rapport](#écarts-avec-le-rapport).

## Objectif

Mettre à la disposition des acteurs du cinéma, en particulier des producteurs indépendants, un système d'aide à la décision **open source**.
Le système fusionne les données économiques des films (budget, revenu) avec les évaluations des spectateurs, pour des analyses multicritères : genre, pays, studio, réalisateur, langue, période.

## Architecture

```
 wikipedia-movies.json ─┐
 movies_metadata.csv  ──┤   ┌──────────────────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐
 ratings.xlsb         ──┼──▶│ ETL Python (pandas)      │──▶│ PostgreSQL   │──▶│ Cube ROLAP    │──▶│ Knowage      │
 IMDb movies.csv      ──┘   │ extract/transform/load   │   │ schéma étoile│   │ Mondrian      │   │ rapports/DB  │
                            └──────────────────────────┘   └──────────────┘   └───────────────┘   └──────────────┘
```

### Pipeline ETL (figure 22)

lecture → sélection des données pertinentes → renommage des colonnes → harmonisation → regroupement des colonnes de langues →
suppression des colonnes ≥ 90 % nulles → correction grammaticale (regex) → uniformisation des valeurs monétaires →
fusion des sources → création des dimensions → création de la table de faits → chargement

| Module | Rôle |
|---|---|
| [`perfilm/extract.py`](src/perfilm/extract.py) | Lecture JSON / CSV / Excel binaire (`.xlsb`) |
| [`perfilm/transform/wiki.py`](src/perfilm/transform/wiki.py) | `clean_movie`, `parse_dollars`, analyse des dates et durées par regex |
| [`perfilm/transform/kaggle.py`](src/perfilm/transform/kaggle.py) | Typage et décodage des colonnes JSON TMDB (genres, studios, pays, langues) |
| [`perfilm/transform/merge.py`](src/perfilm/transform/merge.py) | Fusion sur l'identifiant IMDb et règles de résolution des conflits |
| [`perfilm/transform/dimensions.py`](src/perfilm/transform/dimensions.py) | Dimensions et table de faits |
| [`perfilm/schema.py`](src/perfilm/schema.py), [`sql/schema.sql`](sql/schema.sql) | DDL de l'entrepôt (clés primaires et étrangères, index) |
| [`perfilm/load.py`](src/perfilm/load.py) | Chargement idempotent via SQLAlchemy |
| [`perfilm/pipeline.py`](src/perfilm/pipeline.py) | Orchestration et CLI `perfilm` |

### Schéma en étoile (figure 6)

```
            genre(id_genre, genre)              movie(id_movie, titre, titre_original, duree, rating)
          studio(id_studio, studio)      ╲     ╱
              pays(id_pays, pays)    ─── fact_movies ───  date(id_date, date, annee, trimestre, libelle_trimestre,
realisateur(id_realisateur, realisateur)  (budget,          mois, libelle_mois, jour_semaine, libelle_jour_semaine, jour)
  langue(id_langue, langue, langue_complete)  revenue, poids)
```

### OLAP et reporting

- [`olap/movies_mondrian_schema.xml`](olap/movies_mondrian_schema.xml) : cube `movies_cube`. Mesures `budget`, `revenue` et `nb_films`, plus les membres calculés `ratio_revenu_budget` et `marge`.
- [`olap/Template.xml`](olap/Template.xml) : template du document OLAP Knowage (figure 35).
- [`olap/queries.mdx`](olap/queries.mdx) et [`sql/reports.sql`](sql/reports.sql) : requêtes des rapports des figures 38 à 40. Ces rapports présentent la répartition par genre au Royaume-Uni et le ratio revenu/budget aux États-Unis et pour tous les pays, sur 2007-2017.

## Démarrage rapide

```bash
# 1. Environnement Python
uv venv && uv pip install -e ".[dev,explore]"     # ou : python -m venv .venv && pip install -e ".[dev,explore]"

# 2. Essai immédiat sur un jeu d'échantillon synthétique (SQLite)
python -m perfilm.sample_data data/sample
perfilm --data-dir data/sample --database-url sqlite:///perfilm-demo.db

# 3. Chaîne complète
cp .env.example .env                               # renseigner les mots de passe
docker compose up -d warehouse                     # PostgreSQL
# déposer les 4 fichiers sources dans data/raw/ (voir data/README.md)
perfilm                                            # ETL -> PostgreSQL

# 4. OLAP / reporting
docker compose --profile bi up -d                  # Knowage sur http://localhost:8080/knowage
```

Dans Knowage :

1. Créer une *data source* JDBC PostgreSQL : `jdbc:postgresql://warehouse:5432/movies`.
2. Importer `olap/movies_mondrian_schema.xml` dans *Mondrian schemas catalog* sous le nom `movies_schema`.
3. Créer un document OLAP à partir de `olap/Template.xml`.
4. Construire les cockpits : tableaux, camemberts par genre, graphe parallèle budget/revenu, filtres pays, année, trimestre, mois et jour.

## Tests

```bash
pytest          # tests unitaires (regex, parse_dollars…) et test de bout en bout sur SQLite
ruff check .
```

## Écarts avec le rapport

| Rapport (2021) | Reconstruction | Raison |
|---|---|---|
| Mot de passe PostgreSQL écrit en clair dans le notebook | Variables d'environnement (`.env`) | Sécurité |
| Clés de la table de faits contenant les libellés (figure 32) | Remplacement par les identifiants entiers des dimensions | Intégrité référentielle |
| `id_date` de type texte dans la dimension et entier dans les faits | Entier `AAAAMMJJ` des deux côtés, `0` pour une date inconnue | Cohérence |
| Budget et revenu dupliqués sur chaque ligne « explosée » | Colonne `poids` = 1 / nb de lignes du film, mesures Mondrian pondérées | Évite le double comptage d'un film multi-genres |
| Valeurs manquantes perdues lors des jointures | Membre `Inconnu` dans chaque dimension | Aucun fait n'est perdu par les jointures internes du cube |
| Notebook Jupyter unique | Package Python, CLI, tests et notebook d'exploration | Reproductibilité |

## Arborescence

```
src/perfilm/        package ETL
sql/                DDL de l'entrepôt et requêtes des rapports
olap/               schéma Mondrian, template Knowage, requêtes MDX
notebooks/          exploration des sources (figures 11 à 18)
data/               emplacement des sources (non versionnées)
tests/              tests pytest
.claude/            agents et skills Claude Code pour ce projet
```

## Technologies

Python 3 (pandas, NumPy, SQLAlchemy, Matplotlib, Jupyter) · PostgreSQL · Mondrian (Pentaho Schema Workbench) · Knowage · Docker
