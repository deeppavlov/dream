FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skill_selectors/rule_based_selector/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skill_selectors/rule_based_selector/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
