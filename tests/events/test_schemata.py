import json
from os import path

import jsonschema

VALIDATION_SCHEMA = "draft-07_hyper-schema.json"
HERE = path.dirname(path.realpath(__file__))

with open(path.join(HERE, "schemata", VALIDATION_SCHEMA), "r") as schema_fp:
    validation_schema_spec = json.load(schema_fp)


def test_schema_validity(jsonschemafile):
    with open(jsonschemafile, "r") as schema_fp:
        instance = json.load(schema_fp)

    jsonschema.validate(
        instance,
        schema=validation_schema_spec,
        format_checker=jsonschema.FormatChecker(),
    )
