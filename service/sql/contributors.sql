-- name: create_contributors#
-- Create table contributors if not exists
CREATE TABLE IF NOT EXISTS contributors (
  login text
  ,repo_id int
  ,first_commit_at TIMESTAMP WITH TIME ZONE
  ,commit_json jsonb
		,create_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
		,update_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
  ,PRIMARY KEY (login, repo_id)
  ,FOREIGN KEY (repo_id) REFERENCES repositories (id)
);
-- name: list_contributors_by_id
-- Get all contributors for a specific repo as list of dict
SELECT *
FROM contributors 
WHERE repo_id = :repo_id
ORDER BY create_at ASC;

-- name: upsert_contributors*!
-- Insert contributors and update first commit if more recent
INSERT INTO contributors 
(login, repo_id, first_commit_at, commit_json) 
VALUES (:login, :repo_id, :first_commit_at, :commit_json)
ON CONFLICT (login, repo_id) DO UPDATE 
SET first_commit_at = EXCLUDED.first_commit_at, update_at = CURRENT_TIMESTAMP, commit_json = EXCLUDED.commit_json
WHERE contributors.first_commit_at > EXCLUDED.first_commit_at;
