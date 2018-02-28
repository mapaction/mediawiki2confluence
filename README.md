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

Once installed, refer to the [action reference] for commands.

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

# Run Things in Order

First of all, create a image downloads directory with:

```bash
$ mkdir -p images
```

Then, the migration, so far, is run in the following order:

```
$ m2c static_spaces
$ m2c static_labels
$ m2c migrate_categories
$ m2c migrate_pages --markdown
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

# The Algorithm

  - Create the top level spaces (from the Excel sheet categories)
  - Label those spaces accordingly (from the Excel sheet categories)
  - Migrate the rest of the categories into the general-guidance space
  - Start the page migration:
    - Convert the mediawiki page content to JSON
    - Rewrite internal links and drop categories from page ending
    - Convert from JSON to markdown and rewrite image links
    - Add mediawiki migration back-link to the page
    - Upload the page (auto-magic convert to confluence storage format from markdown)
  - Start the image migration
    - For each page, find all images
    - Upload the image attached to the page
