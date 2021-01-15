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

Uptimer is packaged using poetry but is also available as a Docker image on [Docker Hub as `docker.io/willhaus/uptimer`](https://hub.docker.com/r/willhaus/uptimer) or `willhaus/uptimer` for short.

In its default usage scenario Uptimer uses Kafka as a message bus to push probe results to, and PostgreSQL as the database to ultimately store the results in. In both the Docker-compose stack as well as the k8s manifests, Uptimer has been preconfigured to use the necessary plugins for this forwarding chain to function. In any case you will **have to provide a Postgres `DATABASE_URL` as well as a `KAFKA_BOOTSTRAP_SERVER` and certificate-based authentication for Kafka**, thus the first step (below) applies to both scenarios.

## Initial Setup

1. After checkout create a Python 3.8 virtual environment and install the project dependencies.

    ```bash
    python3.8 -m venv .venv
    . .venv/bin/activate
    pip install poetry
    poetry install
    ```

2. Configure the connection parameters for Postgres and Kafka by copying the `configuration.env.example` file while removing the `.example` suffix, and adjusting its contents. The file will also be sourced automatically by the various ways to run Uptimer.

    ```bash
    cp configuration.env.example configuration.env
    ```

   * Adjust the `KAFKA_BOOTSTRAP_SERVER` and `DATABASE_URL` to match your environment
   * Adjust the `KAFKA_SSL_*` variables to match your auth key/cert anc CA certificate
   * Optional: change the `PROBE_*` parameters to change to urls, applied regexes or the interval for the requests

3. Uptimer uses [dbmate](https://github.com/amacneil/dbmate) for database schema migration handling. It can be installed via:

    ```bash
    # On macOS
    brew install dbmate

    # On Linux
    sudo curl -fsSL -o /usr/local/bin/dbmate https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64
    sudo chmod +x /usr/local/bin/dbmate
    ```

4. Apply the database migrations to your Postgres instance

    ```bash
    . configuration.env

    dbmate up
    ```

All steps below assume you have done this initial setup.

## Running the application

### Single Instance

When not specifying a `WRITER_PLUGIN` Uptimer will output all generated events to stdout:

```bash
. .venv/bin/activate
./bin/single_instance.sh
```

### Using Kafka and Postgres

Two terminal windows are required for this, one for the producer instance (i.e. the one trying requests against the URLs) and forwarding events to Kafka, and a consumer instance, consuming the data from Kafka and writing it to Postgres:

```bash
# Instance 1
. .venv/bin/activate
./bin/producer.sh

# Instance 2
. .venv/bin/activate
./bin/consumer.sh
```
