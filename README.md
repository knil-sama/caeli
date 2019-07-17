[![CircleCI](https://circleci.com/gh/knil-sama/caeli.svg?style=svg)](https://circleci.com/gh/knil-sama/caeli)

# caeli

This project use github api and expose stats about it on a REST API.

# Stats displayed

+ New contributors by github repository for each month since project creation

Run it either with:
`GITHUB_TOKEN=XXXXX docker-compose up --build caeli_api`  
Or this if you don't have generated a github token api:
`docker-compose up --build caeli_api`  

then you can access it at 

`http GET localhost:5000/stats`

# Constraint for github api

https://developer.github.com/v3/rate_limit/

## Using REST API

https://developer.github.com/v3/rate_limit/

### Core api

1) First try

Based on list of repositories for a specific organisation/user

Fetch all existing contributors for a said repository : https://developer.github.com/v3/repos/#list-contributors
`r=requests.get(f"{URL_GITHUB_API}/repos/{source}/{repository}/contributors")`
 
Then for each contributor fetch their oldest commit (min call 1 max call 2)

```
# already order from most recent to oldest
r=requests.get(f"{URL_GITHUB_API}/repos/{source}/{repository}/commits", params={"author":user})
if "url" in r.links.get("last"):
r = requests.get(r.links["last"]["url"])
return r.json()[-1]
```
We can then store the date of their first commit that we use to generate expected "new contributor stats"

Sadly this don't work because of github limitation for `/contributors`
```
GitHub identifies contributors by author email address. This endpoint groups contribution counts by GitHub user, which includes all associated email addresses.
To improve performance, only the first 500 author email addresses in the repository link to GitHub users.
The rest will appear as anonymous contributors without associated GitHub user information.
```

2) Second try

Based on list of repositories for a specific organisation/user that we store in our database
 
Fetch all commit of a specific repo from oldest to most recent if they contain user we didn't already have stored,  
save them to the database with the date of the commit and the commit itself,  
then continue until we reach rate limite and update date last checked commit in repositories table
Refresh of the view is done in a separate thread

### Search api

Search api rely on a keyword based query that also allow to add some qualifier to work, sadly you can't make a search without using keyword  
So for example, I can't list all user that commited to facebook project with something like
`curl https://api.github.com/search/users?q=*+org:facebook`


## Using GraphQL

Github also provide a GraphQL interface 

https://developer.github.com/v4/guides/resource-limitations/

Because of the nature of GraphQL you got complicated rate limiting system with a score notation system 
that make everything harder so we will not use it for now

# Running test

`docker-compose up --build tests_api`  
`docker-compose up --build tests_service`
