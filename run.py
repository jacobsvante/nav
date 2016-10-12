"""Make Microsoft Dynamics NAV Web Services requests"""
import argh
import lxml.etree
import requests
import requests_ntlm


def format_xml(text):
    return lxml.etree.tostring(lxml.etree.fromstring(text), pretty_print=True).decode()


def request(method, url, username, password, headers=None, data=None):
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


def meta(url, username, password):
    """Get metadata about a web service endpoint"""
    resp = request('GET', url, username, password)
    return format_xml(resp.text)


def page_results(url, username, password, num_results=0):
    """Get a web services Page's results"""
    page = url.rpartition('/')[2].lower()
    resp = request(
        'POST', url, username, password,
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


parser = argh.ArghParser()

commands = [
    meta,
    page_results,
]

parser.add_commands(commands)
parser.dispatch()
