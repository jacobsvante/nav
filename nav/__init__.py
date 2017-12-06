"""Conveniently make requests to Microsoft Dynamics NAV Web Services

Tested with Dynamics NAV 2009 R2. A lot of assumptions have been made while
making this project, so it cannot be guaranteed that it will work for everyone.

# Endpoint URL format is::

    http://<Server>:<WebServicePort>/<ServerInstance>/WS/<CompanyName>/<EndpointType>/<EndpointName>

More info here::

    https://msdn.microsoft.com/en-us/library/dd355398.aspx
"""
import logging

import lxml.etree
import requests
import requests_ntlm
import xml.sax.saxutils
import xmltodict

from . import config  # noqa
from ._metadata import __version__, __version_info__  # noqa

NOT_SET = object()

logging.basicConfig()
logger = logging.getLogger('nav')


def pprint_xml(etree, pretty_print=True):
    return lxml.etree.tostring(etree, pretty_print=pretty_print).decode()


def _make_endpoint_url(base_url, *args):
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return '/'.join([base_url, *args])


def _make_filters(filter_template, filters):
    return '\n'.join([
        filter_template.format(k, xml.sax.saxutils.escape(v))
        for k, v in (filters or {}).items()
    ])


def _extract_results(data, tags, default=NOT_SET):
    for tag in tags:
        data = data[tag]
        if data is None:
            if default is NOT_SET:
                raise ValueError(
                    'Data was `None`, expected value for tag {}.'.format(tag)
                )
            else:
                return default
    return data


def request(
        method,
        url,
        username,
        password,
        headers=None,
        data=None
):
    resp = requests.request(
        method,
        url,
        auth=requests_ntlm.HttpNtlmAuth(username, password),
        headers=dict(
            **{'content-type': 'text/xml;charset=UTF-8'},
            **(headers or {})
        ),
        data=data,
    )
    try:
        resp.raise_for_status()
    except Exception:
        logger.error(resp.text)
        raise
    return resp


def meta(
    base_url: 'The base URL for the endpoint.',
    endpoint_type: 'The endpoint type ("Page" or "Codeunit")',
    endpoint: 'Web services endpoint (i.e. the last part of the URL)',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
    to_python: 'Convert to standard python data structures instead of an lxml tree.' = True,
    force_list: 'If `to_python` is also True then this setting allows forcing specified element tags to always be returned as lists, even if they only contain a single child element (standard behavior is to convert to dict then).' = (),
):
    """Info about an endpoint"""
    assert endpoint_type in ('Page', 'Codeunit')
    endpoint_url = _make_endpoint_url(base_url, endpoint_type, endpoint)
    resp = request('GET', endpoint_url, username, password)
    if to_python:
        return xmltodict.parse(resp.text, force_list=force_list)
    else:
        return lxml.etree.fromstring(resp.text)


def codeunit(
    base_url: 'The base URL for the endpoint.',
    endpoint: 'The code unit to fetch',
    function_name: 'Name of the function to run',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
    filters: 'Apply filters to the page search' = None,
    to_python: 'Convert to standard python data structures instead of an lxml tree.' = True,
    results_only: 'If `to_python` is True, this controls wether to only return the results within the body of the XML envelope.' = True,
    force_list: 'If `to_python` is also True then this setting allows forcing specified element tags to always be returned as lists, even if they only contain a single child element (standard behavior is to convert to dict then).' = (),
):
    """Get a Codeunit's results"""
    endpoint_url = _make_endpoint_url(base_url, 'Codeunit', endpoint)

    payload_tmpl = """
<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:int="urn:microsoft-dynamics-schemas/codeunit/{codeunit}" xmlns:x50="urn:microsoft-dynamics-nav/xmlports/x50033">
    <soapenv:Header/>
    <soapenv:Body>
        <int:{function_name}>
            {filters}
        </int:{function_name}>
    </soapenv:Body>
</soapenv:Envelope>
    """
    filters = _make_filters("<int:{0}>{1}</int:{0}>", filters)
    payload = payload_tmpl.format(
        function_name=function_name,
        filters=filters,
        codeunit=endpoint,
    ).strip().encode('utf-8')
    logger.info('request to:{}'.format(endpoint_url))
    logger.info('payload:{}'.format(payload))
    resp = request(
        'POST', endpoint_url, username, password,
        headers={
            'SOAPAction': (
                'urn:microsoft-dynamics-schemas/codeunit/{}:{}'
                .format(endpoint, function_name)
            )
        },
        data=payload,
    )
    if to_python:
        data = xmltodict.parse(resp.text, force_list=force_list)
        if results_only:
            return _extract_results(
                data,
                [
                    'Soap:Envelope',
                    'Soap:Body',
                    '{}_Result'.format(function_name),
                ],
            )
        else:
            return data
    else:
        return lxml.etree.fromstring(resp.text)


def render_ReadMultiple_page_template(page, filters, num_results):
        generated_filters = _make_filters(
            """
            <sal:filter>
                <sal:Field>{}</sal:Field>
                <sal:Criteria>{}</sal:Criteria>
            </sal:filter>
            """,
            filters,
        )
        return """
            <?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sal="urn:microsoft-dynamics-schemas/page/{page_lower}">
              <soapenv:Header/>
              <soapenv:Body>
                 <sal:ReadMultiple>
                    {filters}
                    <sal:setSize>{num_results}</sal:setSize>
                 </sal:ReadMultiple>
              </soapenv:Body>
            </soapenv:Envelope>
        """.format(
            page_lower=page.lower(),
            filters=generated_filters,
            num_results=num_results,
        )


def render_CreateMultiple_page_template(page, entries, num_results):
        generated_entries = []
        for entry in entries:
            generated_entry = ''
            for key, val in entry.items():
                generated_entry += '<{0}>{1}</{0}>\n'.format(
                    key,
                    xml.sax.saxutils.escape((val)),
                )
            generated_entries.append(generated_entry)
        joined_generated_entries = '\n'.join([
            '<{0}>{1}</{0}>'.format(page, e)
            for e in generated_entries
        ])

        return """
        <?xml version="1.0" encoding="utf-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sal="urn:microsoft-dynamics-schemas/page/{page_lower}">
          <soapenv:Header/>
            <soapenv:Body>
                <CreateMultiple xmlns="urn:microsoft-dynamics-schemas/page/{page_lower}">
                    <{page}_List>
                        {entries}
                    </{page}_List>
                </CreateMultiple>
            </soapenv:Body>
        </soapenv:Envelope>
        """.format(
            page=page,
            page_lower=page.lower(),
            entries=joined_generated_entries,
        )


def render_page_template(method, page, **tmpl_kw):
    if method == 'ReadMultiple':
        return render_ReadMultiple_page_template(
            page=page,
            filters=tmpl_kw.pop('filters'),
            num_results=tmpl_kw.pop('num_results'),
        )
    elif method == 'CreateMultiple':
        return render_CreateMultiple_page_template(
            page=page,
            entries=tmpl_kw.pop('entries'),
            num_results=tmpl_kw.pop('num_results'),
        )
    else:
        raise RuntimeError('Unsupported method {}'.format(method))


def page(
    base_url: 'The base URL for the endpoint.',
    method: 'The method to use. Currently supported methods are ReadMultiple and CreateMultiple.',
    endpoint: 'The page to fetch',
    username: 'Username (usually includes AD domain)',
    password: 'Password',
    num_results: 'Maximum amount of results to return for ReadMultiple. Defaults to no limit.' = 0,
    filters: 'Apply filters to a ReadMultiple result' = None,
    entries: 'Entries to pass to CreateMultiple' = None,
    to_python: 'Convert to standard python data structures instead of an lxml tree.' = True,
    results_only: 'If `to_python` is True, this controls wether to only return the results within the body of the XML envelope.' = True,
    force_list: 'If `to_python` is also True then this setting allows forcing specified element tags to always be returned as lists, even if they only contain a single child element (standard behavior is to convert to dict then). Default is to apply this to elements with same name as the specified entrypoint. Set to False to disable this default.' = None,
):
    """Get a Page's results"""
    endpoint_url = _make_endpoint_url(base_url, 'Page', endpoint)
    payload = render_page_template(
        method,
        page=endpoint,
        filters=filters,
        entries=entries,
        num_results=num_results,
    ).strip().encode('utf-8')

    logger.info('request to:{}'.format(endpoint_url))
    logger.info('payload:{}'.format(payload))
    resp = request(
        'POST',
        endpoint_url,
        username,
        password,
        headers={
            'SOAPAction': (
                'urn:microsoft-dynamics-schemas/page/{}:{}'
                .format(endpoint, method)
            )
        },
        data=payload,
    )

    if to_python:
        if force_list is None:
            xmltodict_kw = {'force_list': endpoint}
        else:
            xmltodict_kw = {} if force_list is False else force_list
        data = xmltodict.parse(resp.text, **xmltodict_kw)
        if results_only:
            result_tag = '{}_Result'.format(method)
            tags = ['Soap:Envelope', 'Soap:Body', result_tag]
            if method == 'ReadMultiple':
                tags.append(result_tag)
            elif method == 'CreateMultiple':
                tags.append('{}_List'.format(endpoint))
            return _extract_results(
                data,
                [*tags, endpoint],
                default=[],
            )
        else:
            return data
    else:
        return lxml.etree.fromstring(resp.text)
