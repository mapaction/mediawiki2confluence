# mediawiki2confluence

[MediaWiki] migration scripts by [Aptivate] for [MapAction].

[MediaWiki]: https://www.mediawiki.org/wiki/MediaWiki
[Aptivate]: http://www.aptivate.org
[MapAction]: https://mapaction.org

# Install The Free Software

Get a local copy of [pipenv] and then run:

[pipenv]: https://docs.pipenv.org

```bash
$ pipenv install --dev
```

# Install the Non-Free Software

You'll need a CLI tool from the Confluence. Follow the instructions at:

> https://bobswift.atlassian.net/wiki/spaces/CSOAP/pages/10584068/Reference

Untar that file in the ignored `propietary` folder in this repository.

For usage, refer to the [action reference] for commands.

[action reference]: https://bobswift.atlassian.net/wiki/spaces/CSOAP/overview

# Configure the Environment

The program expects a number of environment variables to work properly. Please export:

```bash
CONFLUENCE_COMMAND_PATH="${PWD}/propietary/atlassian-cli-7.6.0/confluence" # for example
HTTP_BASIC_AUTH_USERNAME="stallman"
HTTP_BASIC_AUTH_PASSWORD="freesoftwarefreesociety"
MEDIAWIKI_USERNAME='stallman'
MEDIAWIKI_PASSWORD='ilikeparrots'
```

# Use the CLI Tool

Once you've ran the `pipenv` incantation, you can access the tool with:

```
$ pipenv run m2c --help
```

Or drop into a pipenv managed shell and run commands with:

```
$ pipenv shell
$ m2c --help
```

# Run Things in Order

First of all, create a image downloads directory with:

```bash
$ mkdir -p images
```

The migration is run manually in steps, so far:

```
$ m2c static_spaces
$ m2c static_labels
$ m2c migrate_categories
$ m2c migrate_pages --markdown
$ m2c migrate_category_pages --markdown
$ m2c migrate_images
```

# From Where To Where?

> https://mediawiki.mapaction.org

To:

> https://wiki-test.mapaction.org

# Planning

We're organising on this [Trello] board:

[Trello]: https://trello.com

> https://trello.com/b/KDErLd9q
