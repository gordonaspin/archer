FROM python:3.12-alpine AS base

FROM base AS builder

ARG OPT

COPY dist/*.whl /tmp/
RUN python3 -m ensurepip
RUN pip install --upgrade pip setuptools
RUN set -xe \
  && pip install wheel==0.35.1 \
  && pip install /tmp/*.whl \
  && rm /tmp/*.whl \
  && pip list \
  && pip uninstall -y setuptools \
  && archer --password ${OPT}
COPY dist/*.whl /tmp/


#ARG USER_ID
#RUN adduser --disabled-password --gecos '' --uid $USER_ID docker
#USER docker
ENTRYPOINT [ "archer" ]
