CREATE TABLE IF NOT EXISTS contributors (
  login text
  ,repo_id int
  ,first_commit_at TIMESTAMP WITH TIME ZONE
  ,commit_json jsonb
  ,PRIMARY KEY (login, repo_id)
  ,FOREIGN KEY (repo_id) REFERENCES repositories (id)
);
