from os import path

from uptimer.events import Event

HERE = path.dirname(path.realpath(__file__))

TYPECASTING_SCHEMA = path.join(HERE, "schemata", "test-typecasting.json")
DOUBLY_NESTED_SCHEMA = path.join(HERE, "schemata", "test-double-nested.json")
SIMPLE_SCHEMA = path.join(HERE, "schemata", "test-simple-event.json")


class TypecastingEvent(Event):
    schema = TYPECASTING_SCHEMA
    table = "dummy_table"


class DoublyNestedEvent(Event):
    schema = DOUBLY_NESTED_SCHEMA
    table = "dummy_table"


class SimpleEvent(Event):
    schema = SIMPLE_SCHEMA
    table = "dummy_table"
