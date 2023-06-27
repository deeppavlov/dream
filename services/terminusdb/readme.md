
# TerminusDB Service

**TerminusDB Service** is a service for connecting to a TerminusDB database server, either remotely or locally.


## To connect locally
To run a TerminusDB server locally, execute the following command, which starts the terminusdb-server Docker container from the *docker-compose.override.yml* file
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml up --build terminusdb-server
```

## To connect remotely
To connect to a remote TerminusDB server, run the terminusdb-server Docker container from the *proxy.yml* file. Modify the PROXY_PASS value in the file according to your server's URL.
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml -f assistant_dists/dream_kg/proxy.yml -p --build terminusdb-server
```

An example of connecting to the database after running the server is demonstrated in *terminusdb/test.py*.