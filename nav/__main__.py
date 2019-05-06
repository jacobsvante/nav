import getpass
import functools
import logging
import logging.config

import IPython
import argh
import lxml
import traitlets

import nav
import nav.utils
from nav.wrappers import json


def _set_log_level(log_level):
    if log_level is not None:
        level = getattr(logging, log_level.upper())
        logging.basicConfig()
        logging.getLogger('zeep').setLevel(level)
        nav.logger.setLevel(level)


def _get_username(config_getter, username):
    return username or config_getter('username', None) or input('Username: ')


def _get_password(config_getter, password):
    return (
        password or
        config_getter('password', None) or
        getpass.getpass('Password: ')
    )


@argh.arg('endpoint-type', help='Web services endpoint type')
@argh.arg('service-name', help='Web services endpoint')
@argh.arg('-b', '--base-url', help='The base URL for the endpoint.')
@argh.arg('-u', '--username', help='Web services username')
@argh.arg('-p', '--password', help='Web services password')
@argh.arg('-l', '--log-level', help='The log level to use')
@argh.arg('-i', '--insecure', help="Skip certificate validation over HTTPS connections")
@argh.arg('-c', '--config-section', help='The config section to get settings from.')
def meta(
    endpoint_type,
    service_name,
    base_url=None,
    username=None,
    password=None,
    log_level=None,
    insecure=False,
    config_section='nav'
):
    """Print the definition of a Codeunit or a Page"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    username = _get_username(c, username)
    password = _get_password(c, password)
    data = nav.meta(
        endpoint_type=endpoint_type,
        service_name=service_name,
        base_url=c('base_url', base_url),
        username=username,
        password=password,
        verify_certificate=not insecure,
    )
    return lxml.etree.tostring(data, pretty_print=True).decode()


@argh.arg('-t', '--endpoint-type')
@argh.arg('-e', '--endpoint')
@argh.arg('-b', '--base-url', help='The base URL for the endpoint.')
@argh.arg('-u', '--username', help='Web services username')
@argh.arg('-p', '--password', help='Web services password')
@argh.arg('-l', '--log-level', help='The log level to use')
@argh.arg('-i', '--insecure', help="Skip certificate validation over HTTPS connections")
@argh.arg('-c', '--config-section', help='The config section to get settings from.')
def interact(
    endpoint_type=None,
    endpoint=None,
    base_url=None,
    username=None,
    password=None,
    log_level=None,
    insecure=False,
    config_section='nav'
):
    """Starts a REPL to enable live interaction with a WSDL endpoint"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    base_url = c('base_url', base_url)
    username = _get_username(c, username)
    password = _get_password(c, password)

    banner1_tmpl = """Welcome to nav client interactive mode
Available vars:
    {additional_arg}
    `create_service` - Create a WS service to make calls to

Example usage:
    service = create_service('Page', 'ItemList')
    item_filter = dict(Field='No', Criteria='12345')
    results = service.ReadMultiple(filter=item_filter, setSize=0)

    {additional_arg_example}
"""

    def create_service(endpoint_type, service_name):
        return nav.service(
            base_url,
            username,
            password,
            endpoint_type,
            service_name,
            verify_certificate=not insecure,
        )

    user_ns = {
        'create_service': create_service,
    }

    if endpoint_type and endpoint:
        endpoint_var = endpoint.lower()
        tmpl_kw = {
            'additional_arg': f'`{endpoint_var}` - Service for {endpoint_type} {endpoint}',
            'additional_arg_example': f"{endpoint_var}_results = {endpoint_var}.ReadMultiple(filter=dict(Field='MyField', Criteria='My criteria'), setSize=0)" if endpoint_type == 'Page' else '',
        }
        banner1 = banner1_tmpl.format(**tmpl_kw)
        user_ns[endpoint_var] = create_service(endpoint_type, endpoint)
    else:
        banner1 = banner1_tmpl.format(
            additional_arg='',
            additional_arg_example='',
        )

    IPython.embed(
        user_ns=user_ns,
        banner1=banner1,
        config=traitlets.config.Config(colors='LightBG'),
        # To fix no colored input we pass in `using=False`
        # See: https://github.com/ipython/ipython/issues/11523
        # TODO: Remove once this is fixed upstream
        using=False,
    )


@argh.arg('service-name', help='Name of the code unit')
@argh.arg('func', help='Name of the function to run')
@argh.arg('-b', '--base-url', help='The base URL for the endpoint.')
@argh.arg('-u', '--username', help='Web services username')
@argh.arg('-p', '--password', help='Web services password')
@argh.arg('-f', '--func-args', nargs='+', type=str, help='Add these kw args to the codeunit function call')
@argh.arg('-i', '--insecure', help="Skip certificate validation over HTTPS connections")
@argh.arg('-l', '--log-level', help='The log level to use')
@argh.arg('-c', '--config-section', help='The config section to get settings from.')
def codeunit(
    service_name,
    func,
    base_url=None,
    username=None,
    password=None,
    func_args=(),
    insecure=False,
    log_level=None,
    config_section='nav'
):
    """Get a Codeunit's results"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    username = _get_username(c, username)
    password = _get_password(c, password)
    data = nav.codeunit(
        base_url=c('base_url', base_url),
        username=username,
        password=password,
        service_name=service_name,
        function=func,
        func_args=nav.utils.convert_string_filter_values(
            dict(f.split('=') for f in func_args)
        ),
        verify_certificate=not insecure,
    )
    return json.dumps(data, indent=2)


@argh.arg('service-name', help='Name of the WS page')
@argh.arg('func', help='Name of the function to use')
@argh.arg('-b', '--base-url', help='The base URL for the endpoint.')
@argh.arg('-u', '--username', help='Web services username')
@argh.arg('-p', '--password', help='Web services password')
@argh.arg('-f', '--filters', nargs='+', type=str, help='Filters to apply to a ReadMultiple query')
@argh.arg('-e', '--entries', nargs='+', type=str, help='Entries to create when function is CreateMultiple')
@argh.arg('-a', '--additional-data', nargs='+', type=str, help='Additional data to pass alongside the main entries to create with CreateMultiple')
@argh.arg('-n', '--num-results', help='Amount of results to return')
@argh.arg('-l', '--log-level', help='The log level to use')
@argh.arg('-i', '--insecure', help="Skip certificate validation over HTTPS connections")
@argh.arg('-c', '--config-section', help='The config section to get settings from.')
def page(
    service_name,
    func,
    base_url=None,
    username=None,
    password=None,
    filters=(),
    entries=(),
    additional_data=(),
    num_results=0,
    log_level=None,
    insecure=False,
    config_section='nav'
):
    """Get a Page's results"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    username = _get_username(c, username)
    password = _get_password(c, password)

    data = nav.page(
        base_url=c('base_url', base_url),
        username=username,
        password=password,
        service_name=service_name,
        function=func,
        verify_certificate=not insecure,
        filters=nav.utils.convert_string_filter_values(
            dict(f.split('=') for f in filters)
        ),
        entries=[
            nav.utils.convert_string_filter_values(
                dict(field.split('=') for field in entry.split(','))
            )
            for entry in entries
        ],
        additional_data=nav.utils.convert_string_filter_values(
            dict(ad.split('=') for ad in additional_data)
        ),
        num_results=num_results,
    )
    return json.dumps(data, indent=2)


command_parser = argh.ArghParser()
command_parser.add_commands([
    interact,
    meta,
    codeunit,
    page,
])
main = command_parser.dispatch
