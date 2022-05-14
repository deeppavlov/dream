# Image Captioning service

## Running server

```sh
sudo AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up --build image-captioning
```

## Testing

```sh
./test.sh
```
