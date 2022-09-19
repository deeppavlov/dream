# What Is Deepy?
Deepy is a free, open-source Multiskill AI Assistant built using DeepPavlov Conversational AI Stack. It is  built on top of DeepPavlov Agent running as container in Docker. It runs on x86_64 machines, and prefers having NVIDIA GPUs on the machine. 

**Why Deepy?**

Deepy was inspired by Gerty 3000, a moonbase A.I. Assistant from the Moon Movie made by Duncan Jones.

![img](https://cdn-images-1.medium.com/max/800/0*HarsFmC8UKJBaNU6.jpg)

## Learn More About Deepy
Official wiki is located here: [Deepy Wiki](https://github.com/deeppavlov/assistant-base/wiki).

## Distributions
You can find distributions in the /assistant_dists subdirectory of the repository. Learn more about distributions here: [Distributions](https://github.com/deeppavlov/assistant-base/wiki/Distributions) 

# Quick Demo
1. Clone repository
2. Switch to its directory: `cd deepy`
3. Build and run it: `docker-compose up --build`

DeepPavlov's Agent API will run on `http://localhost:4242'. You can learn about its API from the [DeepPavlov Agent Docs](https://deeppavlov-agent.readthedocs.io/en/latest/)

All dialogs will be saved in **dp-agent** database running in **mongo** container.

You can talk to the system through CLI by using these commands:

`$: docker-compose exec agent bash`

`$(inside docker): python -m deeppavlov_agent.run`

Then you'll have to supply user's name, and you'll be able to talk to the machine

## ASR & TTS
You can add custom docker-compose file called `asr_tts.yml` located in `/assistant_dists` subdirectory to your `docker-compose` command like this:

`docker-compose -f docker-compose.yml -f assistant_dists/asr_tts.yml up --build`

After that you'll be able to interact with Deepy through the ASR service to provide speech input via its `http://_service_name_:4343/asr?user_id=` endpoint.  Attach recorded voice as a `.wav` file, 16KHz.

You can use either NeMo or Clone TTS service by sending batches of text phrases to its `http://_tts_service_name:_tts_service_port_/tts?text=_your_text_here_` endpoint.

## Bonus: Check Out GERTY 3000 Replica made by Markus Wobisch
**IMPORTANT** This project isn't related to ours, though we'd be thrilled for it to run our Deepy! )

![image](https://user-images.githubusercontent.com/5264043/112886628-d6720900-90da-11eb-9c97-addd8b63f97e.png)

Read more in Markus Wobisch's [Blog](http://markus-wobisch.blogspot.com/2020/05/building-gerty-3000-replica-part-1.html)
