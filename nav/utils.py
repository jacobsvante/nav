import collections

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
