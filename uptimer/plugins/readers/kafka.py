from functools import lru_cache

from kafka import KafkaConsumer
from structlog import get_logger

from uptimer import events
from uptimer.events import serializer
from uptimer.plugins.readers import ReaderPlugin

logger = get_logger()


@lru_cache(maxsize=1)
def get_consumer(
    *,
    topic,
    group_id,
    bootstrap_server,
    security_protocol,
    ssl_cafile,
    ssl_keyfile,
    ssl_certfile,
    ssl_check_hostname,
):
    logger.info("Connecting to Kafka as Consumer", topic=topic, group_id=group_id)
    consumer = KafkaConsumer(
        value_deserializer=serializer.loads,
        bootstrap_servers=bootstrap_server,
        group_id=group_id,
        security_protocol=security_protocol,
        ssl_cafile=ssl_cafile,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        ssl_check_hostname=ssl_check_hostname,
    )

    consumer.subscribe([topic])
    return consumer


class Plugin(ReaderPlugin):
    plugin_type = "kafka topic reader"
    event_type = events.stubs.Event
    required_settings = (
        "kafka_bootstrap_server",
        "kafka_reader_topic",
        "kafka_ssl_cafile",
        "kafka_ssl_certfile",
        "kafka_ssl_keyfile",
    )
    optional_settings = (
        "kafka_security_protocol",  # Defaults to `"SSL"` in settings.toml
        "kafka_ssl_check_hostname",  # Defaults to `True` in settings.toml
        "kafka_group_id",
    )

    def read(self):
        consumer = get_consumer(
            topic=self.settings.kafka_reader_topic,
            group_id=self.settings.kafka_group_id,
            bootstrap_server=self.settings.kafka_bootstrap_server,
            security_protocol=self.settings.kafka_security_protocol,
            ssl_cafile=self.settings.kafka_ssl_cafile,
            ssl_certfile=self.settings.kafka_ssl_certfile,
            ssl_keyfile=self.settings.kafka_ssl_keyfile,
            ssl_check_hostname=self.settings.kafka_ssl_check_hostname,
        )
        for data in consumer:
            yield data.value
