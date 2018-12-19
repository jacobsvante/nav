import zeep.helpers

from . import constants

UNSET = object()


def convert_string_filter_values(filters):
    """Convert string type filter values to their XML equivalent
    Mostly useful for parsing CLI input data.
    """
    return {
        field: constants.STRING_VALUE_TO_PYTHON_TYPE_MAPPING.get(
            criteria,
            criteria
        )
        for field, criteria in filters.items()
    }


def to_builtins(data, default=UNSET, target_cls=dict):
    """
    Turn zeep XML object into python built-in data structures

    Args:
        default (Any):
            A default to return when serialized object is None.
        target_cls (Type[dict]):
            Which type of dictionary type will be used for objects.
            As this project's minimum Python version officially supported is
            3.6 we can rely on the native sorted order of the standard `dict`
            class as a default.
    """
    d = zeep.helpers.serialize_object(data)
    if d is None and default is not UNSET:
        return default
    return zeep.helpers.serialize_object(d, target_cls=target_cls)
