import requests
from lxml import etree


class InvalidServiceType(Exception):
    """Raised when an invalid service type is encountered

    I.e. not one of Page, Codeunit
    """


class UnsupportedPageFunction(Exception):
    """Raised when an invalid service function is encountered

    I.e. not one of ReadMultiple, CreateMultiple
    """


class NAVHTTPError(requests.exceptions.HTTPError):
    """Displays the error details that NAV returns"""

    def __str__(self):
        try:
            return ' - '.join(
                filter(
                    None,
                    (
                        e.text for e
                        in etree.fromstring(self.response.text).iter()
                        if e.tag in ('faultcode', 'faultstring', 'detail')
                    )
                )
            )
        except BaseException:
            return self.response.text
