# syntax = docker/dockerfile:1.4.0

ARG FROM_IMAGE="python/3.9-alpine"

## build the image
#
FROM "${FROM_IMAGE}"

COPY ./pydepgroups.py ./requirements.txt /
RUN pip install -r requirements.txt

ENTRYPOINT ["/pydepgroups.py"]
