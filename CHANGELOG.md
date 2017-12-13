# Changelog

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
