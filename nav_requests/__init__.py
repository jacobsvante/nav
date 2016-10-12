"""Make Microsoft Dynamics NAV Web Services requests

# Endpoint URL format is::

    http://<Server>:<WebServicePort>/<ServerInstance>/WS/<CompanyName>/Page/<ServiceName>

More info here::

    https://msdn.microsoft.com/en-us/library/dd355398.aspx
"""
import getpass
import os

import argh
import lxml.etree
import requests
import requests_ntlm


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
    resp.raise_for_status()
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
    password: 'Web services password' = None
):
    """Info"""
    username, password = _username_and_password(username, password)
    resp = request('GET', endpoint_url, username, password)
    return format_xml(resp.text)


def page_results(
    endpoint_url: 'Web services endpoint URL',
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    num_results: 'Amount of results to return' = 0
):
    """Get a Page's results"""
    username, password = _username_and_password(username, password)
    page = endpoint_url.rpartition('/')[2].lower()
    resp = request(
        'POST', endpoint_url, username, password,
        headers={
            'SOAPAction': 'urn:microsoft-dynamics-schemas/page/{}:ReadMultiple'
        },
        data="""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sal="urn:microsoft-dynamics-schemas/page/{page}">
              <soapenv:Header/>
              <soapenv:Body>
                 <sal:ReadMultiple>
                    <sal:setSize>{num_results}</sal:setSize>
                 </sal:ReadMultiple>
              </soapenv:Body>
            </soapenv:Envelope>
        """.format(page=page, num_results=num_results),
    )
    return format_xml(resp.text)


def main():
    os.environ['INTERACTIVE'] = '1'
    command_parser.dispatch()


command_parser = argh.ArghParser()
command_parser.add_commands([
    meta,
    page_results,
])
