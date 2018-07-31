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
import warnings
from urllib3.exceptions import InsecureRequestWarning

import requests
import requests_ntlm
import zeep
import zeep.cache

from . import config  # noqa
from . import exceptions
from ._metadata import __version__, __version_info__  # noqa
from .constants import (
    DEFAULT_WSDL_CACHE_EXPIRATION,
    CODEUNIT,
    PAGE,
    ReadMultiple,
    CreateMultiple,
)
from .plugins import RemoveNamespacePlugin  # noqa
from .utils import to_builtins

logger = logging.getLogger('nav')


class NAV:

    def __init__(
        self,
        base_url: 'The base URL for the NAV web service.',
        username: 'Username (usually includes AD domain)',
        password: 'Password',
        cache_expiration: 'How long WSDL files are cached in memory. Set to something Falsy like False/0/None to disable this functionality.' = DEFAULT_WSDL_CACHE_EXPIRATION,
        verify_certificate=True,
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.cache_expiration = cache_expiration
        self.verify_certificate = verify_certificate
        self._service_cache = {}

        # Ignore warning in case we've actively disabled
        # certificate verification.
        if self.verify_certificate is False:
            warnings.simplefilter('ignore', InsecureRequestWarning)

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

    def _run_capture_500(self, fun, *args, **kw):
        try:
            return fun(*args, **kw)
        except requests.exceptions.HTTPError as exc:
            raise exceptions.NAVHTTPError(
                *exc.args, request=exc.request, response=exc.response,
            )

    @staticmethod
    def validate_service_type(s):
        allowed_values = (CODEUNIT, PAGE)
        if s not in allowed_values:
            raise exceptions.InvalidServiceType(
                '`{}` is not a valid service type, must be one of {}'
                .format(s, allowed_values)
            )

    @staticmethod
    def validate_supported_page_function(s):
        allowed_values = (ReadMultiple, CreateMultiple)
        if s not in allowed_values:
            raise exceptions.UnsupportedPageFunction(
                '`{}` is not a supported service function, must be one of {}'
                .format(s, allowed_values)
            )

    def _make_client(self, endpoint_type, service_name, **client_kwargs):
        self.validate_service_type(endpoint_type)
        url = self._make_endpoint_url(endpoint_type, service_name)
        if self.cache_expiration:
            cache = zeep.cache.InMemoryCache(timeout=self.cache_expiration)
        else:
            cache = None

        session = requests.Session()
        session.verify = self.verify_certificate
        session.auth = requests_ntlm.HttpNtlmAuth(self.username, self.password)
        transport = zeep.transports.Transport(session=session, cache=cache)

        if 'settings' not in client_kwargs:
            client_kwargs['settings'] = zeep.Settings(strict=False)

        return self._run_capture_500(
            zeep.Client,
            url,
            transport=transport,
            **client_kwargs
        )

    def make_service(
        self,
        endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
        service_name: 'Name of the page/codeunit',
        **client_kwargs: 'Additional kwargs to pass to zeep.Client'
    ):
        """Create a WSDL service instance"""
        binding = self._make_binding(endpoint_type, service_name)
        service_cache_key = (binding, str(client_kwargs))

        if service_cache_key in self._service_cache:
            srvc = self._service_cache[service_cache_key]
        else:
            client = self._make_client(
                endpoint_type,
                service_name,
                **client_kwargs
            )
            srvc = client.create_service(binding, client.wsdl.location)
            self._service_cache[service_cache_key] = srvc
        return srvc

    def meta(
        self,
        endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
        service_name: 'Name of the page/codeunit',
    ):
        """Get the definition of Codeunit or a Page"""
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
        srvc = self.make_service(
            endpoint_type=CODEUNIT,
            service_name=service_name,
        )
        func = getattr(srvc, function)
        data = func(**func_args)

        return to_builtins(data, default=[])

    def page(
        self,
        service_name: 'The name of the WS page',
        function: 'The function to use. Currently supported functions are ReadMultiple and CreateMultiple.',
        num_results: 'Maximum amount of results to return for ReadMultiple. Defaults to no limit.' = 0,
        filters: 'Apply filters to a ReadMultiple result' = None,
        entries: 'Entries to pass to CreateMultiple' = None,
        additional_data: 'Any additional data to pass along to the WS call.' = None,
    ):
        """Get a Page's results or create entries"""
        self.validate_supported_page_function(function)

        srvc = self.make_service(
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

        call_kw = dict(additional_data or {})

        if function == ReadMultiple:
            data = srvc.ReadMultiple(
                filter=self._make_page_filters(filters),
                setSize=num_results,
                **call_kw,
            )
        elif function == CreateMultiple:
            if not entries:
                raise ValueError(
                    "Can't run Page CreateMultiple without passing in "
                    "any `entries`"
                )
            call_kw.update({
                '{}_List'.format(service_name): [
                    {service_name: [entry for entry in entries]}
                ],
            })
            data = srvc.CreateMultiple(**call_kw)
        else:
            raise NotImplementedError

        return to_builtins(data, default=[])

    def read_multiple(
        self,
        service_name: 'The name of the WS page',
        num_results: 'Maximum amount of results to return. Defaults to no limit.' = 0,
        filters: 'Apply filters to the query' = None,
        additional_data: 'Any additional data to pass along to the WS call.' = None,
    ):
        return self.page(
            service_name=service_name,
            function=ReadMultiple,
            num_results=num_results,
            filters=filters,
            additional_data=additional_data,
        )

    def create_multiple(
        self,
        service_name: 'The name of the WS page',
        entries: 'Entries to pass to CreateMultiple' = None,
        additional_data: 'Any additional data to pass along to the WS call.' = None,
    ):
        return self.page(
            service_name=service_name,
            function=CreateMultiple,
            entries=entries,
            additional_data=additional_data,
        )


def _nav_factory(
    base_url,
    username,
    password,
    cache_expiration,
    verify_certificate=True,
):
    return NAV(
        base_url=base_url,
        username=username,
        password=password,
        cache_expiration=cache_expiration,
        verify_certificate=verify_certificate,
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
        verify_certificate=kw.pop('verify_certificate', True),
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
        verify_certificate=kw.pop('verify_certificate', True),
    ).make_service(*args, **kw)


def page(base_url, username, password, *args, **kw):
    return _nav_factory(
        base_url,
        username,
        password,
        cache_expiration=kw.pop(
            'cache_expiration',
            DEFAULT_WSDL_CACHE_EXPIRATION,
        ),
        verify_certificate=kw.pop('verify_certificate', True),
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
        verify_certificate=kw.pop('verify_certificate', True),
    ).codeunit(*args, **kw)
