# Uptimer 📈

**Uptimer is a plugin-based prober to determine website uptime.**

Uptimer is designed to be modular and extensible, and –by using reader/probe plugins– not only allows for HTTP(S) probing of websites but potentially more low-level protocols (such as TCP, ICMP/ping) and other application layer protocols. The forwarding and processing data is extensible as well, so it is possible to run Uptimer as a single instance that stores results in a database directly, or have an arbitrary number of probe instances that produce results into a Kafka queue, which in turn is being consumed by only a few instances that persist the results into the database.

The heart and core of Uptimer is an equally modular event paradigm that is used to ensure plugin compatibility and validity of data passed between plugins. Should a future to-be-probed protocol require additional properties to be produced, those can be defined in a new event type without the necessity of adapting other reader/writer plugins. Events based on and validated via [JSON Schema](https://json-schema.org/).
