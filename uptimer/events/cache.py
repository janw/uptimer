import json
from os import path

from cachetools import Cache
from structlog import get_logger

from uptimer.events import SCHEMATA_PATH

logger = get_logger()


class SchemaCache(Cache):
    """Load and cache JSON schema files.

    The cache loads a missing JSON schema from a filename and caches it upon successful
    loading. By default the cache also resolves ``$ref`` fields in the schema on-the-fly
    and stores the resolved version of the schema.

    An instantiated SchemaCache object behaves like a dict keyed by the schema's
    filename, and can be queried as such::

        sc = SchemaCache()
        schema = sc['root.json']

        # Access names/URIs of the cached schema files
        sc.keys()

    """

    def __init__(self, resolve_refs=True, maxsize=1024, **kwargs):
        """Instantiates a SchemaCache object.

        By default, all ``$ref`` references in the schemas will be resolved and replaced
        by their schema contents.

        Args:
            resolve_refs (bool): Enables/Disables the inherent resolving of ``$ref``
                in the schemas.

        """
        self.resolve = resolve_refs
        super().__init__(maxsize, **kwargs)

    def __missing__(self, schema_name):
        """Loads JSON schema that is not cached yet."""
        orig_schema_name = schema_name
        logger.debug(f"Loading schema {schema_name} from file", schema_name=schema_name)
        if not path.isfile(schema_name):
            schema_name = path.join(SCHEMATA_PATH, schema_name)
        if not path.isfile(schema_name):
            raise ValueError(f"Cannot resolve schema path for {orig_schema_name}")

        with open(schema_name, "r") as schema_fp:
            data = json.load(schema_fp)

        if self.resolve:
            logger.debug(
                f"Caching resolved representation of {orig_schema_name}",
                schema_name=orig_schema_name,
            )
            resolved_data = self.resolve_refs(data)
            self[orig_schema_name] = resolved_data
            return resolved_data

        logger.debug(f"Caching {orig_schema_name}")
        self[orig_schema_name] = data
        return data

    def resolve_refs(self, data):
        """Resolves all ``$ref`` fields in a given JSON object.

        Nested occurrences of ``$ref`` will also be resolved, and the returned data
        structure is complete without external references.

        Args:
            data (dict or list): Loaded JSON object to be parsed

        Returns:
            dict or list: JSON object with all ``$ref`` occurrences replaced with their
                referenced contents.

        """
        array_iter = []
        if isinstance(data, dict):
            array_iter = data.items()
        elif isinstance(data, list):
            array_iter = enumerate(data)

        for key, value in array_iter:
            if key == "$ref":
                logger.debug(f"Resolving $ref {value}", reference=value)
                return self[value]
            else:
                data[key] = self.resolve_refs(value)

        return data


schema_cache = SchemaCache()
