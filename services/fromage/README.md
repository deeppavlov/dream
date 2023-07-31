# FROMAGe Service
**FROMAGe** is a service that is used to get an image and respond accordingly to the user's questions. FROMAGe is based on grounding pretrained language models to the visual domain ([Grounding Language Models to Images for Multimodal Inputs and Outputs](https://arxiv.org/abs/2301.13823)). 

GPU RAM 5 GB, RAM 5 GiB. 

## Running server

```sh
sudo AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up --build fromage
```

## Testing

```sh
./test.sh
```
