import re
import copy
import pprint

import jsonschema

from jsonschema.exceptions import ValidationError


class Validator(object):
    core_schema = {
        'type': 'object',
        'properties': {
            'paradigm': {
                'type': 'string',
            },
            'method': {
                'type': 'string',
            },
        },
        'additionalProperties': False,
    }

    def request(self, *args):
        self.validate('request', *args)

    def response(self, *args):
        self.validate('response', *args)

    def validate(self, kind, request, paradigms):
        paradigm_name, method_key = self.get_method(request)

        paradigm = paradigms.get(paradigm_name)

        if paradigm is None:
            raise ValidationError(
                "Paradigm '{0}' not known. Choices are: {1}".format(
                    paradigm_name,
                    self._csl(paradigms)
                )
            )

        validator = paradigm.validator
        method_name = '{0}_{1}'.format(method_key, kind)
        method = getattr(validator, method_name, None)

        if method is None:
            raise ValidationError(
                "Method '{0}()' not found in '{1}'. Choices are: {2}".format(
                    method_name,
                    paradigm_name,
                    self._csl(validator.get_known_methods())
                )
            )

        # Since we are going to modify the schema, we need to make a deep copy
        # of it so that future requests are not contaminated by what we do now.
        # TODO: Split into function and add deeper tests.
        schema = copy.deepcopy(self.core_schema)
        schema['properties'].update(method())

        jsonschema.validate(request, schema)

    def get_method(self, data):
        # TODO: Make this method actually return the method, with the
        # validation from the above.
        error = None

        if 'paradigm' not in data:
            error = 'paradigm'
        elif 'method' not in data:
            error = 'method'

        if error:
            msg = ''''{0}' field missing in:\n{1}'''
            raise ValidationError(msg.format(error, pprint.pformat(data)))

        return data['paradigm'], data['method']

    def get_known_methods(self):
        """
        Get known validation methods by finding all methods ending in _request
        or _response.

        """

        ret = []
        for key in dir(self):
            item = getattr(self, key)
            if re.search(r'_(request|response)$', key) and callable(item):
                ret.append(key)
        return ret

    def _csl(self, iterable):
        """
        Make a list quoted and comma separated

        """

        return ", ".join("'{0}'".format(x) for x in iterable)
