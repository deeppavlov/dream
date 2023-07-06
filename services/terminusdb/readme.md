
# TerminusDB Service

**TerminusDB Service** is a service for connecting to a TerminusDB server, which runs locally.


To run a TerminusDB server locally, first execute the following command, which starts the terminusdb-server Docker container from the *docker-compose.override.yml* file
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml up --build terminusdb-server
```

Then, ensure you provide the following env variables in the container, that would use the **TerminusDB Service**, in *docker-compose.override.yml*:
* TERMINUSDB_SERVER_URL=http://terminusdb-server:6363
* TERMINUSDB_SERVER_TEAM=admin
* TERMINUSDB_SERVER_DB=<NAME_YOUR_DB>
* TERMINUSDB_SERVER_PASSWORD=root
* INDEX_LOAD_PATH=/root/.deeppavlov/downloads/entity_linking_eng/custom_el_eng_dream

Please update the DB name, as well as the team and password values if you have made any changes to the default Terminusdb settings.


## Example
An example of connecting to the database after running the server is demonstrated in *terminusdb/test.py*.