from itertools import chain
from os import environ
from pprint import pprint
from subprocess import check_output

import click


WIKI_URL = 'https://wiki-test.mapaction.org/'


# Please note, this was generated based on the comments in
# https://docs.google.com/spreadsheets/d/1MGapwHaEAdcvD98HzYw91Ze295xI7SQKE0NPmf_pE6g/edit?usp=sharing
# Updated format due to https://jira.atlassian.com/browse/CONFSERVER-7934
TOP_LEVEL_SPACES = [
    {'general-guidance': {'labels': []}},
    {'standard-procedures': {
        'labels': [
            'Current-SOPs-SAPs-and-Security-Manual',
            'Security-Manual',
            'Non-MapAction Security-Advice',
            'Standard-Administrative-Procedures',
            'SAP-01-General-Policies',
            'SAP-02-Human-Resources',
            'SAP-03-Risk-Management',
            'SAP-04-Financial-Management',
            'SAP-05-Fundraising-and-Marketing',
            'SAP-05-01-External-Communications',
            'SAP-06-Quality-Assurance',
            'SAP-07-Stakeholder-Communications',
            'SAP-08-Information-Technology',
            'SAP-09-Institutional-Partnerships',
            'SAP-09-01-ECHO',
            'SAP-09-02-USAID',
            'SAP-10-Equipment-Accounting-and-Management',
            'Standard-Operational-Procedures',
        ]
    }},
    {'internal-training': {
        'labels': [
            '2017-Team-Training',
            '2016-Team-Training',
            '2015-Team-Training',
            '2014-Team-Training',
            '2013-Team-Training',
            '2012-Team-Training',
            '2011-Team-Training',
            'Team-Training-Diary',
            'External-Training-Cost-Recoverable',
            'Partner-Training',
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
        '--server', WIKI_URL,
        '--user', credentials['username'],
        '--password', credentials['password']
    ]


def get_action_cmd(action, **arguments):
    """Assemble the action command."""
    command = [[
        '--action',
        '{}'.format(action)
    ]]
    for flag, value in arguments.items():
        command.append(['--{}'.format(flag)])
        command.append([value])
    return [part for part in chain(*command)]


def run_confluence_cmd(command, verbose=False):
    """Run a confluence CLI command. Accepts a list."""
    if verbose is True:
        click.echo('Executing the following command:')
        pprint(command)
    return check_output(command)


def format_space_key(label):
    """Get the space key in the right format."""
    return "".join(label.split('-'))


def format_space_name(label):
    """Get the space label in the right format."""
    return " ".join(map(str.capitalize, label.split('-')))


@click.group()
def main():
    """m2c: A bespoke MediaWiki to Confluence migration tool."""
    pass


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the spaces')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
def static_spaces(undo, verbose):
    """Create top level spaces"""
    space_keys = chain(*[k.keys() for k in TOP_LEVEL_SPACES])

    for space_key in space_keys:
        formatted_key = format_space_key(space_key)
        space_name = format_space_name(space_key)

        action, args = 'addSpace', dict(space=formatted_key, name=space_name)
        if undo:
            action, args = 'removeSpace', dict(space=formatted_key)

        space_cmd = get_action_cmd(action, **args)
        base = get_confluence_cmd()
        command = base + space_cmd

        output = run_confluence_cmd(command, verbose=verbose)
        click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the labels')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
def static_labels(undo, verbose):
    """Create labels on top level spaces"""
    space_keys = chain(*[k.keys() for k in TOP_LEVEL_SPACES])
    for key, space_dict in zip(space_keys, TOP_LEVEL_SPACES):
        labels = space_dict[key]['labels']

        if not labels:
            continue

        formatted_labels = ','.join(labels)
        formatted_key = format_space_key(key)

        action = 'removeLabels' if undo else 'addLabels'
        args = dict(space=formatted_key, labels=formatted_labels)

        label_cmd = get_action_cmd(action, **args)
        base = get_confluence_cmd()
        command = base + label_cmd

        output = run_confluence_cmd(command, verbose=verbose)
        click.echo(output)


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the labels')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
def pages(undo, verbose):
    """Migrates pages from MediaWiki."""
    pass
