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

## Initial Setup

1. After checkout create a **Python 3.8** virtual environment and install the project dependencies.

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

### Adjusting the Configuration

to run an instance with your own configuration parameters, you can do so by passing them to the application through environment variables. The main parameters of the HTTP prober are

* `PROBE_URLS`: a single URL string, or a list (TOML or YAML formatted!) of urls to probe
* `PROBE_REGEXES`: a single regex string, or a list (TOML or YAML formatted!) of regexes to check the URLs against. If only the list has a length of 1, it is used for all URLs. Otherwise the length has to match the length of `PROBE_URLS` (one regex per URL with same order)
* `PROBE_INTERVAL`: an integer setting the pause between running all probes once

By default Uptimer will use the HTTP prober and output all events to stdout, i.e. the `READER_PLUGIN` is set to `readers.prober.http`, and the `WRITER_PLUGIN` to `writers.stdout`. Thus a minimal config looks like this:

```bash
. .venv/bin/activate
. configuration.env

PROBE_URLS='https://status.aiven.io' python -m uptimer

# Or include a regex and multiple URLs:
PROBE_URLS='["https://status.aiven.io", "https://www.githubstatus.com"]' \
PROBE_REGEXES='All Systems Operational' \
    python -m uptimer
```

To instead forward the events to Kafka, you can simply change the `WRITER_PLUGIN`:

```bash
. .venv/bin/activate
. configuration.env

WRITER_PLUGIN=writers.kafka \
PROBE_URLS='["https://status.aiven.io", "https://www.githubstatus.com"]' \
PROBE_REGEXES='All Systems Operational' \
    python -m uptimer
```

It's also possible to write the events to the database directly:

```bash
. .venv/bin/activate
. configuration.env

WRITER_PLUGIN=writers.postgres \
PROBE_URLS='["https://status.aiven.io", "https://www.githubstatus.com"]' \
PROBE_REGEXES='All Systems Operational' \
    python -m uptimer
```

## Development Tools

### Running the tests

```bash
. .venv/bin/activate
pytest
```

Tests also run in [this GitHub Actions workflow](https://github.com/janw/uptimer/actions?query=workflow%3ATests) on every push, and pull request

### Auto-formatting, code style and linting

Uptimer's uses the [pre-commit framework](https://pre-commit.com/) to enforce consistency in code-formatting, and to avoid increased complexity and common mistakes and code smells. It is installed together with the dev-dependencies during the initial setup above. Its configuration can be found in [.pre-commit-config.yaml](.pre-commit-config.yaml) and contains instructions to enforce the following:

* auto-formatting using [Black, the uncompromising Python code formatter](https://black.readthedocs.io).
* import sorting using [isort](https://pycqa.github.io/isort/)
* static typing using [mypy](http://www.mypy-lang.org/)
* linting using [Flake8](https://flake8.pycqa.org) to ensure a consistent code-style, including the [bugbear plugin](https://github.com/PyCQA/flake8-bugbear)
* a check to avoid using the print() built-in (most often should be replaced by a logger)
* checks preventing `eval` and blanket `# NOQA` pragmas
* checks preventing trailing whitespace, ensuring a single newline at the end of a file
* a check to ensure validity of YAML files

Run the checks in a one-off on all files:

```bash
. .venv/bin/activate

pre-commit run --all-files
```

Or automatically on `git commit` when installed as a pre-commit hook:

```bash
. .venv/bin/activate

pre-commit install
```

The pre-commit config is used in [this GitHub Actions workflow](https://github.com/janw/uptimer/actions?query=workflow%3ALinters) on every pull request and pushes to the master branch.

### Commit style

Uptimer follows the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) specification of formatting commit messages which helps auto-generating the [Changelog](CHANGELOG.md) in this [GitHub Actions workflow](https://github.com/janw/uptimer/actions?query=workflow%3A%22Bump+version%22) (must be triggered manually). The tool used here is [Commitizen](https://commitizen-tools.github.io/commitizen/).

The commit style is checked in [this GitHub Actions workflow](https://github.com/janw/uptimer/actions?query=workflow%3ALinters) on every pull request and pushes to the master branch.

## Containerized usage

If you're so inclined Uptimer can be run in a containerized setting as well, and includes an example docker-compose stack  Again assuming the initial setup has been done, the docker-compose stack can be brought up:

```bash
. configuration.env

docker-compose up --build
```

## Installing via Pip

Since Uptimer uses the PEP517-compatible dependency/project manager Poetry, it is easy to install Uptimer via pip directly, too.

```bash
    python3.8 -m venv uptimer_venv
    . uptimer_venv/bin/activate
    pip install -U git+git://github.com/janw/uptimer.git#egg=uptimer

    uptimer
```

## Potential Future Improvements

* Add (Web-)UI to actually display the collected data
* Make use of relational database schema, linking hosts with probe events
* Improve robustness of settings parsing, specifically for the lists of PROBE_URLS, PROBE_REGEXES
* Add more meaningful tests, specifically to validate specific plugin's communication with outside service
* Add more type annotations beyond type inference and the current state annotations
