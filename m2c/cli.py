from os import environ

import click


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


def build_auth():
    """Assemble the HTTP Basic Auth credentials from the environment."""
    try:
        username = environ['HTTP_BASIC_AUTH_USERNAME']
        password = environ['HTTP_BASIC_AUTH_PASSWORD']
    except KeyError:
        click.echo('Failed to retrieve Basic Auth credentials!')
    return (username, password)


@click.command()
@click.option('--undo', help='Undo creation of the spaces')
def spaces(undo):
    """Create the agreed upon top level spaces"""
    # for each key in TOP_LEVEL_SPACES, create a space
    # for each label inside that key, label that space with them
    # If we pass --undo, delete everything
    pass
