from functools import lru_cache

from kafka import KafkaProducer
from structlog import get_logger

from uptimer.events import Event, serializer
from uptimer.plugins.writers import WriterPlugin

logger = get_logger()


@lru_cache(maxsize=1)
def get_producer(
    *,
    bootstrap_server,
    security_protocol,
    ssl_cafile,
    ssl_keyfile,
    ssl_certfile,
    ssl_check_hostname,
):
    logger.info("Connecting to Kafka as Producer")
    return KafkaProducer(
        bootstrap_servers=bootstrap_server,
        value_serializer=serializer.dumps,
        security_protocol=security_protocol,
        ssl_cafile=ssl_cafile,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        ssl_check_hostname=ssl_check_hostname,
    )


def send_error_callback(excp):
    logger.exception(
        "Sending message to topic failed", exc_info=excp, error=type(excp).__name__
    )


class Plugin(WriterPlugin):
    plugin_type = "kafka topic writer"
    event_type = Event
    required_settings = (
        "kafka_bootstrap_server",
        "kafka_writer_topic",
        "kafka_ssl_cafile",
        "kafka_ssl_keyfile",
        "kafka_ssl_certfile",
    )
    optional_settings = (
        "kafka_security_protocol",  # Defaults to `"SSL"` in settings.toml
        "kafka_ssl_check_hostname",  # Defaults to `True` in settings.toml
    )

    _type_unset = "__event_type_unset__"

    def write(self, payload):
        producer = get_producer(
            bootstrap_server=self.settings.kafka_bootstrap_server,
            security_protocol=self.settings.kafka_security_protocol,
            ssl_cafile=self.settings.kafka_ssl_cafile,
            ssl_keyfile=self.settings.kafka_ssl_keyfile,
            ssl_certfile=self.settings.kafka_ssl_certfile,
            ssl_check_hostname=self.settings.kafka_ssl_check_hostname,
        )
        count = 0
        event_type = self._type_unset

        for event in payload:
            if event_type is self._type_unset:
                event_type = event.__class__.__name__
            producer.send(
                self.settings.kafka_writer_topic,
                self.validate_event_type(event, strict=False),
            ).add_errback(send_error_callback)
            count += 1

        log_data = dict(
            event_count=count,
            event_type=event_type,
            to="kafka",
            topic=self.settings.kafka_writer_topic,
        )

        if count == 0:
            self.logger.info(
                f"No events to post to {self.settings.kafka_writer_topic}.", **log_data
            )
        else:
            self.logger.info(
                f"Posted {count} events to {self.settings.kafka_writer_topic}.",
                **log_data,
            )
            producer.flush()
