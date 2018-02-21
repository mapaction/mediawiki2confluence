# mediawiki2confluence

[MediaWiki] migration scripts by [Aptivate] for MapAction.

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

> https://bobswift.atlassian.net/wiki/spaces/ACLI/pages/98009238/CLI+Client+Installation+and+Use

You can untar that file in the ignored `propietary` folder in this repository.

You can then do the following to get the `jira` executable on your `$PATH`:

```bash
$ cp propietary/atlassian-cli-<version>/jira.sh propietary/atlassian-cli-<version>/jira
$ source .env
```

Where the `.env` file contains definitions to extend your current `$PATH`.

Once installed, refer to the [action reference] for commands.

[action reference]: https://bobswift.atlassian.net/wiki/spaces/ACLI/pages/60194830/Action+Reference

# From Where To Where?

> https://mediawiki.mapaction.org

To:

> https://wiki-test.mapaction.org

# Planning

We're organising on this [Trello] board:

[Trello]: https://trello.com

> https://trello.com/b/KDErLd9q
