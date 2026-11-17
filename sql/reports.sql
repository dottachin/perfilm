-- =====================================================================
-- Requêtes SQL équivalentes aux rapports Knowage du rapport (figures 38 à 40)
-- Les montants sont pondérés par `poids` pour éviter le double comptage
-- d'un film présent sur plusieurs lignes (multi-genres, multi-pays…).
-- =====================================================================

-- Figure 38 : distribution des genres des films du Royaume-Uni par budget et revenu (2007-2017)
SELECT g.genre,
       SUM(f.budget  * f.poids) AS budget,
       SUM(f.revenue * f.poids) AS revenue
FROM fact_movies f
JOIN genre g  ON g.id_genre = f.id_genre
JOIN pays p   ON p.id_pays  = f.id_pays
JOIN "date" d ON d.id_date  = f.id_date
WHERE p.pays = 'UK' AND d.annee BETWEEN 2007 AND 2017
GROUP BY g.genre
ORDER BY revenue DESC NULLS LAST;

-- Figure 39 : ratio revenu / budget par genre et par année, États-Unis (2007-2017)
SELECT d.annee,
       g.genre,
       SUM(f.revenue * f.poids) / NULLIF(SUM(f.budget * f.poids), 0) AS ratio_revenu_budget
FROM fact_movies f
JOIN genre g  ON g.id_genre = f.id_genre
JOIN pays p   ON p.id_pays  = f.id_pays
JOIN "date" d ON d.id_date  = f.id_date
WHERE p.pays = 'USA' AND d.annee BETWEEN 2007 AND 2017
  AND f.budget IS NOT NULL AND f.revenue IS NOT NULL
GROUP BY d.annee, g.genre
ORDER BY d.annee, ratio_revenu_budget DESC NULLS LAST;

-- Figure 40 : ratio revenu / budget par genre, tous pays (2007-2017)
SELECT g.genre,
       SUM(f.revenue * f.poids) / NULLIF(SUM(f.budget * f.poids), 0) AS ratio_revenu_budget,
       SUM((f.revenue - f.budget) * f.poids)                         AS marge
FROM fact_movies f
JOIN genre g  ON g.id_genre = f.id_genre
JOIN "date" d ON d.id_date  = f.id_date
WHERE d.annee BETWEEN 2007 AND 2017
  AND f.budget IS NOT NULL AND f.revenue IS NOT NULL
GROUP BY g.genre
ORDER BY marge DESC;
