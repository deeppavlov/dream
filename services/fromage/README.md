# FROMAGe Service
**FROMAGe** is a service that is used to process an input image and respond to the user's questions accordingly. It is based on the [FROMAGe](https://github.com/kohjingyu/fromage/tree/main) model from [Grounding Language Models to Images for Multimodal Inputs and Outputs](https://arxiv.org/abs/2301.13823).

GPU RAM 20 GB, RAM 45 GB. 

## Running server

```sh
sudo AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream_multimodal/docker-compose.override.yml -f assistant_dists/dream_multimodal/dev.yml -f assistant_dists/dream_multimodal/test.yml up --build fromage
```

## Testing

```sh
./test.sh
```
