import re
import subprocess as subp

import pytest
import responses

import nav

BASE_URL = 'http://navtest:7080/DynamicsNAV/WS/CRONUS-Company-Ltd/'

PAGE_RESPONSE_DATA = """
<Soap:Envelope xmlns:Soap="http://schemas.xmlsoap.org/soap/envelope/">
  <Soap:Body>
    <ReadMultiple_Result xmlns="urn:microsoft-dynamics-schemas/page/customerlist">
      <ReadMultiple_Result>
        <CustomerList>
          <No>123456</No>
          <Name>Test customer #1</Name>
        </CustomerList>
        <CustomerList>
          <No>123457</No>
          <Name>Test customer #2</Name>
        </CustomerList>
      </ReadMultiple_Result>
    </ReadMultiple_Result>
  </Soap:Body>
</Soap:Envelope>
"""

CODEUNIT_RESPONSE_DATA = """
<Soap:Envelope xmlns:Soap="http://schemas.xmlsoap.org/soap/envelope/">
  <Soap:Body>
    <ItemListFunction_Result xmlns="urn:microsoft-dynamics-schemas/codeunit/ItemList">
      <Row xmlns="urn:microsoft-dynamics-nav/xmlports/x50040">
        <ItemNo>123</ItemNo>
        <SizeId>S</SizeId>
        <ColorId>Red</ColorId>
      </Row>
    </ItemListFunction_Result>
  </Soap:Body>
</Soap:Envelope>
"""


def request_callback(request):
    if '/Codeunit' in request.url:
        data = CODEUNIT_RESPONSE_DATA
    elif '/Page/' in request.url:
        data = PAGE_RESPONSE_DATA
    else:
        data = ''
    return (200, {}, data)


@pytest.fixture
def add_dummy_response():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add_callback(
            responses.GET,
            re.compile(BASE_URL + '(Page|Codeunit)/.+'),
            callback=request_callback,
            content_type='application/xml'
        )
        rsps.add_callback(
            responses.POST,
            re.compile(BASE_URL + '(Page|Codeunit)/.+'),
            callback=request_callback,
            content_type='application/xml'
        )
        yield


@pytest.mark.usefixtures('add_dummy_response')
def test_meta():
    data = nav.meta(BASE_URL, 'Codeunit', 'MetaTest', 'x', 'y')
    assert data


@pytest.mark.usefixtures('add_dummy_response')
def test_codeunit():
    args = [BASE_URL, 'ItemList', 'ItemListFunction', 'x', 'y']
    data = nav.codeunit(*args, results_only=True)
    assert data['Row']['ItemNo'] == '123'


@pytest.mark.usefixtures('add_dummy_response')
def test_codeunit_force_list():
    args = [BASE_URL, 'ItemList', 'ItemListFunction', 'x', 'y']
    data = nav.codeunit(*args, results_only=True, force_list=['Row'])
    assert data['Row'][0]['ItemNo'] == '123'


@pytest.mark.usefixtures('add_dummy_response')
def test_page():
    args = [BASE_URL, 'CustomerList', 'x', 'y']
    data = nav.page(*args, results_only=True)
    assert data[0]['No'] == '123456'
    assert data[1]['No'] == '123457'


def test_entry_point_runnable():
    proc = subp.run(['nav'], stdout=subp.PIPE)
    assert b'{meta,codeunit,page}' in proc.stdout
