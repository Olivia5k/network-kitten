import jsonschema


CORE_SCHEMA = {
    'type': 'object',
    'properties': {
        'paradigm': {
            'type': 'string',
        },
        'method': {
            'type': 'string',
        },
        'address': {
            'type': 'string',
        },
    },
    'additionalProperties': False,
}

VALIDATORS = {
    'core': CORE_SCHEMA
}


def validate(request, schema_name):
    jsonschema.validate(request, VALIDATORS[schema_name])
