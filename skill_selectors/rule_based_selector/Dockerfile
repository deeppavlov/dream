FROM python:3.7.4

ARG HIGH_PRIORITY_INTENTS=1
ENV HIGH_PRIORITY_INTENTS ${HIGH_PRIORITY_INTENTS}
ARG RESTRICTION_FOR_SENSITIVE_CASE=1
ENV RESTRICTION_FOR_SENSITIVE_CASE ${RESTRICTION_FOR_SENSITIVE_CASE}
ARG ALWAYS_TURN_ON_ALL_SKILLS=0
ENV ALWAYS_TURN_ON_ALL_SKILLS ${ALWAYS_TURN_ON_ALL_SKILLS}
ARG ALWAYS_TURN_ON_GIVEN_SKILL=0
ENV ALWAYS_TURN_ON_GIVEN_SKILL ${ALWAYS_TURN_ON_GIVEN_SKILL}

RUN mkdir /src
RUN mkdir /src/common

COPY ./skill_selectors/rule_based_selector/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skill_selectors/rule_based_selector/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
