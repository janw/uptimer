# Uptimer 📈

<!-- markdownlint-disable MD033 -->
<div align="center">

**A plugin-based prober to determine website uptime.**

[![Build Status](https://github.com/janw/uptimer/workflows/Build/badge.svg)](https://github.com/janw/uptimer/actions?query=workflow%3ABuild+branch%3Amaster)
[![Tests Status](https://github.com/janw/uptimer/workflows/Tests/badge.svg)](https://github.com/janw/uptimer/actions?query=workflow%3ATests+branch%3Amaster)
[![Code Coverage](https://codecov.io/gh/janw/uptimer/branch/master/graph/badge.svg?token=2I5XYEBZ4W)](https://codecov.io/gh/janw/uptimer)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Dependency management: poetry](https://img.shields.io/badge/deps-poetry-blueviolet.svg)](https://poetry.eustace.io/docs/)

</div>

Uptimer is designed to be modular and extensible, and –by using reader/probe plugins– not only allows for HTTP(S) probing of websites but potentially more low-level protocols (such as TCP, ICMP/ping) and other application layer protocols. The forwarding and processing data is extensible as well, so it is possible to run Uptimer as a single instance that stores results in a database directly, or have an arbitrary number of probe instances that produce results into a Kafka queue, which in turn is being consumed by only a few instances that persist the results into the database.

The heart and core of Uptimer is an equally modular event paradigm that is used to ensure plugin compatibility and validity of data passed between plugins. Should a future to-be-probed protocol require additional properties to be produced, those can be defined in a new event type without the necessity of adapting other reader/writer plugins. Events based on and validated via [JSON Schema](https://json-schema.org/).

Uptimer uses containerization as the primary "packaging" mechanism. Its Docker image is available on [Docker Hub as `docker.io/willhaus/uptimer`](https://hub.docker.com/r/willhaus/uptimer) or `willhaus/uptimer` for short.

In its default usage scenario Uptimer uses Kafka as a message bus to push probe results to, and PostgreSQL as the database to ultimately store the results in. In both the Docker-compose stack as well as the k8s manifests, Uptimer has been preconfigured to use the necessary plugins for this forwarding chain to function. In any case you will **have to provide a Postgres `DATABASE_URL` as well as a `KAFKA_BOOTSTRAP_SERVER` and certificate-based authentication for Kafka**, thus the first step (below) applies to both scenarios.

## Quick Start

This repository includes both a [`docker-compose.yml`](docker-compose.yml) file to run an instance of Uptimer locally, and [Kubernetes manifests](k8s/) with [Kustomize](https://kustomize.io/) configuration to run Uptimer in k8s. The following steps assume

* Either of:
  * Docker to be running and `docker-compose` installed, or
  * a connection to a Kubernetes cluster to be configured and `kubectl` being available at the command line
* A locally clone or copy of this repository, `github.com/janw/uptimer.git`
* A running Postgres instance with an existing database
* A running Kafka instance with an existing topic named `probes` which you connect to via client certificate authentication. This requires a client key/cert pair and adjacent CA certificate

### Configuring Postgres and Kafka connections

1. Create a copy of the `.credentials/*.env.example` files while removing the `.example` suffix:

    ```bash
    cp .credentials/kafka.env.example .credentials/kafka.env
    cp .credentials/postgres.env.example .credentials/postgres.env
    ```

2. Adjust the `KAFKA_BOOTSTRAP_SERVER` in `.credentials/kafka.env` to match your Kafka setup
3. Copy the Kafka authentication files:

    * the client key to `.credentials/service.key`
    * the client certificate to `.credentials/service.cert`
    * the CA certificate to `.credentials/ca.pem`.

4. Adjust the `DATABASE_URL` in `.credentials/kafka.env` to match your Postgres setup. The URL must follow [libpq's connection string](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING) specification.

### Option 1: Using Docker-compose

After configuring the Postgres and Kafka connections, the docker-compose stack can be brought up:

```bash
# EITHER: Using the willhaus/uptimer image from Docker Hub
docker-compose up

# OR: Build the image on-the-fly before starting
docker-compose up --build
```

### Option 2: Using Kubernetes

Bringing up the k8s-based deployment, is just as easy as docker-compose. It is important to use kubectl's `-k` flag though:

```bash
kubectl apply -k k8s/
```
