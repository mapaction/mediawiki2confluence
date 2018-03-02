import io
from itertools import chain
from os import environ
from os.path import abspath, dirname
from pprint import pprint
from subprocess import CalledProcessError, check_output

from bs4 import BeautifulSoup

import click
import requests

import mwclient
import panflute
import pypandoc

FAILURE_LOG = 'failure.log'


CONFLUENCE_URL = 'https://wiki-test.mapaction.org'
MEDIAWIKI_URL = 'mediawiki.mapaction.org'
IMAGES_DIR = '{}/../images'.format(dirname(abspath(__file__)))

CATEGORY_NAMESPACE = 14


def get_mw_client():
    """Build MediaWiki client connection."""
    try:
        username = environ['MEDIAWIKI_USERNAME']
        password = environ['MEDIAWIKI_PASSWORD']
    except KeyError as error:
        click.fail('Unable to retrieve {}'.format(str(error)))

    client = mwclient.Site(MEDIAWIKI_URL, path='/')
    client.login(username, password)

    return client


mwsite = get_mw_client()

main_pages = [p for p in mwsite.allpages()]
cat_pages = [p for p in mwsite.allpages(namespace=CATEGORY_NAMESPACE)]
all_pages = main_pages + cat_pages


# Please note, this was generated based on the comments in
# https://docs.google.com/spreadsheets/d/1MGapwHaEAdcvD98HzYw91Ze295xI7SQKE0NPmf_pE6g/edit?usp=sharing
# Updated format due to https://jira.atlassian.com/browse/CONFSERVER-7934
TOP_LEVEL_SPACES = [
    {'general-guidance': {'labels': []}},
    {'standard-procedures': {
        'labels': [
            'Current SOPs, SAPs and Security Manual',
            'Security Manual',
            'Non-MapAction Security Advice',
            'Standard Administrative Procedures',
            'SAP 01: General Policies',
            'SAP 02: Human Resources',
            'SAP 03: Risk Management',
            'SAP 04: Financial Management',
            'SAP 05: Fundraising and Marketing',
            'SAP 05.01: External Communications',
            'SAP 06: Quality Assurance',
            'SAP 07: Stakeholder Communications',
            'SAP 08: Information Technology',
            'SAP 09: Institutional Partnerships',
            'SAP 09.01: ECHO',
            'SAP 09.02: USAID',
            'SAP 10: Equipment Accounting and Management',
            'Standard Operational Procedures',
        ]
    }},
    {'internal-training': {
        'labels': [
            '2017 Team Training',
            '2016 Team Training',
            '2015 Team Training',
            '2014 Team Training',
            '2013 Team Training',
            '2012 Team Training',
            '2011 Team Training',
            'Team Training Diary',
            'External Training (Cost Recoverable)',
            'Partner Training',
        ]
    }}
]


def get_credentials():
    """Assemble the HTTP Basic Auth credentials from the environment."""
    try:
        username = environ['HTTP_BASIC_AUTH_USERNAME']
        password = environ['HTTP_BASIC_AUTH_PASSWORD']
    except KeyError as error:
        click.fail('Unable to retrieve {}'.format(str(error)))
    return {'username': username, 'password': password}


def get_confluence_cmd():
    """Assemble mandatory parameters for the Confluence command."""
    try:
        command_path = environ['CONFLUENCE_COMMAND_PATH']
    except KeyError as error:
        click.fail('Unable to access {}'.format(str(error)))

    credentials = get_credentials()
    return [
        command_path,
        '--server', CONFLUENCE_URL,
        '--user', credentials['username'],
        '--password', credentials['password']
    ]


def get_action_cmd(action, *args, **kwargs):
    """Assemble the action command."""
    command = [[
        '--action',
        '{}'.format(action)
    ]]

    for argument in args:
        command.append(['--{}'.format(argument)])

    for flag, value in kwargs.items():
        command.append(['--{}'.format(flag)])
        command.append([value])

    return [part for part in chain(*command)]


def run_confluence_cmd(command, verbose=False, debug=False):
    """Run a confluence CLI command. Accepts a list."""
    if verbose is True:
        click.echo('Executing the following command:')
        pprint(command)

    if debug:
        __import__('ipdb').set_trace()

    try:
        return check_output(command)
    except (CalledProcessError, ValueError) as err:
        click.echo('Failed to run command, saw: {}'.format(str(err)))
        with open(FAILURE_LOG, 'a') as handle:
            handle.write('Hard failure! Saw: {}\n'.format(str(err)))
        click.echo('Continuing ...')


def format_space_key(label):
    """Get the space key in the right format."""
    return ''.join(label.split('-'))


def format_space_name(label):
    """Get the space label in the right format."""
    return ' '.join(map(str.capitalize, label.split('-')))


def category_cleaner(category):
    """Remove Confluence invalid characters from categories."""
    VALID = '-'

    invalid = [' ', ':', '(', ')', '_', ',', '.', '&']
    for character in category:
        if character in invalid:
            category = category.replace(character, VALID)

    return category


def parse_category_page_title(page):
    """Rip out category prefixes for category pages."""
    return page.name.replace('Category:', '')


def clean_mw_categories(categories):
    """Clean up parsed MediaWiki categories."""
    formatted = map(lambda cat: cat.replace('Category:', ''), categories)
    return list(map(category_cleaner, formatted))


def mwprefix(string):
    """Make sure to prefix things with 'mw-'."""
    return 'mw-' + string


def get_static_spaces():
    """Retrieve all space names from TOP_LEVEL_SPACES."""
    return chain(*[k.keys() for k in TOP_LEVEL_SPACES])


def get_static_labels():
    """Retrieve all labels from TOP_LEVEL_SPACES."""
    labels = []
    space_keys = get_static_spaces()
    for key, space_dict in zip(space_keys, TOP_LEVEL_SPACES):
        labels.append(space_dict[key]['labels'])
    return chain(*labels)


def parse_space(page):
    """Find which space the page lands in after migration."""
    mw_categories = clean_mw_categories([
        cat.name for cat in page.categories()
    ])

    space_keys = get_static_spaces()
    for key, space_dict in zip(space_keys, TOP_LEVEL_SPACES):
        labels = space_dict[key]['labels']
        cleaned = map(category_cleaner, labels)
        if set(mw_categories).intersection(cleaned):
            return key.replace('-', '')

    return 'general-guidance'.replace('-', '')


def parse_title(page):
    """Parse the title of the page."""
    return page.name


def parse_image_name(image):
    """Parse the name of the image."""
    return image.name.replace('File:', '')


def drop_loose_categories(elem, doc):
    """Drop all category links at the bottom of the page."""
    if type(elem) == panflute.Link:
        if elem.url.startswith('Category:'):
            return []


def space_from_page_name(name):
    """Determine space name from a page URL."""
    ANCHOR_MARKER = '#'

    try:
        cleaned = name.split(ANCHOR_MARKER)[0].replace('_', ' ')
        page = [p for p in all_pages if cleaned in p.name][0]
        return parse_space(page)
    except IndexError:
        click.echo('Failed to determine internal link for {}'.format(name))
        with open(FAILURE_LOG, 'a') as handle:
            handle.write('Failed to re-write internal link {}\n'.format(name))
        click.echo('Continuing ...')


def handle_anchor_link(name):
    """Will format internal anchor link if present."""
    if '#' not in name:
        return

    try:
        front, back = name.split('#')

        front_formatted = front.replace('_', '')
        back_formatted = back.replace('_', '')

        return '{}#{}-{}'.format(
            front.replace('_', '+'),
            front_formatted,
            back_formatted,
        )
    except Exception:
        click.echo('Failed to format anchor link for {}'.format(name))
        with open(FAILURE_LOG, 'a') as handle:
            handle.write('Failed to format anchor link {}\n'.format(name))
        click.echo('Continuing ...')


def rewrite_internal_links(elem, doc):
    if type(elem) == panflute.Link:
        if elem.title == 'wikilink':
            space = space_from_page_name(elem.url)

            page = elem.url.replace('_', '+')
            anchor = handle_anchor_link(elem.url)
            if anchor is not None:
                page = anchor

            elem.url = '{base}/display/{space}/{page}'.format(
                base=CONFLUENCE_URL,
                space=space,
                page=page
            )


def back_to_content(document):
    with io.StringIO() as f:
        panflute.dump(document, f)
        return f.getvalue()


def back_to_markdown(document):
    """Convert a Panflute JSON document back to markdown."""
    return pypandoc.convert_text(
        back_to_content(document),
        'markdown_mmd',
        format='json',
    )


def convert_image_format(markdown):
    """Make images appear in confluence format."""
    separated = markdown.split('\n')
    for index, line in enumerate(separated):
        if '<img' in line:
            soup = BeautifulSoup(line, 'html.parser')
            src = soup.select('img')[0]['src']

            dimensions = ""

            try:
                width = soup.select('img')[0]['width']
                dimensions += 'ac:width={}'.format(width)
            except KeyError:
                pass

            try:
                height = soup.select('img')[0]['height']
                dimensions += 'ac:height={}'.format(height)
            except KeyError:
                pass

            link_template = (
                '<p><ac:image ac:thumbnail="true" {dimensions}">'
                '<ri:attachment ri:filename="{filename}"/>'
                '</ac:image></p>'
            )
            separated[index] = link_template.format(
                filename=src, dimensions=dimensions
            )
    return '\n'.join(separated)


def with_markdown(content, space, name):
    """User pandoc to get markdown from MediaWiki format."""
    try:
        json_converted = pypandoc.convert_text(
            content,
            'json',
            format='mediawiki'
        )

        stream = io.StringIO(json_converted)
        traversable_doc = panflute.load(stream)

        panflute.run_filter(drop_loose_categories, doc=traversable_doc)

        panflute.run_filter(
            rewrite_internal_links,
            doc=traversable_doc
        )

        content = back_to_markdown(traversable_doc)
    except Exception:
        click.echo('Failed to parse into JSON! Continuing ...')
        with open(FAILURE_LOG, 'a') as handle:
            handle.write((
                'Failed to re-write links and '
                'drop categories for page {}\n'.format(name)
            ))

    return convert_image_format(content)


def parse_content(page, markdown, space):
    """Retrieve the content of the page."""
    link = '<a href="https://{base}/index.php/{link}">{name}</a>'.format(
        base=MEDIAWIKI_URL,
        link=page.name.replace(' ', '_'),
        name=page.name
    )

    migrated_notice = ((
        '<p><ac:structured-macro ac:name="note" ac:schema-version="1" '
        'ac:macro-id="63359400-3dc8-43af-897b-d82aa4529401"> '
        '<ac:parameter ac:name="title">{title}</ac:parameter> '
        '<ac:rich-text-body><p>{notice}</p></ac:rich-text-body>'
        '</ac:structured-macro></p>'
    ).format(
        title='MediaWiki Migration Notice',
        notice=(
            'Please note, this page has been '
            'automatically migrated from the '
            'MediaWiki page: {link}.'.format(link=link)
        )
    ))

    toc_markup = ((
        '<p><ac:structured-macro ac:name="toc" ac:schema-version="1" '
        'ac:macro-id="a4c703fc-b0db-4716-bc78-8682460e8220"/></p>'
        '\n'
    ))

    content = page.text()
    if markdown:
        content = with_markdown(page.text(), space, page.name)

    return toc_markup + content + migrated_notice


def parse_labels(page, extra_labels=[]):
    """Parse labels for the page."""
    parsed = clean_mw_categories([cat.name for cat in page.categories()])

    if extra_labels is not []:
        parsed += extra_labels

    return ",".join(chain(*parsed))


def download_image(image):
    """Download the image from MediaWiki."""
    url = image._info['imageinfo'][0]['url']
    response = requests.get(url, stream=True)
    location = '{}/{}'.format(IMAGES_DIR, parse_image_name(image))
    handle = open(location, 'wb')
    for chunk in response.iter_content(chunk_size=512):
        handle.write(chunk)
    return location


@click.group()
def main():
    """m2c: A bespoke MediaWiki to Confluence migration tool."""
    pass


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the spaces')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
def static_spaces(undo, verbose, debug):
    """Create top level spaces"""
    space_keys = get_static_spaces()

    for space_key in space_keys:
        formatted_key = format_space_key(space_key)
        space_name = format_space_name(space_key)

        action, kwargs = 'addSpace', dict(space=formatted_key, name=space_name)
        if undo:
            action, kwargs = 'removeSpace', dict(space=formatted_key)

        space_cmd = get_action_cmd(action, **kwargs)
        base = get_confluence_cmd()
        command = base + space_cmd

        output = run_confluence_cmd(
            command,
            verbose=verbose,
            debug=debug,
        )
        click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the labels')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
def static_labels(undo, verbose, debug):
    """Create labels on top level spaces"""
    space_keys = get_static_spaces()

    for key, space_dict in zip(space_keys, TOP_LEVEL_SPACES):
        labels = space_dict[key]['labels']

        if not labels:
            continue

        cleaned = map(category_cleaner, labels)
        prefixed = map(mwprefix, cleaned)
        formatted_labels = ','.join(prefixed)
        formatted_key = format_space_key(key)

        action = 'removeLabels' if undo else 'addLabels'
        kwargs = dict(space=formatted_key, labels=formatted_labels)

        label_cmd = get_action_cmd(action, **kwargs)
        base = get_confluence_cmd()
        command = base + label_cmd

        output = run_confluence_cmd(command, verbose=verbose, debug=debug)
        click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the categories')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
def migrate_categories(undo, verbose, debug):
    """Migrate MediaWiki categories."""
    AGREED_SPACE = 'general-guidance'

    labels = [label for label in get_static_labels()]
    cleaned_labels = list(map(category_cleaner, labels))
    categories = clean_mw_categories([
        cat.name for cat in mwsite.allcategories()
    ])
    remaining = set(categories).difference(set(cleaned_labels))
    formatted_remaining = ",".join(map(mwprefix, remaining))

    action = 'removeLabels' if undo else 'addLabels'
    kwargs = dict(
        space=AGREED_SPACE.replace('-', ''),
        labels=formatted_remaining
    )

    label_cmd = get_action_cmd(action, **kwargs)
    base = get_confluence_cmd()
    command = base + label_cmd

    output = run_confluence_cmd(command, verbose=verbose, debug=debug)
    click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the pages')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--limit', default=None, help='Limit the number of pages')
@click.option('--markdown', is_flag=True, help='Migrate with markdown')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
def migrate_pages(undo, verbose, limit, markdown, debug):
    """Migrates pages from MediaWiki."""
    if limit is not None:
        pages = [p for p in main_pages][:int(limit)]
    else:
        pages = [p for p in main_pages]

    for page in pages:
        action, args, kwargs = 'addPage', [], {}

        space = parse_space(page)
        title = parse_title(page)
        content = parse_content(page, markdown=markdown, space=space)
        labels = parse_labels(page)

        extra_labels = []
        if "{{:" in content:
            extra_labels.append(['FIXME-transclusion-markup-unhandled'])
        if 'REDIRECT' in content:
            extra_labels.append(['FIXME-redirect-page'])
        labels = parse_labels(page, extra_labels=extra_labels)

        kwargs = dict(
            space=space,
            title=title,
            content=content,
            labels=labels
        )

        if markdown:
            args = ['markdown']

        if undo:
            action, kwargs = 'removePage', dict(space=space, title=title)

        label_cmd = get_action_cmd(action, *args, **kwargs)
        base = get_confluence_cmd()
        command = base + label_cmd

        output = run_confluence_cmd(
            command,
            verbose=verbose,
            debug=debug,
        )
        click.echo(output)


@main.command()
@click.argument('page-title')
@click.option('--undo', is_flag=True, help='Undo creation of the pages')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--markdown', is_flag=True, help='Migrate with markdown')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
def migrate_page(page_title, undo, verbose, markdown, debug):
    """Migrate a single from MediaWiki."""
    try:
        page = [p for p in all_pages if page_title in p.name][0]
    except IndexError:
        click.echo('Could not find that page. Sorry.')
        raise click.Abort()

    action, args, kwargs = 'addPage', [], {}

    space = parse_space(page)
    title = parse_title(page)
    content = parse_content(page, markdown=markdown, space=space)

    extra_labels = []
    if '{{:' in content:
        extra_labels.append(['FIXME-transclusion-markup-unhandled'])
    if 'REDIRECT' in content:
        extra_labels.append(['FIXME-redirect-page'])
    labels = parse_labels(page, extra_labels=extra_labels)

    kwargs = dict(
        space=space,
        title=title,
        content=content,
        labels=labels
    )

    if markdown:
        args = ['markdown']

    if undo:
        action, kwargs = 'removePage', dict(space=space, title=title)

    label_cmd = get_action_cmd(action, *args, **kwargs)
    base = get_confluence_cmd()
    command = base + label_cmd

    output = run_confluence_cmd(
        command,
        verbose=verbose,
        debug=debug,
    )
    click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the images')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
@click.option('--limit', default=None, help='Limit the number of images')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
def migrate_images(undo, debug, limit, verbose):
    """Migrates images from MediaWiki."""
    # FIXME: Should we also do this with category pages!?
    if limit is not None:
        pages = [p for p in main_pages][:int(limit)]
    else:
        pages = [p for p in main_pages]

    for page in pages:
        images = [img for img in page.images()]
        for image in images:
            action, args, kwargs = 'addAttachment', [], {}

            space = parse_space(page)
            title = parse_title(page)
            name = parse_image_name(image)

            try:
                location = download_image(image)
            except Exception:
                click.echo('Failed to download image! Continuing ...')
                with open(FAILURE_LOG, 'a') as handle:
                    msg = 'Failed to download image: {} for page {}\n'
                    handle.write(msg.format(name, page.name))
                continue

            kwargs = dict(
                space=space,
                title=title,
                name=name,
                file=location,
            )

            if undo:
                action, kwargs = (
                    'removeAttachment',
                    dict(space=space, name=name, title=title)
                )

            label_cmd = get_action_cmd(action, *args, **kwargs)
            base = get_confluence_cmd()
            command = base + label_cmd

            output = run_confluence_cmd(
                command,
                verbose=verbose,
                debug=debug,
            )
            click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the pages')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--limit', default=None, help='Limit the number of pages')
@click.option('--markdown', is_flag=True, help='Migrate with markdown')
@click.option('--debug', is_flag=True, help='Drop into ipdb for commands')
def migrate_category_pages(undo, verbose, limit, markdown, debug):
    """Migrates category pages from MediaWiki."""
    if limit is not None:
        pages = [p for p in cat_pages][:int(limit)]
    else:
        pages = [p for p in cat_pages]

    for page in pages:
        action, args, kwargs = 'addPage', [], {}

        space = parse_space(page)
        title = parse_category_page_title(page)
        content = parse_content(page, markdown=markdown, space=space)

        extra_labels = ['FIXME-was-a-category-page']
        if '{{:' in content:
            extra_labels.append(['FIXME-transclusion-markup-unhandled'])
        if 'REDIRECT' in content:
            extra_labels.append(['FIXME-redirect-page'])
        labels = parse_labels(page, extra_labels=extra_labels)

        kwargs = dict(
            space=space,
            title=title,
            content=content,
            labels=labels
        )

        if markdown:
            args = ['markdown']

        if undo:
            action, kwargs = 'removePage', dict(space=space, title=title)

        label_cmd = get_action_cmd(action, *args, **kwargs)
        base = get_confluence_cmd()
        command = base + label_cmd

        output = run_confluence_cmd(
            command,
            verbose=verbose,
            debug=debug,
        )
        click.echo(output)
