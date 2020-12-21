FROM amazon/aws-cli as aws

FROM docker/compose:debian-1.27.4 as docker

FROM debian:stable-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install \
    --no-install-recommends \
    -qqy \
    wget \
    curl \
    ca-certificates \
    python3.7 \
    python3-pip \
    python3-setuptools \
 && rm -rf /var/lib/apt/lists /var/cache/apt/archives

RUN curl -s -L https://storage.googleapis.com/kubernetes-release/release/$(wget -q -O - https://storage.googleapis.com/kubernetes-release/release/stable.txt -O -)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

COPY --from=docker /usr/local/bin/docker-compose /usr/local/bin/docker-compose
COPY --from=docker /usr/local/bin/docker /usr/local/bin/docker
RUN chmod +x /usr/local/bin/docker-compose /usr/local/bin/docker

COPY --from=aws /usr/local/aws-cli/ /usr/local/aws-cli/
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
