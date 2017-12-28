# Changelog

## 5.0.1 (2017-12-28)

* Fix some regressions introduced by the 5.0.0 release

## 5.0.0 (2017-12-28)

Never thought I'd have to do this but here's the second major version in the same day. Had to bump because order of arguments to `nav.meta/service/page/codeunit` has changed again and some arguments have been renamed to not be misleading.

* Feature: New class `nav.NAV` for easier programmatic access
* Feature: Shortcut methods on `nav.NAV` object - `nav.NAV.read_multiple()` and `nav.NAV.create_multiple()`
* Feature: Cache WS client service objects to speed up subsequent calls to WS endpoints
* Feature: Add in-memory WSDL and XSD definition caching for faster access when calling the same endpoint multiple times. Defaults to 3600 seconds and can be overridden in the `nav.NAV` constructor


## 4.0.0 (2017-12-28)

* Rewrite to make use of the dedicated SOAP library `zeep`, which gives us a number of benefits:
    * Always returns the correct type for all types of fields, no need for `force_list`.
    * Fields that are not returned in the HTTP response because of null values are created by zeep which should make the returned data more easy to work with.
    * Automatic validation of passed in filters and data
* Performance is a bit worse for the classic `nav.meta`, `nav.codeunit`, `nav.page` (about 20%) but this can be improved with WSDL definition caching in a future release
* Feature: New CLI command for interacting with the NAV web services
* Breaking change: `nav.page` function name argument has moved to after page name arg to make the API more consistent with `nav.codeunit`. Same goes for CLI equivalent.
* Breaking change: CLI dependencies are now an optional install. See `README.md` for details on how to install.
* Change: Don't set log level in CLI usage unless explicitly specified

## 3.0.2 (2017-12-13)

* Allow passing in additional data alongside CreateMultiple entries list

## 3.0.1 (2017-12-12)

* Only call `logging.basicConfig` when run as a CLI utility. Should be set by the user of this package when run programmatically.
* Log headers for each request
* Set request info logging to debug level

## 3.0.0 (2017-12-07)

* Add support for creating page entries with CreateMultiple. Signature for `nav.page` has changed to take `method` as its second argument. Supports ReadMultiple (previous default) and CreateMultiple.
* Default to always turning elements with the same name as the Page into lists results for ReadMultiple and CreateMultiple page results. Disable this behavior by passing in `force_list=False` to `nav.page`.

## 2.1.0 (2017-08-25)

* Explicitly pass UTF-8-encoding

## 2.0.0 (2017-02-13)

* Break out cli into own module and generally make more friendly for programmatic interaction with the library.
* Allow setting `base_url`, `username` and `password` in a config so it doesn't have to be passed in during CLI usage. In programmatic usage the config is not read. Default location for the config is `~/.config/nav.ini` but can be overridden with env-var `NAV_CONFIG`. Default config section is `nav` but can also be overridden through the commands.
* Rename project from `nav-requests` to `nav`
* Rename command from `navrequest` to `nav`

## 1.1.2 (2017-02-03)

* Allow forcing type to list for specified elements by passing in a list of space separated names to `--xml-force-list`

## 1.1.1 (2017-01-30)

* Escape passed in filter values

## 1.1.0 (2016-12-21)

* Call codeunits
* Ability to pass in filters to page/codeunit

## 1.0.0 (2016-10-12)

* Initial version
