FROM python:3.6

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN groupadd -g 999 caeli_api \
  && useradd -ms /bin/bash -u 999 -g caeli_api caeli_api

RUN mkdir /opt/api \
  && chown caeli_api:caeli_api /opt/api

WORKDIR /opt/api

COPY --chown=caeli_api:caeli_api . /opt/api

USER caeli_api

ENV PYTHONPATH $PYTHONPATH:/opt/
