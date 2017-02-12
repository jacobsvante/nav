import collections
import getpass
import functools
import json
import logging

import argh

import nav


def _set_log_level(log_level):
    nav.logger.setLevel(getattr(logging, log_level.upper()))


def _get_username(config_getter, username):
    return username or config_getter('username', None) or input('Username: ')


def _get_password(config_getter, password):
    return (
        password or
        config_getter('password', None) or
        getpass.getpass('Password: ')
    )


@argh.arg('-x', '--xmltodict-force-list', nargs='+', type=str)
def meta(
    endpoint: 'Web services endpoint',
    endpoint_type: 'Web services endpoint type',
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    json_transform: 'Return data as json' = False,
    interactive: 'Interactive mode' = True,
    xmltodict_force_list: 'Force list for these XML tags. From xmltodict.force_keys.' = (),
    log_level: 'The log level to use' = 'WARNING',
    config_section: 'The config section to get settings from.' = 'nav',
):
    """Info about an endpoint"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    username = _get_username(c, username)
    password = _get_password(c, password)
    data = nav.meta(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        base_url=c('base_url', base_url),
        username=username,
        password=password,
        to_python=json_transform,
        force_list=xmltodict_force_list,
    )
    if json_transform:
        return json.dumps(data, indent=2)
    else:
        return nav.pprint_xml(data)


@argh.arg('-f', '--filters', nargs='+', type=str)
@argh.arg('-x', '--xmltodict-force-list', nargs='+', type=str)
def codeunit(
    endpoint: 'Web services endpoint',
    function_name: 'Name of the function to run',
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    filters: 'Apply filters to the page search' = (),
    json_transform: 'Return data as json' = False,
    interactive: 'Interactive mode' = True,
    xmltodict_force_list: 'Force list for these XML keys. From xmltodict.force_keys.' = (),
    log_level: 'The log level to use' = 'WARNING',
    results_only: 'If `json_transform` is True, this controls wether to only return the results within the body of the XML envelope.' = False,
    config_section: 'The config section to get settings from.' = 'nav',
):
    """Info about an endpoint"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    username = _get_username(c, username)
    password = _get_password(c, password)
    data = nav.codeunit(
        endpoint=endpoint,
        base_url=c('base_url', base_url),
        function_name=function_name,
        username=username,
        password=password,
        filters=collections.OrderedDict(f.split('=') for f in filters),
        to_python=json_transform,
        force_list=xmltodict_force_list,
        results_only=results_only,
    )
    if json_transform:
        return json.dumps(data, indent=2)
    else:
        return nav.pprint_xml(data)


@argh.arg('-f', '--filters', nargs='+', type=str)
@argh.arg('-x', '--xmltodict-force-list', nargs='+', type=str)
def page(
    endpoint: 'Web services endpoint',
    base_url: 'The base URL for the endpoint.' = None,
    username: 'Web services username' = None,
    password: 'Web services password' = None,
    filters: 'Apply filters to the page search' = (),
    json_transform: 'Return data as json' = False,
    interactive: 'Interactive mode' = True,
    num_results: 'Amount of results to return' = 0,
    xmltodict_force_list: 'Force list for these XML keys. From xmltodict.force_keys.' = (),
    log_level: 'The log level to use' = 'WARNING',
    results_only: 'If `json_transform` is True, this controls wether to only return the results within the body of the XML envelope.' = False,
    config_section: 'The config section to get settings from.' = 'nav',
):
    """Info about an endpoint"""
    _set_log_level(log_level)
    c = functools.partial(nav.config.get, config_section)
    username = _get_username(c, username)
    password = _get_password(c, password)
    data = nav.page(
        endpoint=endpoint,
        base_url=c('base_url', base_url),
        username=username,
        password=password,
        filters=collections.OrderedDict(f.split('=') for f in filters),
        to_python=json_transform,
        num_results=num_results,
        force_list=xmltodict_force_list,
        results_only=results_only,
    )
    if json_transform:
        return json.dumps(data, indent=2)
    else:
        return nav.pprint_xml(data)


command_parser = argh.ArghParser()
command_parser.add_commands([
    meta,
    codeunit,
    page,
])
main = command_parser.dispatch
