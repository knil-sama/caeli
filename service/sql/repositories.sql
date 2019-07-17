CREATE TABLE IF NOT EXISTS repositories (
  id int PRIMARY KEY
  ,name text
  ,owner text
  ,last_commit_check TIMESTAMP WITH TIME ZONE
  ,create_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  ,repo_json jsonb
);
