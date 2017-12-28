import pkg_resources

__version__ = pkg_resources.require('nav')[0].version
__version_info__ = tuple(int(p) for p in __version__.split('.'))
