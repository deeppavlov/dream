Create `local.yml`:
```
python3 utils/create_local_yml.py -d assistant_dists/dream_sfc/ -s dff-book-sfc-skill
```

Run distribution:
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_sfc/docker-compose.override.yml -f assistant_dists/dream_sfc/local.yml up --build
```

Go to localhost:4242 and send POST requests like this:
```
{
	"user_id": "MyDearFriend",
	"payload": "hi how are you"
}
```
