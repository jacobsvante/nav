import collections
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


def meta(
    endpoint_type: 'Web services endpoint type',
    service_name: 'Web services endpoint',
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    log_level: 'The log level to use' = None,
    insecure: "Skip certificate validation over HTTPS connections" = False,
    config_section: 'The config section to get settings from.' = 'nav',
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


@argh.arg('-t', '--endpoint-type', type=str)
@argh.arg('-e', '--endpoint', type=str)
def interact(
    endpoint_type: 'Web services endpoint type' = None,
    endpoint: 'Web services endpoint' = None,
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    log_level: 'The log level to use' = None,
    insecure: "Skip certificate validation over HTTPS connections" = False,
    config_section: 'The config section to get settings from.' = 'nav',
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
    results = service.ReadMultiple(filter=dict(No='123'), setSize=0)

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
        banner1 = banner1_tmpl.format(
            additional_arg='`{0}` - Service to run WS calls against'.format(endpoint.lower()),
            additional_arg_example="{0}_results = {0}.ReadMultiple(filter=dict(Field='MyField', Criteria='My criteria'), setSize=0)".format(endpoint.lower())
        )
        user_ns[endpoint.lower()] = create_service(endpoint_type, endpoint)
    else:
        banner1 = banner1_tmpl.format(
            additional_arg='',
            additional_arg_example='',
        )

    IPython.embed(
        user_ns=user_ns,
        banner1=banner1,
        config=traitlets.config.Config(colors='LightBG')
    )


@argh.arg('-f', '--func-args', nargs='+', type=str)
def codeunit(
    service_name: 'Name of the code unit',
    func: 'Name of the function to run',
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    func_args: 'Add these kw args to the codeunit function call' = (),
    insecure: "Skip certificate validation over HTTPS connections" = False,
    log_level: 'The log level to use' = None,
    config_section: 'The config section to get settings from.' = 'nav',
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
            collections.OrderedDict(f.split('=') for f in func_args)
        ),
        verify_certificate=not insecure,
    )
    return json.dumps(data, indent=2)


@argh.arg('-f', '--filters', nargs='+', type=str)
@argh.arg('-n', '--num-results')
@argh.arg('-e', '--entries', nargs='+', type=str)
@argh.arg('-a', '--additional_data', nargs='+', type=str)
def page(
    service_name: 'Name of the WS page',
    func: 'Name of the function to use',
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    filters: 'Filters to apply to a ReadMultiple query' = (),
    entries: 'Entries to create when function is CreateMultiple' = (),
    additional_data: 'Additional data to pass alongside the main entries to create with CreateMultiple' = (),
    num_results: 'Amount of results to return' = 0,
    log_level: 'The log level to use' = None,
    insecure: "Skip certificate validation over HTTPS connections" = False,
    config_section: 'The config section to get settings from.' = 'nav',
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
            collections.OrderedDict(f.split('=') for f in filters)
        ),
        entries=[
            nav.utils.convert_string_filter_values(
                collections.OrderedDict(
                    field.split('=') for field in entry.split(',')
                )
            )
            for entry in entries
        ],
        additional_data=nav.utils.convert_string_filter_values(
            collections.OrderedDict(
                ad.split('=') for ad in additional_data
            )
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
