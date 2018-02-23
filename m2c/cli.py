from os import environ
from subprocess import check_output

import click


WIKI_URL = 'wiki-test.mapaction.org'


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


def get_jira_cmd():
    """Assemble mandatory parameters for the jira command."""
    try:
        command_path = environ['JIRA_COMMAND_PATH']
    except KeyError as error:
        click.fail('Unable to access {}'.format(str(error)))

    base_cmd = '{cmd} --server "{srv}" --user "{user}" --password "{pword}"'
    credentials = get_credentials()
    return base_cmd.format(
        cmd=command_path,
        srv=WIKI_URL,
        user=credentials['username'],
        pword=credentials['password']
    )


@click.group()
def main():
    """m2c: A bespoke MediaWiki to Confluence migration tool."""
    pass


@main.command()
@click.option('--undo', help='Undo creation of the spaces')
def spaces(undo):
    """Create the agreed upon top level spaces"""
    jira_base = get_jira_cmd()
    __import__('ipdb').set_trace()
    # for each key in TOP_LEVEL_SPACES, create a space
    # for each label inside that key, label that space with them
    # If we pass --undo, delete everything
    pass
