FROM python:3.10

RUN mkdir /src /src/common

COPY ./skill_selectors/rule_based_selector/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skill_selectors/rule_based_selector/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
