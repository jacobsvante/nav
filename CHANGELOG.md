# Changelog

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
