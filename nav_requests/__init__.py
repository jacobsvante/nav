"""Make Microsoft Dynamics NAV Web Services requests

# Endpoint URL format is::

    http://<Server>:<WebServicePort>/<ServerInstance>/WS/<CompanyName>/Page/<ServiceName>

More info here::

    https://msdn.microsoft.com/en-us/library/dd355398.aspx
"""
import getpass
import logging
import os

import argh
import json
import lxml.etree
import requests
import requests_ntlm
import xmltodict


logging.basicConfig()
logger = logging.getLogger('navrequest')


def format_xml(text):
    return lxml.etree.tostring(lxml.etree.fromstring(text), pretty_print=True).decode()


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
    except:
        logger.error(resp.text)
        raise
    return resp


def _username_and_password(username, password):
    interactive = 'INTERACTIVE' in os.environ
    if username is None:
        if interactive:
            username = input('Username: ')
    if password is None:
        if interactive:
            password = getpass.getpass('Password: ')
    return (username, password)


def meta(
    endpoint_url: 'Web services endpoint URL',
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    log_level: 'The log level to use' = 'INFO',
):
    """Info about an endpoint"""
    logger.setLevel(getattr(logging, log_level.upper()))
    username, password = _username_and_password(username, password)
    resp = request('GET', endpoint_url, username, password)
    return format_xml(resp.text)


@argh.arg('-f', '--filters', nargs='+', type=str)
def codeunit(
    endpoint_url: 'Web services endpoint URL',
    function_name: 'Name of the function to run',
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    num_results: 'Amount of results to return' = 0,
    filters: 'Apply filters to the page search' = (),
    json_transform: 'Return data as json' = False,
    log_level: 'The log level to use' = 'INFO',
):
    """Get a Codeunit's results"""
    logger.setLevel(getattr(logging, log_level.upper()))
    username, password = _username_and_password(username, password)
    codeunit = endpoint_url.rpartition('/')[2]

    payload_tmpl = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:int="urn:microsoft-dynamics-schemas/codeunit/{codeunit}" xmlns:x50="urn:microsoft-dynamics-nav/xmlports/x50033">
    <soapenv:Header/>
    <soapenv:Body>
        <int:{function_name}>
            {filters}
        </int:{function_name}>
    </soapenv:Body>
</soapenv:Envelope>
    """
    filter_tmpl = """<int:{0}>{1}</int:{0}>"""
    filters = (
        '\n'.join([
            filter_tmpl.format(*f)
            for f in [fil.split('=') for fil in filters]
        ])
    )
    payload = payload_tmpl.format(
        num_results=num_results,
        function_name=function_name,
        filters=filters,
        codeunit=codeunit,
    )
    logger.debug('payload:{}'.format(payload))
    resp = request(
        'POST', endpoint_url, username, password,
        headers={
            'SOAPAction': (
                'urn:microsoft-dynamics-schemas/codeunit/{}:{}'
                .format(codeunit, function_name)
            )
        },
        data=payload,
    )
    data = format_xml(resp.text)
    if json_transform:
        dct = xmltodict.parse(data)
        results = (
            dct['Soap:Envelope']['Soap:Body']
            ['{}_Result'.format(function_name)]
        )
        return json.dumps(results, indent=2)
    return format_xml(resp.text)


@argh.arg('-f', '--filters', nargs='+', type=str)
def page(
    endpoint_url: 'Web services endpoint URL',
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    num_results: 'Amount of results to return' = 0,
    filters: 'Apply filters to the page search' = (),
    json_transform: 'Return data as json' = False,
    log_level: 'The log level to use' = 'INFO',
):
    """Get a Page's results"""
    logger.setLevel(getattr(logging, log_level.upper()))
    username, password = _username_and_password(username, password)
    page = endpoint_url.rpartition('/')[2]
    filter_tmpl = """<sal:filter>
       <sal:Field>{}</sal:Field>
       <sal:Criteria>{}</sal:Criteria>
    </sal:filter>"""
    payload_tmpl = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sal="urn:microsoft-dynamics-schemas/page/{page_lower}">
          <soapenv:Header/>
          <soapenv:Body>
             <sal:ReadMultiple>
                {filters}
                <sal:setSize>{num_results}</sal:setSize>
             </sal:ReadMultiple>
          </soapenv:Body>
        </soapenv:Envelope>
    """
    filters = (
        '\n'.join([
            filter_tmpl.format(*f)
            for f in [fil.split('=') for fil in filters]
        ])
    )
    payload = payload_tmpl.format(
        filters=filters,
        page_lower=page.lower(),
        num_results=num_results,
    )
    logger.debug('payload:{}'.format(payload))
    resp = request(
        'POST', endpoint_url, username, password,
        headers={
            'SOAPAction': (
                'urn:microsoft-dynamics-schemas/page/{}:ReadMultiple'
                .format(page)
            )
        },
        data=payload,
    )
    data = format_xml(resp.text)
    if json_transform:
        dct = xmltodict.parse(data)
        results = (
            dct['Soap:Envelope']['Soap:Body']['ReadMultiple_Result']
            ['ReadMultiple_Result']
        )
        if results is None:
            results = []
        else:
            results = results[page]
        return json.dumps(results, indent=2)
    return data


def main():
    os.environ['INTERACTIVE'] = '1'
    command_parser.dispatch()


command_parser = argh.ArghParser()
command_parser.add_commands([
    meta,
    codeunit,
    page,
])
