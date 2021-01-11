from abc import ABCMeta
from uuid import UUID

import jsonschema
from dateutil.parser import parse as dateparse

from uptimer.events import SCHEMATA_PATH
from uptimer.events.cache import schema_cache
from uptimer.helpers import to_bool, to_none


class EventDefinitionError(ValueError):
    pass


class EventMeta(ABCMeta, metaclass=ABCMeta):
    schema_path: str = f"file:///{SCHEMATA_PATH}"
    """Base-URL at which the schema resolver will look up schema references."""

    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        schema = attrs.pop("schema", None)

        # `table` can be a valid None, so use False as placeholder of missing property
        table = attrs.pop("table", False)

        if not schema:
            raise EventDefinitionError(f"Class {name} did not declare a JSON schema.")
        if table is False:
            raise EventDefinitionError(
                f"Class {name} did not declare a database table mapping."
            )

        # Now resolve and parse the JSON schema for additional properties; generating
        # useful representations, the proper schema resolver for validation, etc.
        # Inserting them in the `attrs` dictionary will cause them to become regular
        # class variables, available in every instantiated class object.
        schema_spec = schema_cache[schema]
        if schema_spec["title"] != name:
            raise EventDefinitionError(
                f"Name of class {name} must be equal to "
                f"JSON schema title '{schema_spec['title']}'"
            )

        properties_dict = cls._collect_properties(schema_spec)
        properties = list(properties_dict.keys())
        property_cast_mapping = {
            prop: cls.property_to_python(spec) for prop, spec in properties_dict.items()
        }
        resolver = jsonschema.RefResolver(cls.schema_path, schema_spec)
        attrs.update(
            dict(
                schema=schema,
                table=table,
                schema_spec=schema_spec,
                properties_dict=properties_dict,
                properties=properties,
                property_cast_mapping=property_cast_mapping,
                _resolver=resolver,
            )
        )
        return super_new(cls, name, bases, attrs, **kwargs)

    @staticmethod
    def _collect_properties(schema):
        """Collects a list of all (including nested and conditional) properties."""
        props = dict()
        array_iter = []
        if isinstance(schema, list):
            array_iter = enumerate(schema)
        elif isinstance(schema, dict):
            array_iter = schema.items()

        for key, value in array_iter:
            if key == "properties":
                props.update(value)
            elif key == "required":
                continue
            else:
                props.update(EventMeta._collect_properties(value))

        return props

    @staticmethod
    def property_to_python(property_spec):
        """
        Returns a list of appropriate python-native datatypes for a schema property.

        Based on the event class'es schema, a list of callables is returned that a
        value might be tried against. The list is ordered from most to least strict
        as to prevent falsely casting values as a less strict type.

        Possible types taken from JSON schema validation specification
        http://json-schema.org/latest/json-schema-validation.html#rfc.section.6.1.1
        """

        propformat = property_spec.get("format")
        if propformat == "date-time":
            return [dateparse]
        if propformat == "uuid":
            return [UUID]

        proptypes = property_spec.get("type")
        if not proptypes:
            return []
        if not isinstance(proptypes, list):
            proptypes = [proptypes]

        callables = []
        if "null" in proptypes:
            callables.append(to_none)
        if "boolean" in proptypes:
            callables.append(to_bool)
        if "integer" in proptypes:
            callables.append(int)
        if "number" in proptypes:
            callables.append(float)
        return callables
