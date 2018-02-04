import collections

import zeep.helpers

from . import constants


def convert_string_filter_values(filters):
    """Convert string type filter values to their XML equivalent
    Mostly useful for parsing CLI input data.
    """
    return collections.OrderedDict(
        (
            field,
            constants.STRING_VALUE_TO_PYTHON_TYPE_MAPPING.get(
                criteria,
                criteria
            )
        )
        for field, criteria in filters.items()
    )


def to_builtins(data, default=False):
    """Turn zeep XML data into python built-in data structures"""
    d = zeep.helpers.serialize_object(data)
    if d is None and default is not False:
        return default
    return d
