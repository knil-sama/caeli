-- name: create_repositories#
-- Create table repositories if not exists
CREATE TABLE IF NOT EXISTS repositories (
  id int PRIMARY KEY
  ,name text
  ,owner text
  ,last_commit_check TIMESTAMP WITH TIME ZONE
  ,create_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  ,update_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
  ,repo_json jsonb
);

-- name: update_last_commit_check_repositories!
-- Update last commit check date
UPDATE repositories
SET last_commit_check = :last_commit_check, update_at = CURRENT_TIMESTAMP
WHERE id = :repo_id;

-- name: upsert_repositories*!
-- Insert only new values into repositories
INSERT INTO repositories 
(id,name,owner,last_commit_check, repo_json)
VALUES (:repo_id, :name, :owner, NULL, :repo_json)
ON CONFLICT (id)
DO NOTHING;

-- name: select_repositories
-- list
SELECT id, owner, name, last_commit_check 
FROM repositories
ORDER BY create_at ASC;
