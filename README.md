# What Is Deepy?
Deepy is a free, open-source Multiskill AI Assistant built using DeepPavlov Conversational AI Stack. It is  built on top of DeepPavlov Agent running as container in Docker. It runs on x86_64 machines, and prefers having NVIDIA GPUs on the machine. 

**Why Deepy?**

Deepy was inspired by Gerty 3000, a moonbase A.I. Assistant from the Moon Movie made by Duncan Jones.

![img](https://cdn-images-1.medium.com/max/800/0*HarsFmC8UKJBaNU6.jpg)

## Learn More About Deepy
Official wiki is located here: [Deepy Wiki](https://github.com/deepmipt/assistant-base/wiki).

## Distributions
You can find distributions in the /assistant_dists subdirectory of the repository. Learn more about distributions here: [Distributions](https://github.com/deepmipt/assistant-base/wiki/Distributions) 

# Quick Demo
1. Clone repository
2. Switch to its directory: `cd assistant-base`
3. Build and run it: `docker-compose up --build`

API will run on `http://localhost:4242'.

All dialogs will be saved in **dp-agent** database running in **mongo** container.

## ASR & TTS
You can add custom docker-compose file called `asr_tts.yml` located in `/assistant_dists` subdirectory to your `docker-compose` command like this:

`docker-compose -f docker-compose.yml -f assistant_dists/asr_tts.yml up --build`

After that you'll be able to interact with Deepy through the ASR service to provide speech input via its `http://_service_name_:4343/asr?user_id=` endpoint.  Attach recorded voice as a `.wav` file, 16KHz.

You can use either NeMo or Clone TTS service by sending batches of text phrases to its `http://_tts_service_name:_tts_service_port_/tts?text=_your_text_here_` endpoint.

