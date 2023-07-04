
# TerminusDB Service

**TerminusDB Service** is a service for connecting to a TerminusDB database server, which runs locally.


To run a TerminusDB server locally, first execute the following command, which starts the terminusdb-server Docker container from the *docker-compose.override.yml* file
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml up --build terminusdb-server
```

Then, ensure you provide the following env variables in *.env*:
* TERMINUSDB_SERVER_URL=http://terminusdb-server:6363
* TERMINUSDB_SERVER_TEAM=admin
* TERMINUSDB_SERVER_DB=<NAME_YOUR_DB>

in *.env_secret*:
* TERMINUSDB_SERVER_PASSWORD=root

Please update the team and password values if you have made any changes from the default settings.


## Example
An example of connecting to the database after running the server is demonstrated in *terminusdb/test.py*.