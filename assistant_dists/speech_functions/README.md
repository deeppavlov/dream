Run distribution:
```
docker-compose -f docker-compose.yml -f assistant_dists/speech_functions/docker-compose.override.yml -f assistant_dists/speech_functions/dev.yml -f assistant_dists/speech_functions/proxy.yml up --build --remove-orphans
```

Go to localhost:4242 and send POST requests like this:
```
{
	"user_id": "MyDearFriend",
	"payload": "hi how are you"
}
```
