# syntax = docker/dockerfile:1.4

# Transient Python Build Image
# ------------------------------------------------------------------------------
# Build up the Python dependencies
FROM python:3.6-slim-bullseye as python-build

ARG DEV_MODE

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    DEV_MODE=$DEV_MODE

COPY --from=busybox:1.30 /bin/wget /tmp/wget
COPY .docker/install-system-packages.sh /tmp
RUN /tmp/install-system-packages.sh \
    apt-utils \
    build-essential \
    default-libmysqlclient-dev

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH VIRTUAL_ENV=/venv DEV_MODE=$DEV_MODE

ENV TINI_VERSION v0.19.0
RUN /tmp/wget https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini -O /venv/bin/tini
RUN chmod +x /venv/bin/tini

COPY .docker/install-python-packages.sh /tmp
COPY requirements.txt requirements.*.txt /tmp/
RUN /tmp/install-python-packages.sh

# Run Image
# ------------------------------------------------------------------------------
# The final image that is used to execute everything
FROM python:3.6-slim-bullseye as run-stage

ARG GIT_COMMIT
ARG GIT_VERSION
ARG VERSION
ARG RUN_TESTS=0

RUN useradd --create-home nuremberg
WORKDIR /home/nuremberg

# Install packages required for run time
# > default-libmysqlclient-dev - mysql drivers
# > xz-utils curl - needed for nodejs / npm install
COPY .docker/install-system-packages.sh /tmp
RUN /tmp/install-system-packages.sh default-libmysqlclient-dev xz-utils curl

RUN curl https://nodejs.org/dist/v16.15.1/node-v16.15.1-linux-x64.tar.xz -O
RUN tar -xJvf node-v16.15.1-linux-x64.tar.xz && mv node-v16.15.1-linux-x64 /usr/local/lib/nodejs
ENV PATH=$PATH:/usr/local/lib/nodejs/bin
RUN npm install --location=global less

USER nuremberg

# Copy over the code, virtualenv, and collected static changing it to be owned by our new user:
COPY --chown=nuremberg:nuremberg ./nuremberg /home/nuremberg/nuremberg
COPY --chown=nuremberg:nuremberg manage.py pytest.ini /home/nuremberg/
COPY --from=python-build --chown=nuremberg:nuremberg /venv /venv
# COPY --from=node-build --chown=nuremberg:nuremberg /app/node_modules/less/bin/lessc /venv/bin

# When Docker image is stopped, send a SIGINT (KeyboardInterrupt exception by
# default in Python) instead of SIGTERM. Really you should listen for SIGTERM,
# but not all programs do (see https://hynek.me/articles/docker-signals/).
STOPSIGNAL SIGINT

ENV PYTHONFAULTHANDLER=true \
    PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv \
    RUN_TESTS=$RUN_TESTS \
    GIT_COMMIT=$GIT_COMMIT \
    GIT_VERSION=$GIT_VERSION \
    RELEASE_VERSION=$VERSION

EXPOSE 8000

# Entrypoint that handles signals correctly (see
# https://hynek.me/articles/docker-signals/ for details):
# 1. With tini as init script.
# 2. Use [] syntax so it doesn't get wrapped with "/bin/sh -c" that screws up
#    signal delivery.
# 3. "-g" kills all processes when the container is told to shut down, instead
#    of just the parent process. For details se
#     https://github.com/krallin/tini#process-group-killing
COPY .docker/entrypoint.sh /venv/bin
ENTRYPOINT ["/venv/bin/tini", "-g", "-s", "--"]

# By default run entrypoint.sh, if other arguments are given run those instead:
CMD ["/venv/bin/entrypoint.sh"]
