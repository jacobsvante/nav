"""
Simple wrapper that adds some extra encoding capabilities needed for
this project.
"""
import collections
import datetime
import decimal
from json import JSONDecodeError  # noqa
import json as json_impl


class JsonExtendedEncoder(json_impl.JSONEncoder):
    """
    Needed for the json module to understand what to do with the types we
    use in this project.
    """
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(
            obj,
            (
                datetime.time,
                datetime.date,
                datetime.datetime,
            ),
        ):
            return str(obj)

        # Handle case where zeep returns the undocumented _raw_elements key
        # which is of type `collections.deque`. As the name suggestions this
        # object contains raw elements, which json will be unable to process,
        # therefore we return None.
        elif isinstance(obj, collections.deque):
            return None
        return super().default(obj)


def dump(*args, **kw):
    if 'cls' not in kw:
        kw['cls'] = JsonExtendedEncoder
    return json_impl.dump(*args, **kw)


def dumps(*args, **kw):
    if 'cls' not in kw:
        kw['cls'] = JsonExtendedEncoder
    return json_impl.dumps(*args, **kw)


load = json_impl.load
loads = json_impl.loads
