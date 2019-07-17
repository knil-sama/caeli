FROM python:3.7

COPY requirements.txt .
COPY requirements_tests.txt .

ARG BUILD_TEST=""

RUN pip install --upgrade pip && if [ "$BUILD_TEST" = "yes" ] ; then pip install --upgrade -r requirements_tests.txt ; else pip install --upgrade -r requirements.txt ; fi

RUN groupadd -g 999 caeli_service \
  && useradd -ms /bin/bash -u 999 -g caeli_service caeli_service

RUN mkdir /opt/service \
  && chown caeli_service:caeli_service /opt/service

WORKDIR /opt/service

COPY --chown=caeli_service:caeli_service . /opt/service

USER caeli_service

ENV PYTHONPATH $PYTHONPATH:/opt/
