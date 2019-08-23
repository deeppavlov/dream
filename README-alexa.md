# Alexa skill based on DeepPavlov Agent

CoBotQA miniskill
========================
CoBotQA miniskill sends requests to CoBot's services. Two environment variables
should be set to use this miniskill:
 * COBOT_API_KEY - API key given to our Team
 * COBOT_QA_SERVICE_URL - service url, could be found in Trello

How to run and test
=======================

```
$: docker-compose -f docker-compose.yml -f skills.yml up --build
$: docker-compose -f docker-compose.yml -f skills.yml exec agent bash
$(inside docker): python3 -m core.run
```


.env file
=======================

В корне нужно сделать .env файл со следующими полями. Значения полей ищи в Trello.

```
EXTERNAL_FOLDER=/path
COBOT_API_KEY=apikey
COBOT_QA_SERVICE_URL=url
TELEGRAM_TOKEN=token
TELEGRAM_PROXY=proxy

```


docker stack deploy
=======================

1. Docker-machine install https://docs.docker.com/machine/install-machine/

`base=https://github.com/docker/machine/releases/download/v0.16.0 &&
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&
  sudo mv /tmp/docker-machine /usr/local/bin/docker-machine`

2.

https://www.digitalocean.com/community/tutorials/how-to-configure-the-linux-firewall-for-docker-swarm-on-ubuntu-16-04

Open protocols and ports between the hosts

The following ports must be available. On some systems, these ports are open by default.

    TCP port 2377 for cluster management communications
    TCP and UDP port 7946 for communication among nodes
    UDP port 4789 for overlay network traffic

```
ufw allow 22/tcp
ufw allow 2376/tcp
ufw allow 2377/tcp
ufw allow 7946/tcp
ufw allow 7946/udp
ufw allow 4789/udp
ufw allow 2275/udp
ufw allow 2275/tcp
ufw reload
ufw enable
systemctl restart docker
```

2.  https://dev.to/zac_siegel/using-docker-machine-to-provision-a-remote-docker-host-1267
```
➜  dp-agent-mipt git:(feature/telegram-bot-44) ✗ docker-machine create \       
--driver generic \
--generic-ip-address=10.11.1.75 \    
--generic-ssh-port 2275 \
--generic-ssh-user admin \
--generic-ssh-key ~/.ssh/id_rsa \
staging

```

3. `eval $(docker-machine env myvm1)`
4. `docker-compose -f docker-compose.yml -f skills.yml -f telegram.yml -f staging.yml build`
4. `docker service create --name registry --publish published=5000,target=5000 registry:2`
5. `➜  dp-agent-mipt git:(feature/telegram-bot-44) ✗ docker-compose -f docker-compose.yml -f skills.yml -f telegram.yml -f staging.yml push`
