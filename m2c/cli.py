import io
import unicodedata
import os
from itertools import chain
from os import environ
from os.path import abspath, dirname
from pprint import pprint
from subprocess import STDOUT, CalledProcessError, check_output
from uuid import uuid4

import click
import requests
from bs4 import BeautifulSoup

import mwclient
import panflute
import pypandoc

FAILURE_LOG = 'm2c.log'


CONFLUENCE_URL = 'http://wiki.mapaction.org'
MEDIAWIKI_URL = 'mediawiki.mapaction.org'
IMAGES_DIR = '{}/../images'.format(dirname(abspath(__file__)))

CATEGORY_NAMESPACE = 14
MAIN_NAMESPACE = 0


class DuplicatePageException(Exception):
    """Duplicate page exception."""
    pass


def get_mw_client():
    """Build MediaWiki client connection."""
    try:
        username = environ['MEDIAWIKI_USERNAME']
        password = environ['MEDIAWIKI_PASSWORD']
    except KeyError as error:
        click.echo('Unable to retrieve {}'.format(str(error)))
        raise click.Abort()

    client = mwclient.Site(MEDIAWIKI_URL, path='/')
    client.login(username, password)

    return client


mwsite = get_mw_client()

main_pages = [p for p in mwsite.allpages(namespace=MAIN_NAMESPACE)]
cat_pages = [p for p in mwsite.allpages(namespace=CATEGORY_NAMESPACE)]
all_pages = main_pages + cat_pages


TOP_LEVEL_SPACES = [
    {'migration-general-guidance': {'labels': []}},
    {'migration-standard-procedures': {
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
    {'migration-internal-training': {
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
        username = environ['CONFLUENCE_USERNAME']
        password = environ['CONFLUENCE_PASSWORD']
    except KeyError as error:
        click.echo('Unable to retrieve {}'.format(str(error)))
        raise click.Abort()

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
        __import__('pdb').set_trace()

    try:
        return check_output(command, stderr=STDOUT)
    except (CalledProcessError, ValueError) as err:
        if 'already exists' in str(err.stdout):
            raise DuplicatePageException()

        click.echo('Failed to run command, saw: {}'.format(str(err)))
        with open(FAILURE_LOG, 'a') as handle:
            handle.write('Hard failure! Saw: {}\n'.format(str(err)))
        click.echo('Continuing ...\n')


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

    return 'migration-general-guidance'.replace('-', '')


def parse_title(page):
    """Parse the title of the page."""
    if 'Category:' in page.name:
        return page.name.replace('Category', '')
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
    DEFAULT_SPACE = 'migrationgeneralguidance'

    if ':Category:' in name:
        name = name.replace(':Category:', 'Category:')

    try:
        cleaned = name.split(ANCHOR_MARKER)[0].replace('_', ' ')

        if 'Category: ' in cleaned:
            cleaned = cleaned.replace('Category: ', 'Category:')

        page = [
            p for p in all_pages
            if cleaned.lower() in
            unicodedata.normalize("NFKD", p.name.lower())
        ][0]
        return parse_space(page)
    except IndexError:
        click.echo('Failed to determine space for {}'.format(name))
        with open(FAILURE_LOG, 'a') as handle:
            handle.write((
                'Failed to determine space for {}. '
                'Using default of {}.\n'.format(
                    name, DEFAULT_SPACE)
            ))
        click.echo('Continuing ...\n')

        return DEFAULT_SPACE


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
        click.echo('Continuing ...\n')

        return name


def rewrite_internal_links(elem, doc):
    if type(elem) == panflute.Link:
        if elem.title == 'wikilink':
            space = space_from_page_name(elem.url)

            page = elem.url.replace('_', '+')

            if 'Category:' in page:
                page = page.replace('Category:', '')

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
        'markdown_strict',
        format='json',
        extra_args=['--wrap=none']
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
        click.echo('Failed to parse content! Continuing ...\n')
        with open(FAILURE_LOG, 'a') as handle:
            handle.write((
                'Failed to parse content. Could not re-write links '
                'and drop categories for page {}\n'.format(name)
            ))

    return convert_image_format(content)


def build_migration_notice(page):
    """Build markup for migration notice."""
    link = '<a href="https://{base}/index.php/{link}">{name}</a>'.format(
        base=MEDIAWIKI_URL,
        link=page.name.replace(' ', '_'),
        name=page.name
    )

    return ((
        '<hr></hr> '
        '<p><ac:structured-macro ac:name="note" ac:schema-version="1" '
        'ac:macro-id="63359400-3dc8-43af-897b-d82aa4529401"> '
        '<ac:parameter ac:name="title">{title}</ac:parameter> '
        '<ac:rich-text-body><p>{notice}</p></ac:rich-text-body>'
        '</ac:structured-macro></p>'
    ).format(
        title='MediaWiki Migration Notice',
        notice=(
            'Please note, this page has been '
            'automatically migrated from the following '
            'MediaWiki page: {link}.'.format(link=link)
        )
    ))


def build_label_macro(label):
    """Build the label macro for category pages."""
    return (
        '<p><ac:structured-macro ac:name="contentbylabel" '
        'ac:schema-version="3" '
        'ac:macro-id="814171db-5a6b-47e9-a6f7-8361d070a401"> '
        '<ac:parameter ac:name="cql">'
        'label = "{}"</ac:parameter>'
        '</ac:structured-macro></p>'
    ).format(label)


def parse_content(page, space, category_page=False, title=None):
    """Retrieve the content of the page."""
    migration_notice = build_migration_notice(page)

    toc_markup = ((
        '<p><ac:structured-macro ac:name="toc" ac:schema-version="1" '
        'ac:macro-id="a4c703fc-b0db-4716-bc78-8682460e8220"/></p>'
        '\n'
    ))

    content = with_markdown(page.text(), space, page.name)

    if category_page and title is not None:
        label_macro = build_label_macro(category_cleaner(title))
        return toc_markup + content + label_macro + migration_notice

    return toc_markup + content + migration_notice


def parse_labels(page, extra_labels=[]):
    """Parse labels for the page."""
    parsed = clean_mw_categories([cat.name for cat in page.categories()])

    if extra_labels is not []:
        parsed += extra_labels

    if all(map(lambda x: isinstance(x, list), parsed)):
        return ','.join(chain(*parsed))

    return ','.join(parsed)


def download_image(image):
    """Download the image from MediaWiki."""
    url = image._info['imageinfo'][0]['url']
    response = requests.get(url, stream=True)
    location = '{}/{}'.format(IMAGES_DIR, parse_image_name(image))
    handle = open(location, 'wb')
    for chunk in response.iter_content(chunk_size=512):
        handle.write(chunk)
    return location


def handle_duplicate_page(args, kwargs, extra_labels, page,
                          title, action, base, verbose, debug):
    """Label and rename for duplicate pages as agreed."""
    extra_labels.append('fixme-duplicate-page-conflict')
    labels = parse_labels(page, extra_labels=extra_labels)
    kwargs['labels'] = labels

    unique_title = '{}-{}'.format(title, str(uuid4())[:8])
    kwargs['title'] = unique_title

    label_cmd = get_action_cmd(action, *args, **kwargs)
    command = base + label_cmd

    output = run_confluence_cmd(command, verbose=verbose, debug=debug)

    with open(FAILURE_LOG, 'a') as handle:
        handle.write('{} was a duplicate. Renamed to {}\n'.format(
            title, unique_title
        ))

    return output


@click.group()
def main():
    """m2c: A bespoke MediaWiki to Confluence migration tool."""
    pass


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the spaces')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--debug', is_flag=True, help='Drop into pdb for commands')
def spaces(undo, verbose, debug):
    """Create top level spaces and label them."""
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
@click.option('--debug', is_flag=True, help='Drop into pdb for commands')
def categories(undo, verbose, debug):
    """Migrate MediaWiki categories."""
    AGREED_SPACE = 'migration-general-guidance'

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
@click.option('--debug', is_flag=True, help='Drop into pdb for commands')
def pages(undo, verbose, limit, debug):
    """Migrates pages from MediaWiki."""
    if limit is not None:
        pages = main_pages[:int(limit)]
    else:
        pages = main_pages

    for page in pages:
        action, args, kwargs = 'addPage', [], {}

        space = parse_space(page)
        title = parse_title(page)
        content = parse_content(page, space=space)
        labels = parse_labels(page)

        if 'REDIRECT' in content:
            click.echo(('Dropping redirect page {}. '
                       'Continuing ...\n'.format(title)))
            with open(FAILURE_LOG, 'a') as handle:
                handle.write('Dropping redirect page {}\n'.format(title))
            continue

        extra_labels = []
        if "{{:" in content:
            extra_labels.append('fixme-transclusion-markup-unhandled')
        labels = parse_labels(page, extra_labels=extra_labels)

        kwargs = dict(
            space=space,
            title=title,
            content=content,
            labels=labels
        )

        args = ['markdown']

        if undo:
            action, kwargs = 'removePage', dict(space=space, title=title)

        label_cmd = get_action_cmd(action, *args, **kwargs)
        base = get_confluence_cmd()
        command = base + label_cmd

        try:
            output = run_confluence_cmd(command, verbose=verbose, debug=debug)
        except DuplicatePageException:
            click.echo('Found duplicate page. Handling accordingly ...')
            output = handle_duplicate_page(
                args, kwargs, extra_labels, page,
                title, action, base, verbose, debug
            )
        click.echo(output)


@main.command()
@click.argument('page-title')
@click.option('--undo', is_flag=True, help='Undo creation of the pages')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
@click.option('--debug', is_flag=True, help='Drop into pdb for commands')
def page(page_title, undo, verbose, debug):
    """Migrate a single from MediaWiki."""
    try:
        page = [p for p in all_pages if page_title in p.name][0]
    except IndexError:
        click.echo('Could not find that page. Sorry.')
        raise click.Abort()

    action, args, kwargs = 'addPage', [], {}

    space = parse_space(page)
    title = parse_title(page)
    content = parse_content(page, space=space)

    if 'REDIRECT' in content:
        click.echo('Dropping redirect page. Continuing ...\n')
        with open(FAILURE_LOG, 'a') as handle:
            handle.write('Dropping redirect page {}\n'.format(title))
        return

    extra_labels = []
    if '{{:' in content:
        extra_labels.append('fixme-transclusion-markup-unhandled')
    labels = parse_labels(page, extra_labels=extra_labels)

    kwargs = dict(
        space=space,
        title=title,
        content=content,
        labels=labels
    )

    args = ['markdown']

    if undo:
        action, kwargs = 'removePage', dict(space=space, title=title)

    label_cmd = get_action_cmd(action, *args, **kwargs)
    base = get_confluence_cmd()
    command = base + label_cmd

    try:
        output = run_confluence_cmd(command, verbose=verbose, debug=debug)
    except DuplicatePageException:
        click.echo('Found duplicate page. Handling accordingly ...')
        output = handle_duplicate_page(
            args, kwargs, extra_labels, page,
            title, action, base, verbose, debug
        )
    click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the images')
@click.option('--debug', is_flag=True, help='Drop into pdb for commands')
@click.option('--limit', default=None, help='Limit the number of images')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
def images(undo, debug, limit, verbose):
    """Migrates images from MediaWiki."""
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

    if limit is not None:
        pages = all_pages[:int(limit)]
    else:
        pages = all_pages

    for page in pages:
        images = [img for img in page.images()]
        for image in images:
            action, args, kwargs = 'addAttachment', [], {}

            space = parse_space(page)
            title = parse_title(page)
            name = parse_image_name(image)

            if 'Category:' in title:
                title = title.split('Category:')[-1]

            try:
                location = download_image(image)
            except Exception:
                click.echo('Failed to download image! Continuing ...\n')
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
@click.option('--debug', is_flag=True, help='Drop into pdb for commands')
def category_pages(undo, verbose, limit, debug):
    """Migrates category pages from MediaWiki."""
    if limit is not None:
        pages = cat_pages[:int(limit)]
    else:
        pages = cat_pages

    for page in pages:
        action, args, kwargs = 'addPage', [], {}

        space = parse_space(page)
        title = parse_category_page_title(page)
        content = parse_content(
            page,
            space=space,
            category_page=True,
            title=title,
        )

        extra_labels = ['fixme-was-a-category-page', category_cleaner(title)]
        if '{{:' in content:
            extra_labels.append('fixme-transclusion-markup-unhandled')

        if 'REDIRECT' in content:
            click.echo('Dropping redirect page. Continuing ...\n')
            with open(FAILURE_LOG, 'a') as handle:
                handle.write('Dropping redirect page {}\n'.format(title))
            continue

        labels = parse_labels(page, extra_labels=extra_labels)

        kwargs = dict(
            space=space,
            title=title,
            content=content,
            labels=labels
        )

        args = ['markdown']

        if undo:
            action, kwargs = 'removePage', dict(space=space, title=title)

        label_cmd = get_action_cmd(action, *args, **kwargs)
        base = get_confluence_cmd()
        command = base + label_cmd

        try:
            output = run_confluence_cmd(command, verbose=verbose, debug=debug)
        except DuplicatePageException:
            click.echo('Found duplicate page. Handling accordingly ...')
            output = handle_duplicate_page(
                args, kwargs, extra_labels, page,
                title, action, base, verbose, debug
            )

        click.echo(output)
