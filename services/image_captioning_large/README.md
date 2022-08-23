# Image Captioning Service (Large)

Image Captioning Service (Large) is the large version of the Image Captioning Service that provides text descriptions of received images. 

One 256 X 256 image is processed ~5 s.

RAM ~1.5GB, GPU RAM 3Gb. 
## Running server

```sh
sudo AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up --build image-captioning-large
```

## Testing

```sh
./services/image_captioning_large/test.sh
```
