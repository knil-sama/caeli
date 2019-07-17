CREATE MATERIALIZED VIEW IF NOT EXISTS stats_contributions AS 
SELECT  repositories.name as repository, to_char(first_commit_at,'YYYY-MM') as date, sum(1) as number_of_new_contributors 
FROM repositories INNER JOIN contributors 
ON repositories.id = contributors.repo_id 
GROUP BY repository, date  
ORDER BY repository, date;
CREATE UNIQUE INDEX IF NOT EXISTS stats_contributions_idx
ON stats_contributions (repository, date);
