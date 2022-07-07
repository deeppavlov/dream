Create `local.yml`:
```
python3 utils/create_local_yml.py -p -d assistant_dists/dream_sfc/ -s dff-book-sfc-skill
```

Run distribution:
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_sfc/docker-compose.override.yml -f assistant_dists/dream_sfc/dev.yml -f assistant_dists/dream_sfc/local.yml up --build --remove-orphans --force-recreate
```

Go to localhost:4242 and send POST requests like this:
```
{
	"user_id": "MyDearFriend",
	"payload": "hi how are you"
}
```
