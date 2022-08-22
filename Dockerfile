FROM python:3.10-slim as build
ENV workdir=/app
RUN mkdir -p $workdir
WORKDIR $workdir
RUN apt-get update
RUN apt-get install -y openssl ca-certificates
RUN apt-get install -y libffi-dev build-essential libssl-dev git rustc cargo
RUN pip install pip -U
RUN pip install poetry -U
# Install dependencies first
COPY poetry.lock pyproject.toml $workdir
RUN poetry install --no-root --no-dev

RUN apt-get remove --purge -y libffi-dev build-essential libssl-dev git rustc cargo
RUN rm -rf /root/.cargo

# Copy source code as late as possible to take advantages about layer cache
COPY . $workdir
RUN poetry install --no-dev


# Squash layers
# FROM python:3.10-slim

# COPY --from=build / /   # doesn't work on kaniko
# Waiting for: https://github.com/GoogleContainerTools/kaniko/pull/1724
# ENV workdir=/app
# COPY --from=build /usr /usr
# COPY --from=build /home /home
# COPY --from=build /opt /opt
# COPY --from=build /lib /lib
# COPY --from=build /app /app

# WORKDIR /app
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/gmail2s3/prometheus
CMD ["./run-server.sh"]
