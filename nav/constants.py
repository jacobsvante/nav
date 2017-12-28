from zeep.xsd.elements.element import NotSet

DEFAULT_WSDL_CACHE_EXPIRATION = 3600

CODEUNIT = 'Codeunit'
PAGE = 'Page'

ReadMultiple = 'ReadMultiple'
CreateMultiple = 'CreateMultiple'

STRING_VALUE_TO_PYTHON_TYPE_MAPPING = {
    'NotSet': NotSet,
    'TRUE': True,
    'FALSE': False,
}
