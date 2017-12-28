import configparser
import os
import os.path as op

from . import constants

PATH = os.environ.get('NAV_CONFIG', '~/.config/nav.ini')

_config_path = op.expanduser(PATH)
_config = configparser.ConfigParser()

if op.isfile(_config_path):
    _config.read(_config_path)


class ConfigKeyMissing(KeyError):
    """A config key is missing, and no fallback was provided."""


def get(section, key, fallback=constants.NotSet, fallback_required=True):
    try:
        return _config[section][key]
    except KeyError:
        if fallback is constants.NotSet and fallback_required:
            raise ConfigKeyMissing(
                '`{}` missing, and no fallback provided.'.format(key)
            )
        else:
            return fallback
