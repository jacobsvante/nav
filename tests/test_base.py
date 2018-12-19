import os
import re
import subprocess as subp

import lxml.etree
import pytest
import responses

import nav

BASE_URL = 'http://navtest:7080/DynamicsNAV/WS/CRONUS-Company-Ltd/'

PAGE_READMULTIPLE_RESPONSE_DATA = """
<Soap:Envelope xmlns:Soap="http://schemas.xmlsoap.org/soap/envelope/">
  <Soap:Body>
    <ReadMultiple_Result xmlns="urn:microsoft-dynamics-schemas/page/customerlist">
      <ReadMultiple_Result>
        <CustomerList>
          <No>123</No>
          <Name>Customer #1</Name>
        </CustomerList>
        <CustomerList>
          <No>456</No>
          <Name>Customer #2</Name>
        </CustomerList>
      </ReadMultiple_Result>
    </ReadMultiple_Result>
  </Soap:Body>
</Soap:Envelope>
"""

PAGE_CREATEMULTIPLE_RESPONSE_DATA = """
<Soap:Envelope xmlns:Soap="http://schemas.xmlsoap.org/soap/envelope/">
  <Soap:Body>
    <CreateMultiple_Result xmlns="urn:microsoft-dynamics-schemas/page/customerlist">
      <CustomerList_List>
        <CustomerList>
          <No>234567</No>
          <Name>Happy Customer Inc</Name>
        </CustomerList>
        <CustomerList>
          <No>345678</No>
          <Name>Cool Guy Inc</Name>
        </CustomerList>
      </CustomerList_List>
    </CreateMultiple_Result>
  </Soap:Body>
</Soap:Envelope>
"""

CODEUNIT_RESPONSE_DATA = """
<Soap:Envelope xmlns:Soap="http://schemas.xmlsoap.org/soap/envelope/">
  <Soap:Body>
    <HelloWorld_Result xmlns="urn:microsoft-dynamics-schemas/codeunit/IntegrationEntry">
      <return_value>true</return_value>
      <oGreeting>Test greeting</oGreeting>
    </HelloWorld_Result>
  </Soap:Body>
</Soap:Envelope>
"""


def dummy_request_callback(request):
    if '/Codeunit' in request.url:
        data = CODEUNIT_RESPONSE_DATA
    elif '/Page/' in request.url:
        if nav.CreateMultiple in request.headers['SOAPAction']:
            data = PAGE_CREATEMULTIPLE_RESPONSE_DATA
        else:
            data = PAGE_READMULTIPLE_RESPONSE_DATA
    else:
        raise RuntimeError
    return (200, {}, data)


@pytest.fixture
def add_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            re.compile(BASE_URL + 'Page/CustomerList'),
            body=open(os.path.join(
                os.path.dirname(__file__),
                'wsdl/page-CustomerList.xml',
            )).read(),
            content_type='application/xml',
        )
        rsps.add(
            responses.GET,
            re.compile(BASE_URL + 'Codeunit/IntegrationEntry'),
            body=open(os.path.join(
                os.path.dirname(__file__),
                'wsdl/codeunit-IntegrationEntry.xml',
            )).read(),
            content_type='application/xml',
        )
        rsps.add_callback(
            responses.POST,
            re.compile(BASE_URL + '(Page|Codeunit)/.+'),
            callback=dummy_request_callback,
            content_type='application/xml'
        )
        yield


@pytest.mark.usefixtures('add_responses')
def test_nav_class():
    nv = nav.NAV(BASE_URL, 'x', 'y')

    data = nv.page('CustomerList', nav.ReadMultiple)
    assert data[0]['No'] == '123'
    assert data[1]['No'] == '456'

    data = nv.codeunit(
        'IntegrationEntry',
        'HelloWorld',
        func_args=dict(
            iName='DISCARDED',
            oGreeting='TEST'
        ),
    )
    assert data['oGreeting'] == 'Test greeting'


@pytest.mark.usefixtures('add_responses')
def test_nav_class_service_cache():
    nv = nav.NAV(BASE_URL, 'x', 'y')

    assert len(nv._service_cache) == 0

    nv.page('CustomerList', nav.ReadMultiple)
    assert len(nv._service_cache) == 1

    nv.page('CustomerList', nav.ReadMultiple)
    assert len(nv._service_cache) == 1

    nv.page('CustomerList', nav.CreateMultiple, entries=[{}])
    assert len(nv._service_cache) == 1  # Still same WS endpoint

    nv.codeunit(
        'IntegrationEntry',
        'HelloWorld',
        func_args=dict(
            iName='DISCARDED',
            oGreeting='TEST'
        ),
    )
    assert len(nv._service_cache) == 2


@pytest.mark.usefixtures('add_responses')
def test_service():
    srvc = nav.service(BASE_URL, 'x', 'y', 'Codeunit', 'IntegrationEntry')
    data = srvc.HelloWorld(iName='DISCARDED', oGreeting='TEST')
    assert data['oGreeting'] == 'Test greeting'


@pytest.mark.usefixtures('add_responses')
def test_meta():
    data = nav.meta(BASE_URL, 'x', 'y', 'Codeunit', 'IntegrationEntry')
    data_bytes = lxml.etree.tostring(data)
    assert b'HelloWorld_Result' in data_bytes


@pytest.mark.usefixtures('add_responses')
def test_codeunit_HelloWorld():
    data = nav.codeunit(
        BASE_URL,
        'x',
        'y',
        'IntegrationEntry',
        'HelloWorld',
        func_args=dict(iName='DISCARDED', oGreeting='TEST'),
    )
    assert data['oGreeting'] == 'Test greeting'


@pytest.mark.usefixtures('add_responses')
def test_page_ReadMultiple():
    data = nav.page(BASE_URL, 'x', 'y', 'CustomerList', nav.ReadMultiple)
    assert data[0]['No'] == '123'
    assert data[1]['No'] == '456'


@pytest.mark.usefixtures('add_responses')
def test_nav_class_read_multiple():
    nv = nav.NAV(BASE_URL, 'x', 'y')

    data1 = nv.page('CustomerList', nav.ReadMultiple)
    data2 = nv.read_multiple('CustomerList')
    assert data1 == data2


@pytest.mark.usefixtures('add_responses')
def test_page_CreateMultiple():
    data = nav.page(
        BASE_URL,
        'x',
        'y',
        'CustomerList',
        nav.CreateMultiple,
        entries=[
            {'No': 'DISCARDED', 'Name': 'DISCARDED'},
            {'No': 'DISCARDED', 'Name': 'DISCARDED'},
        ],
    )
    assert data[0]['No'] == '234567'
    assert data[1]['No'] == '345678'


@pytest.mark.usefixtures('add_responses')
def test_nav_class_create_multiple():
    nv = nav.NAV(BASE_URL, 'x', 'y')

    data1 = nav.page(
        BASE_URL,
        'x',
        'y',
        'CustomerList',
        nav.CreateMultiple,
        entries=[{}],
    )
    data2 = nv.create_multiple(
        'CustomerList',
        entries=[{}],
    )
    assert data1 == data2


def test_entry_point_runnable():
    proc = subp.run(['nav'], stdout=subp.PIPE)
    assert b'{interact,meta,codeunit,page}' in proc.stdout
