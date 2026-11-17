# Sources de données

Les fichiers ne sont pas versionnés : ils sont volumineux et soumis aux licences de leurs fournisseurs.
Placez-les dans `data/raw/`, ou indiquez un autre dossier avec `PERFILM_DATA_DIR`.

| Fichier attendu          | Contenu                                                            | Provenance |
|--------------------------|--------------------------------------------------------------------|------------|
| `wikipedia-movies.json`  | Infobox Wikipedia de ~7 000 films (1990-2018) : budget, box office, sortie… | Extraction Wikipedia (jeu « Movies-ETL ») |
| `movies_metadata.csv`    | Métadonnées TMDB : genres, studios, pays, langue, durée, budget, revenu | Kaggle, *The Movies Dataset* (rounakbanik) |
| `ratings.xlsb` / `ratings.csv` | Évaluations des spectateurs (`userId, movieId, rating, timestamp`) | MovieLens (GroupLens), inclus dans *The Movies Dataset* |
| `IMDb movies.csv`        | Notes IMDb (`imdb_title_id, avg_vote, director, …`)                  | Kaggle, *IMDb movies extensive dataset* (stefanoleone992) |

Remarques :

- `ratings.xlsb` est le format utilisé dans le rapport. Le CSV MovieLens d'origine est accepté directement : le pipeline détecte `.xlsb`, `.xlsx` ou `.csv`.
- `movieId` (MovieLens) correspond à la colonne `id` de `movies_metadata.csv`.
- La fusion entre Wikipedia, Kaggle et IMDb se fait sur l'identifiant IMDb (`tt…`).
- `IMDb movies.csv` est optionnel. S'il est absent, l'enrichissement des notes et des réalisateurs est ignoré.

## Jeu d'échantillon

Pour tester la chaîne complète sans rien télécharger :

```bash
python -m perfilm.sample_data data/sample
perfilm --data-dir data/sample --database-url sqlite:///perfilm-demo.db
```
