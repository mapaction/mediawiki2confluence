# m2c

[MediaWiki] migration scripts by [Aptivate] for [MapAction].

[MediaWiki]: https://www.mediawiki.org/wiki/MediaWiki
[Aptivate]: http://www.aptivate.org
[MapAction]: https://mapaction.org

# Getting Started

## Install m2c

With [pip] that is as easy as:

[pip]: https://pip.pypa.io/en/stable/installing/

```
$ pip install m2c
```

## Install Confluence CLI

You'll need the Confluence CLI tool. Follow the instructions at:

> https://wiki-test.mapaction.org/admin/plugins/org.swift.confluence.cli/getstarted.action

## Configure Environment

The `m2c` tool expects a number of values exposed in your environment.

Here's an example of what that might look like:

```
CONFLUENCE_COMMAND_PATH="${PWD}/propietary/atlassian-cli-7.6.0/confluence" # for example
HTTP_BASIC_AUTH_USERNAME="stallman"
HTTP_BASIC_AUTH_PASSWORD="freesoftwarefreesociety"
MEDIAWIKI_USERNAME='stallman'
MEDIAWIKI_PASSWORD='ilikeparrots'
```

## Running The Migration

The migration is run in a number of steps:

```
$ m2c spaces
$ m2c categories
$ m2c pages
$ m2c category_pages
$ m2c images
```

You can review the logs in `m2c.log` in your current working directory.

## Dealing with Individual Pages

You can run the following:

```
$ m2c page "Windows 7 manual install"
```

This will migrate a single page. Use `--undo` to remove the page.

# Development

See `CONTRIBUTING.md`.
