# Image Captioning Service
**Image Captioning** is an OFA-based service that is used to get a text representation of a received image and respond accordingly. OFA is a unified multimodal pretrained model that unifies modalities and tasks to a simple sequence-to-sequence learning framework ([Unifying Architectures, Tasks, and Modalities Through a Simple Sequence-to-Sequence Learning Framework](http://arxiv.org/abs/2202.03052)). It also uses fairseq - a sequence modeling toolkit for training custom models for text generation tasks ([FAIRSEQ: A Fast, Extensible Toolkit for Sequence Modeling](https://aclanthology.org/N19-4009.pdf)). 

One 256 X 256 picture is processed ~0.7 sec (on average).

GPU RAM ~5.4 GiB, RAM ~4 GiB. 

## Running server

```sh
sudo AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up --build image-captioning
```

## Testing

```sh
./test.sh
```
