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

from . import config  # noqa
from . import constants
from ._metadata import __version__, __version_info__  # noqa

logger = logging.getLogger('nav')


def _make_page_filters(filters):
    return [
        collections.OrderedDict([
            ('Field', field),
            ('Criteria', criteria),
        ])
        for field, criteria in filters.items()
    ]


def make_endpoint_url(base_url, *args):
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return '/'.join([base_url, *args])


def make_binding(endpoint_type, service_name):
    if endpoint_type == constants.PAGE:
        urlpath_service_name = service_name.lower()
    else:
        urlpath_service_name = service_name
    return '{{urn:microsoft-dynamics-schemas/{0}/{1}}}{2}_Binding'.format(
        endpoint_type.lower(),
        urlpath_service_name,
        service_name,
    )


def make_client(endpoint_url, username, password):
    session = requests.Session()
    session.auth = requests_ntlm.HttpNtlmAuth(username, password)
    transport = zeep.transports.Transport(session=session)
    return zeep.Client(endpoint_url, transport=transport, strict=False)


def make_service(client, endpoint_url, binding):
    return client.create_service(binding, endpoint_url)


def service(
    base_url: 'The base URL for the endpoint.',
    endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
    name: 'Name of the page/codeunit',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
):
    """Initiate a WSDL service"""
    assert endpoint_type in (constants.CODEUNIT, constants.PAGE)
    endpoint_url = make_endpoint_url(base_url, endpoint_type, name)
    binding = make_binding(endpoint_type, name)
    client = make_client(endpoint_url, username, password)
    return make_service(client, endpoint_url, binding)


def meta(
    base_url: 'The base URL for the endpoint.',
    endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
    name: 'Name of the page/codeunit',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
):
    """Get the definition of Codeunit or a Page"""
    assert endpoint_type in (constants.CODEUNIT, constants.PAGE)
    endpoint_url = make_endpoint_url(base_url, endpoint_type, name)
    client = make_client(endpoint_url, username, password)
    return client.wsdl._get_xml_document(client.wsdl.location)


def codeunit(
    base_url: 'The base URL for the endpoint.',
    name: 'The name of the code unit to use',
    function: 'Name of the code unit function to run',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
    filters: 'Apply filters to the page search' = None,
):
    """Get a Codeunit's results"""
    srvc = service(
        base_url=base_url,
        endpoint_type=constants.CODEUNIT,
        name=name,
        username=username,
        password=password,
    )
    func = getattr(srvc, function)
    data = func(**filters)

    return zeep.helpers.serialize_object(data) or []


def page(
    base_url: 'The base URL for the endpoint.',
    name: 'The name of the WS page',
    function: 'The function to use. Currently supported functions are ReadMultiple and CreateMultiple.',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
    num_results: 'Maximum amount of results to return for ReadMultiple. Defaults to no limit.' = 0,
    filters: 'Apply filters to a ReadMultiple result' = None,
    entries: 'Entries to pass to CreateMultiple' = None,
    additional_data: 'Any additional data to pass along with the entries when using CreateMultiple.' = None,
):
    """Get a Page's results or create entries"""
    srvc = service(
        base_url=base_url,
        endpoint_type=constants.PAGE,
        name=name,
        username=username,
        password=password,
    )

    if filters:
        filters = _make_page_filters(filters)
    else:
        # NOTE: Workaround because the definition files for NAV 2009 R2 pages
        # requires the filter element to be defined (minOccurs=1), causing
        # zeep to raise a ValidationError exception. However, manually doing
        # an HTTP request to the web service, without passing in a filter
        # works. Perhaps create a ticket regarding a feature to temporarily
        # disable validation of min/maxOccurs.
        filters = _make_page_filters({zeep.helpers.Nil(): zeep.helpers.Nil()})

    if function == 'ReadMultiple':
        data = srvc.ReadMultiple(
            filter=filters,
            setSize=num_results,
        )
    elif function == 'CreateMultiple':
        kw = dict(additional_data or {})
        kw.update({
            '{}_List'.format(name): [{name: entry} for entry in entries],
        })
        data = srvc.CreateMultiple(**kw)
    else:
        raise NotImplementedError

    return zeep.helpers.serialize_object(data) or []
