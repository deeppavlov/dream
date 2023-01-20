## Setting up server

https://minecraft.fandom.com/wiki/Tutorials/Setting_up_a_server

https://www.minecraft.net/en-us/download/server

`home/mtalimanchuk/projects/minecraft-server`

Download server.jar and run it with:
```
nohup java -Xmx1024M -Xms1024M -jar server1_18.jar nogui &
```

Server properties are defined in `world.properties`

World data resides in `/world` directory. Remove it to generate new world.


## Run distribution
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_minecraft/docker-compose.override.yml -f assistant_dists/dream_minecraft/dev.yml -f assistant_dists/dream_minecraft/proxy.yml up --build
```

## Rerun the minecraft connector
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_minecraft/docker-compose.override.yml -f assistant_dists/dream_minecraft/dev.yml -f assistant_dists/dream_minecraft/proxy.yml up --build minecraft dff-minecraft-skill
```

## Say hi to the bot!
