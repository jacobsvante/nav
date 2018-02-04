from lxml import etree
from zeep import Plugin


class RemoveNamespacePlugin(Plugin):
    """Remove a namespace declaration and corresponding prefixes before sending off the XML to NAV.

    Useful when NAV complains about `The Element <ns1:XXX> is unexpected` (possibly fixable by using https://support.microsoft.com/en-hk/help/2509042/-the-element-is-unexpected-error-message-when-you-run-certain-xml-port)

    Args:
        namespace (str):
            The namespace to remove.
            E.g: 'urn:microsoft-dynamics-nav/xmlports/x50001'
    """

    def __init__(self, namespace):
        self.namespace = namespace

    def egress(self, envelope, http_headers, operation, binding_options):
        ns = u'{%s}' % self.namespace
        nsl = len(ns)

        for elem in envelope.getiterator():
            if elem.tag.startswith(ns):
                elem.tag = elem.tag[nsl:]

        etree.cleanup_namespaces(envelope)

        return envelope, http_headers
