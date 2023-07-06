
# TerminusDB Service

**TerminusDB Service** is a service for connecting to a TerminusDB database server, either remotely or locally.


## To connect locally
First, to run a TerminusDB server locally, execute the following command, which starts the terminusdb-server Docker container from the *docker-compose.override.yml* file
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


## To connect remotely
First, to connect to a remote TerminusDB server, run the terminusdb-server Docker container from the *proxy.yml* file. Modify the PROXY_PASS value in the file according to your server's URL.
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml -f assistant_dists/dream_kg/proxy.yml -p --build terminusdb-server
```

Then, ensure you provide the following env variables in *.env*:
* TERMINUSDB_SERVER_URL=<YOUR_SERVER_URL> # https://7063.deeppavlov.ai/ in case you use our server
* TERMINUSDB_SERVER_TEAM=admin
* TERMINUSDB_SERVER_DB=<NAME_YOUR_DB>

in *.env_secret*:
* TERMINUSDB_SERVER_PASSWORD=<YOUR_SERVER_PASSWORD>

Please update the team value if you have made any changes from the default settings.


## Example
An example of connecting to the database after running the server is demonstrated in *terminusdb/test.py*.