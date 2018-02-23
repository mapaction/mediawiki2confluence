from itertools import chain
from os import environ
from pprint import pprint
from subprocess import check_output

import click


WIKI_URL = 'https://wiki-test.mapaction.org/'


# Please note, this was generated based on the comments in
# https://docs.google.com/spreadsheets/d/1MGapwHaEAdcvD98HzYw91Ze295xI7SQKE0NPmf_pE6g/edit?usp=sharing
TOP_LEVEL_SPACES = [
    {'general-guidance': {'labels': []}},
    {'standard-procedures': {
        'labels': [
            'Current_SOPs,_SAPs_and_Security_Manual',
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
            '2017_Team_Training',
            '2016_Team_Training',
            '2015_Team_Training',
            '2014_Team_Training',
            '2013_Team_Training',
            '2012_Team_Training',
            '2011_Team_Training',
            'Team_Training_Diary',
            'External_Training_(Cost_Recoverable)',
            'Partner_Training',
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


@click.group()
def main():
    """m2c: A bespoke MediaWiki to Confluence migration tool."""
    pass


@main.command()
@click.option('--undo', is_flag=True, help='Undo creation of the spaces')
@click.option('--verbose', is_flag=True, help='The computer will speak to you')
def spaces(undo, verbose):
    """Create the agreed upon top level spaces"""
    base = get_confluence_cmd()

    space_cmd = get_action_cmd('addSpace', space='testspace', name='Test Space')
    if undo:
        space_cmd = get_action_cmd('removeSpace', space='testspace')

    command = base + space_cmd
    output = run_confluence_cmd(command, verbose=verbose)
    click.echo(output)

    # for each key in TOP_LEVEL_SPACES, create a space
    # for each label inside that key, label that space with them
    # If we pass --undo, delete everything
