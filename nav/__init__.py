"""Conveniently make requests to Microsoft Dynamics NAV Web Services

Tested with Dynamics NAV 2009 R2. A lot of assumptions have been made while
making this project, so it cannot be guaranteed that it will work for everyone.

# Endpoint URL format is::

    http://<Server>:<WebServicePort>/<ServerInstance>/WS/<CompanyName>/<EndpointType>/<EndpointName>

More info here::

    https://msdn.microsoft.com/en-us/library/dd355398.aspx
"""
import collections
import logging

import requests
import requests_ntlm
import zeep
import zeep.cache

from . import config  # noqa
from ._metadata import __version__, __version_info__  # noqa
from .constants import (
    DEFAULT_WSDL_CACHE_EXPIRATION,
    CODEUNIT,
    PAGE,
    ReadMultiple,
    CreateMultiple,
)

logger = logging.getLogger('nav')


class NAV:

    def __init__(
        self,
        base_url: 'The base URL for the NAV web service.',
        username: 'Username (usually includes AD domain)',
        password: 'Password',
        cache_expiration: 'How long WSDL files are cached in memory. Set to something Falsy like False/0/None to disable this functionality.' = DEFAULT_WSDL_CACHE_EXPIRATION,
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.cache_expiration = cache_expiration
        self._service_cache = {}

    @staticmethod
    def _zeep_object_to_builtin_types(data, default=False):
        d = zeep.helpers.serialize_object(data)
        if d is None and default is not False:
            return default
        return d

    @staticmethod
    def _make_page_filters(filters):
        return [
            collections.OrderedDict([
                ('Field', field),
                ('Criteria', criteria),
            ])
            for field, criteria in filters.items()
        ]

    def _make_endpoint_url(self, *args):
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        return '/'.join([self.base_url, *args])

    @staticmethod
    def _make_binding(endpoint_type, service_name):
        if endpoint_type == PAGE:
            urlpath_service_name = service_name.lower()
        else:
            urlpath_service_name = service_name
        return '{{urn:microsoft-dynamics-schemas/{0}/{1}}}{2}_Binding'.format(
            endpoint_type.lower(),
            urlpath_service_name,
            service_name,
        )

    def _make_client(self, endpoint_type, service_name):
        url = self._make_endpoint_url(endpoint_type, service_name)
        if self.cache_expiration:
            cache = zeep.cache.InMemoryCache(timeout=self.cache_expiration)
        else:
            cache = None

        session = requests.Session()
        session.auth = requests_ntlm.HttpNtlmAuth(self.username, self.password)
        transport = zeep.transports.Transport(session=session, cache=cache)
        return zeep.Client(url, transport=transport, strict=False)

    def _make_service(
        self,
        endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
        service_name: 'Name of the page/codeunit',
    ):
        """Initiate a WSDL service"""
        assert endpoint_type in (CODEUNIT, PAGE)
        binding = self._make_binding(endpoint_type, service_name)
        if binding in self._service_cache:
            srvc = self._service_cache[binding]
        else:
            client = self._make_client(endpoint_type, service_name)
            srvc = client.create_service(binding, client.wsdl.location)
            self._service_cache[binding] = srvc
        return srvc

    def meta(
        self,
        endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
        service_name: 'Name of the page/codeunit',
    ):
        """Get the definition of Codeunit or a Page"""
        assert endpoint_type in (CODEUNIT, PAGE)
        client = self._make_client(
            endpoint_type,
            service_name,
        )
        return client.wsdl._get_xml_document(client.wsdl.location)

    def codeunit(
        self,
        service_name: 'The name of the code unit to use',
        function: 'Name of the code unit function to run',
        func_args: 'Add these kw args to the codeunit function call' = None,
    ):
        """Get a Codeunit's results"""
        srvc = self._make_service(
            endpoint_type=CODEUNIT,
            service_name=service_name,
        )
        func = getattr(srvc, function)
        data = func(**func_args)

        return self._zeep_object_to_builtin_types(data, default=[])

    def page(
        self,
        service_name: 'The name of the WS page',
        function: 'The function to use. Currently supported functions are ReadMultiple and CreateMultiple.',
        num_results: 'Maximum amount of results to return for ReadMultiple. Defaults to no limit.' = 0,
        filters: 'Apply filters to a ReadMultiple result' = None,
        entries: 'Entries to pass to CreateMultiple' = None,
        additional_data: 'Any additional data to pass along with the entries when using CreateMultiple.' = None,
    ):
        """Get a Page's results or create entries"""
        srvc = self._make_service(
            endpoint_type=PAGE,
            service_name=service_name,
        )

        if not filters:
            # NOTE: Workaround because the definition files for NAV 2009 R2 pages
            # requires the filter element to be defined (minOccurs=1), causing
            # zeep to raise a ValidationError exception. However, manually doing
            # an HTTP request to the web service, without passing in a filter
            # works. Perhaps create a ticket regarding a feature to temporarily
            # disable validation of min/maxOccurs.
            filters = {zeep.helpers.Nil(): zeep.helpers.Nil()}

        if function == ReadMultiple:
            data = srvc.ReadMultiple(
                filter=self._make_page_filters(filters),
                setSize=num_results,
            )
        elif function == CreateMultiple:
            if not entries:
                raise ValueError(
                    "Can't run Page CreateMultiple without passing in "
                    "any `entries`"
                )
            kw = dict(additional_data or {})
            kw.update({
                '{}_List'.format(service_name): [
                    {service_name: entry} for entry in entries
                ],
            })
            data = srvc.CreateMultiple(**kw)
        else:
            raise NotImplementedError

        return self._zeep_object_to_builtin_types(data, default=[])

    def read_multiple(
        self,
        service_name: 'The name of the WS page',
        num_results: 'Maximum amount of results to return. Defaults to no limit.' = 0,
        filters: 'Apply filters to the query' = None,
    ):
        return self.page(
            service_name=service_name,
            function=ReadMultiple,
            num_results=num_results,
            filters=filters,
        )

    def create_multiple(
        self,
        service_name: 'The name of the WS page',
        entries: 'Entries to pass to CreateMultiple' = None,
        additional_data: 'Any additional data to pass along with the entries when using CreateMultiple.' = None,
    ):
        return self.page(
            service_name=service_name,
            function=CreateMultiple,
            entries=entries,
            additional_data=additional_data,
        )


def _nav_factory(base_url, username, password, cache_expiration):
    return NAV(
        base_url=base_url,
        username=username,
        password=password,
        cache_expiration=cache_expiration,
    )


def meta(base_url, username, password, *args, **kw):
    return _nav_factory(
        base_url,
        username,
        password,
        cache_expiration=kw.pop(
            'cache_expiration',
            DEFAULT_WSDL_CACHE_EXPIRATION,
        ),
    ).meta(*args, **kw)


def service(base_url, username, password, *args, **kw):
    return _nav_factory(
        base_url,
        username,
        password,
        cache_expiration=kw.pop(
            'cache_expiration',
            DEFAULT_WSDL_CACHE_EXPIRATION,
        ),
    )._make_service(*args, **kw)


def page(base_url, username, password, *args, **kw):
    return _nav_factory(
        base_url,
        username,
        password,
        cache_expiration=kw.pop(
            'cache_expiration',
            DEFAULT_WSDL_CACHE_EXPIRATION,
        ),
    ).page(*args, **kw)


def codeunit(base_url, username, password, *args, **kw):
    return _nav_factory(
        base_url,
        username,
        password,
        cache_expiration=kw.pop(
            'cache_expiration',
            DEFAULT_WSDL_CACHE_EXPIRATION,
        ),
    ).codeunit(*args, **kw)
